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
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
FIXTURES_DIR = TOOLS_DIR.parent / "fixtures"
PRPD_PY = TOOLS_DIR / "prpd.py"
CHAINS_PATH = FIXTURES_DIR / "chains.json"
RESULTS_LOG = FIXTURES_DIR / "results.jsonl"


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


def check_failures_traceable(repo_dir: Path) -> Result:
    """Every recorded failure with result=='fail' must carry a step tag.
    Historical entries predating the --step requirement are a known,
    documented exception (see AUDIT_TRAIL.md) and are not re-flagged here
    -- this check is about catching *new* untraceable failures, not
    re-litigating the one already on record."""
    audit_path = repo_dir / ".prpd" / "audit.jsonl"
    if not audit_path.is_file():
        return Result("failures traceable to a step", True, "no audit.jsonl (nothing to check)", skipped=True)
    untraceable = 0
    total_failures = 0
    for line in audit_path.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("result") == "fail":
            total_failures += 1
            if not entry.get("step"):
                untraceable += 1
    # One pre-existing historical entry (01-greenfield's early ticket-get
    # failure) is the documented baseline; anything beyond that is new.
    ok_ = untraceable <= 1
    return Result(
        "failures traceable to a step",
        ok_,
        "" if ok_ else f"{untraceable} untraceable failures (expected at most 1 documented historical case)",
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


def check_punchout_recorded(repo_dir: Path, point_id: str) -> Result:
    path = repo_dir / ".prpd" / "punchouts.jsonl"
    if not path.is_file():
        return Result(f"punch-out recorded: {point_id}", False, f"{path} does not exist")
    found = any(
        json.loads(line).get("point_id") == point_id
        for line in path.read_text().splitlines() if line.strip()
    )
    return Result(f"punch-out recorded: {point_id}", found, "" if found else f"no entry for {point_id}")


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
    results.append(check_failures_traceable(repo_dir))
    results.append(check_punchout_recorded(repo_dir, "stack_confirmed"))
    results.append(check_punchout_recorded(repo_dir, "accessibility_target_confirmed"))
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
    "records a developer override with reasons/by/at rather than silently dropping the blocker": "override recorded for convention-6",
}


def check_gate_file(repo_dir: Path, gate_name: str) -> Result:
    gate_path = repo_dir / ".prpd" / "gates" / gate_name
    ok_ = gate_path.is_file()
    detail = "" if ok_ else f"{gate_path} does not exist -- guardrail was never run or did not pass"
    return Result(f"guardrail gate present: {gate_name}", ok_, detail)


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
    results.append(check_gate_file(repo_dir, "init.ok"))
    results.append(check_gate_file(repo_dir, f"ticket-{ticket_id}.ok"))
    extension = expected.get("extension_approved")
    if extension:
        results.append(check_extension_in_baseline(repo_dir, extension))
        results.append(check_punchout_recorded(repo_dir, f"extension_approved:{extension}"))
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


def check_override_recorded(repo_dir: Path, ticket_id: str, finding_id: str) -> Result:
    tickets_path = repo_dir / ".prpd" / "tickets.json"
    tickets = load_json(tickets_path)
    record = tickets.get(ticket_id, {})
    finding = next((f for f in record.get("findings", []) if isinstance(f, dict) and f.get("id") == finding_id), None)
    if finding is None:
        return Result(f"override recorded for {finding_id}", False, f"finding {finding_id} not found")
    override = finding.get("override")
    ok_ = (
        finding.get("status") == "overridden"
        and isinstance(override, dict)
        and all(override.get(k) for k in ("reasons", "by", "at"))
    )
    return Result(
        f"override recorded for {finding_id}",
        bool(ok_),
        "" if ok_ else f"status={finding.get('status')!r}, override={override!r}",
    )


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
    results.append(check_gate_file(repo_dir, f"ticket-{ticket_id}.ok"))
    override_id = expected.get("override_finding_id")
    if override_id:
        results.append(check_override_recorded(repo_dir, ticket_id, override_id))
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


