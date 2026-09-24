#!/usr/bin/env python3
"""Mechanical fixture checker for PR Pattern Detective.

Scores a *completed* fixture repo against its fixture.json `expected` block,
using only checks that code can verify deterministically. It does not run
any agent and does not simulate a user — it inspects the repo as it sits on
disk right now.

Usage:
    python3 prpd/tools/run_fixture.py <fixture-dir>   # score one fixture
    python3 prpd/tools/run_fixture.py --all           # score every fixture under prpd/fixtures/

Exit code is non-zero if any fixture fails a check.
"""

import json
import subprocess
import sys
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = TOOLS_DIR.parent / "fixtures"
PRPD_PY = TOOLS_DIR / "prpd.py"


class Result:
    def __init__(self, name, passed, detail="", skipped=False):
        self.name = name
        self.passed = passed
        self.detail = detail
        self.skipped = skipped


def run_prpd(repo_dir: Path, *args) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(PRPD_PY), *args, "--repo-dir", str(repo_dir)],
        capture_output=True,
        text=True,
    )


def load_json(path: Path):
    return json.loads(path.read_text())


def check_baseline_validate(repo_dir: Path) -> Result:
    proc = run_prpd(repo_dir, "baseline", "validate")
    return Result("baseline validate", proc.returncode == 0, proc.stderr.strip() or proc.stdout.strip())


def check_files(repo_dir: Path) -> Result:
    proc = run_prpd(repo_dir, "check-files")
    return Result("check-files", proc.returncode == 0, proc.stderr.strip() or proc.stdout.strip())


def check_dimensions(baseline: dict, expected: dict) -> Result:
    actual = baseline.get("dimensions", {})
    exp = expected.get("dimensions", {})
    ok = actual == exp
    return Result(
        "dimensions match expected",
        ok,
        "" if ok else f"expected {exp}, got {actual}",
    )


def check_outcome(baseline: dict, expected: dict) -> Result:
    actual = baseline.get("outcome")
    allowed = expected.get("outcome", [])
    ok = actual in allowed
    return Result(
        "outcome in expected set",
        ok,
        "" if ok else f"expected one of {allowed}, got {actual!r}",
    )


def check_library_page(repo_dir: Path, baseline: dict) -> Result:
    lib = baseline.get("library_page")
    if not lib:
        return Result("library_page recorded and exists", False, "library_page is empty in baseline.json")
    exists = (repo_dir / lib).is_file()
    return Result(
        "library_page recorded and exists",
        exists,
        "" if exists else f"{lib} does not exist under {repo_dir}",
    )


def check_approved_paths(repo_dir: Path, baseline: dict) -> Result:
    missing = []
    for comp in baseline.get("components", []):
        if comp.get("status") == "approved":
            path = comp.get("path")
            if not path or not (repo_dir / path).exists():
                missing.append(f"component {comp.get('name')}: {path}")
    ok = not missing
    return Result(
        "approved component paths exist",
        ok,
        "" if ok else "; ".join(missing),
    )


def check_build(repo_dir: Path) -> Result:
    if not (repo_dir / "node_modules").is_dir():
        return Result("npm run build succeeds", True, "skipped: node_modules not installed", skipped=True)
    proc = subprocess.run(
        ["npm", "run", "build"],
        cwd=repo_dir,
        capture_output=True,
        text=True,
    )
    ok = proc.returncode == 0
    return Result("npm run build succeeds", ok, "" if ok else proc.stdout[-2000:] + proc.stderr[-2000:])


def check_ticket_validate(repo_dir: Path) -> Result:
    proc = run_prpd(repo_dir, "ticket", "validate")
    return Result("ticket validate", proc.returncode == 0, proc.stderr.strip() or proc.stdout.strip())


def check_ticket_recorded(repo_dir: Path, ticket_id: str) -> Result:
    tickets_path = repo_dir / ".prpd" / "tickets.json"
    if not tickets_path.is_file():
        return Result(f"ticket {ticket_id} recorded in tickets.json", False, f"{tickets_path} does not exist")
    tickets = load_json(tickets_path)
    record = tickets.get(ticket_id)
    ok_ = record is not None and record.get("findings") and record.get("approved_decisions")
    return Result(
        f"ticket {ticket_id} recorded in tickets.json",
        bool(ok_),
        "" if ok_ else f"no findings/decisions recorded for {ticket_id}",
    )