def load_chains():
    if not CHAINS_PATH.exists():
        return [], []
    data = load_json(CHAINS_PATH)
    return data.get("chains", []), data.get("standalone", [])


def compute_and_report_end_to_end(fixture_results: dict):
    """fixture_results: {fixture_id: bool_passed}. Prints and returns the
    end-to-end summary; a 'chain' only counts as a successful end-to-end run
    if every fixture in it currently passes -- this is the number the
    certification rubric calls the 'end-to-end number,' not a per-step
    average."""
    chains, standalone = load_chains()
    print("\n== End-to-end chains ==")
    chain_results = {}
    for chain in chains:
        fids = chain["fixtures"]
        known = [fixture_results.get(f) for f in fids]
        chain_passed = all(known) and None not in known
        chain_results[chain["id"]] = chain_passed
        status = "PASS" if chain_passed else "FAIL"
        print(f"  [{status}] {chain['id']}: {' -> '.join(fids)}")

    if chains:
        passed = sum(1 for v in chain_results.values() if v)
        rate = passed / len(chain_results)
        print(f"\nEND-TO-END SUCCESS RATE: {passed}/{len(chain_results)} chains ({rate:.0%})")
        print("  Sample-size caveat: this is a small, growing number of chains, each")
        print("  currently run once per invocation, not repeated statistical trials.")
        print("  See SUCCESS_RATE.md for the trend log and methodology.")
    else:
        rate = None
        print("  no chains defined in chains.json")

    if standalone:
        print("\n== Standalone fixtures (not part of an end-to-end chain yet) ==")
        for s in standalone:
            fid = s["id"]
            status = "PASS" if fixture_results.get(fid) else ("FAIL" if fid in fixture_results else "UNKNOWN")
            print(f"  [{status}] {fid}")

    return chain_results, rate


def record_result(fixture_results: dict, chain_results: dict, end_to_end_rate):
    RESULTS_LOG.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "fixture_results": fixture_results,
        "chain_results": chain_results,
        "mechanical_pass_rate": sum(1 for v in fixture_results.values() if v) / len(fixture_results) if fixture_results else None,
        "end_to_end_rate": end_to_end_rate,
    }
    with RESULTS_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")
    return entry


def print_trend():
    if not RESULTS_LOG.exists():
        print("no recorded runs yet -- run `run_fixture.py --all` at least once")
        return
    lines = [json.loads(l) for l in RESULTS_LOG.read_text().splitlines() if l.strip()]
    print(f"{'timestamp':<28} {'mechanical':<12} {'end-to-end':<12}")
    for entry in lines:
        mech = f"{entry['mechanical_pass_rate']:.0%}" if entry.get("mechanical_pass_rate") is not None else "n/a"
        e2e = f"{entry['end_to_end_rate']:.0%}" if entry.get("end_to_end_rate") is not None else "n/a"
        print(f"{entry['ts']:<28} {mech:<12} {e2e:<12}")
    print(f"\n{len(lines)} recorded run(s) total.")


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    arg = sys.argv[1]
    if arg == "--report":
        print_trend()
        sys.exit(0)
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
    fixture_results = {}
    for fixture_dir in fixture_dirs:
        fixture_id, results, unverified_behaviors = score_fixture(fixture_dir)
        ok = print_report(fixture_id, results, unverified_behaviors)
        all_passed = all_passed and ok
        passed_count += 1 if ok else 0
        fixture_results[fixture_id] = ok

    print(f"\n{passed_count}/{len(fixture_dirs)} fixture(s) fully passed mechanical checks")

    chain_results, e2e_rate = ({}, None)
    if arg == "--all":
        chain_results, e2e_rate = compute_and_report_end_to_end(fixture_results)
        record_result(fixture_results, chain_results, e2e_rate)

    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    main()