def check_extension_in_baseline(repo_dir: Path, component_name: str) -> Result:
    baseline_path = repo_dir / ".prpd" / "baseline.json"
    baseline = load_json(baseline_path)
    comp = next((c for c in baseline.get("components", []) if c.get("name") == component_name), None)
    ok_ = comp is not None and comp.get("status") == "approved" and (repo_dir / comp.get("path", "")).exists()
    return Result(
        f"extension '{component_name}' approved and present in baseline",
        bool(ok_),
        "" if ok_ else f"{component_name} not found as an approved component with an existing path",
    )


def check_audit_log(repo_dir: Path, required_steps) -> Result:
    audit_path = repo_dir / ".prpd" / "audit.jsonl"
    if not audit_path.is_file():
        return Result("audit.jsonl well-formed with required steps", False, f"{audit_path} does not exist")

    steps_seen = set()
    for i, line in enumerate(audit_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
        except json.JSONDecodeError as e:
            return Result(
                "audit.jsonl well-formed with required steps",
                False,
                f"line {i} is not valid JSON: {e}",
            )
        if "ts" not in entry or "kind" not in entry:
            return Result(
                "audit.jsonl well-formed with required steps",
                False,
                f"line {i} is missing required 'ts'/'kind' fields",
            )
        if entry.get("step"):
            steps_seen.add(entry["step"])

    missing = [s for s in required_steps if s not in steps_seen]
    ok = not missing
    return Result(
        "audit.jsonl well-formed with required steps",
        ok,
        "" if ok else f"missing step tags: {missing}",
    )


def score_init_fixture(fixture_dir: Path, fixture: dict):
    repo_dir = fixture_dir / "repo"
    expected = fixture.get("expected", {})
    baseline_path = repo_dir / ".prpd" / "baseline.json"

    results = [check_baseline_validate(repo_dir), check_files(repo_dir)]

    if not baseline_path.is_file():
        results.append(Result("baseline.json readable", False, f"{baseline_path} does not exist"))
        return results

    baseline = load_json(baseline_path)
    results.append(check_dimensions(baseline, expected))
    results.append(check_outcome(baseline, expected))
    results.append(check_library_page(repo_dir, baseline))
    results.append(check_approved_paths(repo_dir, baseline))
    results.append(check_build(repo_dir))
    results.append(check_audit_log(repo_dir, ["init.classify", "init.verify"]))
    return results


# Behaviors are described as free-text process claims in fixture.json, but a
# few happen to describe an end-state that one of the checks above already
# verifies. Listing them as "unverified" would understate real coverage.
COVERED_BEHAVIORS = {
    "generates a design-system library page": "library_page recorded and exists",
    "writes baseline via prpd.py (schema-valid)": "baseline validate",
    "check-files passes at end of run": "check-files",
    "adds the extension to baseline.json components with source referencing the ticket": "extension approved and present in baseline",
    "persists findings and decisions via ticket upsert (schema-valid)": "ticket recorded in tickets.json",
    "ticket validate passes at end of run": "ticket validate",
    "verdict is fail while any blocker is open, pass once every blocker is fixed or overridden": "verdict matches expected (final)",
}


def score_ticket_fixture(fixture_dir: Path, fixture: dict):
    target = fixture.get("target_repo")
    if not target:
        return [Result("target_repo resolves", False, "fixture.json has no target_repo")]
    repo_dir = (fixture_dir / target).resolve()
    if not repo_dir.is_dir():
        return [Result("target_repo resolves", False, f"{repo_dir} does not exist")]

    ticket_id = fixture.get("ticket", {}).get("id")
    expected = fixture.get("expected", {})
    results = [check_ticket_validate(repo_dir), check_baseline_validate(repo_dir), check_files(repo_dir)]
    results.append(check_ticket_recorded(repo_dir, ticket_id))
    extension = expected.get("extension_approved")
    if extension:
        results.append(check_extension_in_baseline(repo_dir, extension))
    return results


def check_pr_verdict(repo_dir: Path, ticket_id: str, expected_verdict: str) -> Result:
    tickets_path = repo_dir / ".prpd" / "tickets.json"
    if not tickets_path.is_file():
        return Result("verdict matches expected (final)", False, f"{tickets_path} does not exist")
    tickets = load_json(tickets_path)
    record = tickets.get(ticket_id)
    if record is None:
        return Result("verdict matches expected (final)", False, f"no context recorded for {ticket_id}")
    open_blockers = [
        f for f in record.get("findings", [])
        if isinstance(f, dict) and f.get("severity") == "blocker" and f.get("status", "open") == "open"
    ]
    verdict = "fail" if open_blockers else "pass"
    ok_ = verdict == expected_verdict
    detail = "" if ok_ else f"expected {expected_verdict}, computed {verdict} ({len(open_blockers)} open blocker(s): {[f.get('id') for f in open_blockers]})"
    return Result("verdict matches expected (final)", ok_, detail)


def score_pr_fixture(fixture_dir: Path, fixture: dict):
    target = fixture.get("target_repo")
    if not target:
        return [Result("target_repo resolves", False, "fixture.json has no target_repo")]
    repo_dir = (fixture_dir / target).resolve()
    if not repo_dir.is_dir():
        return [Result("target_repo resolves", False, f"{repo_dir} does not exist")]

    ticket_id = fixture.get("ticket_id")
    expected = fixture.get("expected", {})
    results = [check_ticket_validate(repo_dir), check_baseline_validate(repo_dir), check_files(repo_dir)]
    results.append(check_pr_verdict(repo_dir, ticket_id, expected.get("final_verdict", "pass")))
    return results


def score_fixture(fixture_dir: Path):
    fixture_path = fixture_dir / "fixture.json"
    fixture = load_json(fixture_path)
    stage = fixture.get("stage")

    if stage == "init":
        results = score_init_fixture(fixture_dir, fixture)
    elif stage == "ticket":
        results = score_ticket_fixture(fixture_dir, fixture)
    elif stage == "pr":
        results = score_pr_fixture(fixture_dir, fixture)
    else:
        results = [Result(f"stage '{stage}' scoring", False, "no mechanical checks implemented for this stage yet")]

    all_behaviors = fixture.get("expected", {}).get("behaviors", [])
    unverified_behaviors = [b for b in all_behaviors if b not in COVERED_BEHAVIORS]
    return fixture.get("id", fixture_dir.name), results, unverified_behaviors


def print_report(fixture_id, results, unverified_behaviors):
    print(f"\n== {fixture_id} ==")
    all_ok = True
    for r in results:
        if r.skipped:
            status = "SKIP"
        elif r.passed:
            status = "PASS"
        else:
            status = "FAIL"
            all_ok = False
        print(f"  [{status}] {r.name}")
        if r.detail and (status == "FAIL" or (status == "SKIP" and r.detail)):
            print(f"         {r.detail}")

    if unverified_behaviors:
        print("  Not mechanically checked (process claims, not end-state artifacts):")
        for b in unverified_behaviors:
            print(f"    - {b}")

    return all_ok


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    arg = sys.argv[1]
    if arg == "--all":
        fixture_dirs = sorted(
            p.parent for p in FIXTURES_DIR.glob("*/fixture.json")
        )
    else:
        fixture_dirs = [Path(arg).resolve()]

    if not fixture_dirs:
        print(f"no fixtures found under {FIXTURES_DIR}", file=sys.stderr)
        sys.exit(2)

    all_passed = True
    passed_count = 0
    for fixture_dir in fixture_dirs:
        fixture_id, results, unverified_behaviors = score_fixture(fixture_dir)
        ok = print_report(fixture_id, results, unverified_behaviors)
        all_passed = all_passed and ok
        passed_count += 1 if ok else 0

    print(f"\n{passed_count}/{len(fixture_dirs)} fixture(s) fully passed mechanical checks")
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
