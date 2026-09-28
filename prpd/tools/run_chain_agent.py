#!/usr/bin/env python3
"""Agent-driven chain runner with per-run usage capture.

Runs each stage of a fixture chain headlessly through the Devin CLI
(`devin -p`), captures whatever usage data the CLI exposes, records real
measured values into the run's own audit trail, and prints a per-run
usage report. This is the caller the audit schema anticipated: a script
that drives the runtime and knows the usage numbers, so tokens_in /
tokens_out / cost_usd stop being null for agent-driven runs.

Usage:
    python3 prpd/tools/run_chain_agent.py --chain greenfield-manage-users \
        --work-root /tmp/prpd-agent-run-1
    python3 prpd/tools/run_chain_agent.py --list-chains

Requirements:
    - `devin` on PATH (or pass --devin-bin), authenticated (`devin auth login`).
    - Stages run unattended: the replay prompt drives the agent and the
      fixture's user_simulation block answers its questions. Permission
      mode defaults to `dangerous` so the unattended agent can run prpd.py
      and npm without approval prompts (override with --permission-mode).

Honesty policy: usage fields are populated only with values the CLI
actually reported. If a run exposes no usage data, the report says so and
the raw CLI stdout + conversation export are kept under the work dir for
inspection -- nothing is fabricated.
"""

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent.parent
FIXTURES_DIR = REPO_ROOT / "prpd" / "fixtures"
LOCAL_RUNNER = TOOLS_DIR / "local_runner.py"
RUN_FIXTURE = TOOLS_DIR / "run_fixture.py"
PRPD_PY = TOOLS_DIR / "prpd.py"
CHAINS_PATH = FIXTURES_DIR / "chains.json"
RUNS_LOG = FIXTURES_DIR / "agent-runs.jsonl"

STAGE_AGENTS = {"init": "init-agent", "ticket": "ticket-agent", "pr": "pr-agent"}

USAGE_KEY_RE = re.compile(r"token|usage|cost|acu|credit", re.I)
USAGE_LINE_RE = re.compile(
    r"(?i)\b(tokens?[_ ]?in|tokens?[_ ]?out|tokens?|acu|credits?|cost)\b[^0-9]{0,24}"
    r"(\$?\d[\d,]*(?:\.\d+)?)"
)
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def find_devin(explicit: str) -> str:
    if explicit:
        return explicit
    found = shutil.which("devin")
    if found:
        return found
    bundled = Path("/Applications/Devin.app/Contents/Resources/app/extensions/windsurf/devin/bin/devin")
    if bundled.is_file():
        return str(bundled)
    print("error: devin CLI not found on PATH; pass --devin-bin", file=sys.stderr)
    sys.exit(2)


def run(cmd: list, cwd: Path = None, timeout: float = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def load_chains() -> dict:
    return json.loads(CHAINS_PATH.read_text())


def resolve_stages(chain_id: str) -> list:
    chains = load_chains()["chains"]
    chain = next((c for c in chains if c["id"] == chain_id), None)
    if chain is None:
        print(f"error: unknown chain {chain_id!r}; known: {[c['id'] for c in chains]}", file=sys.stderr)
        sys.exit(2)
    stages = []
    for fixture_id in chain["fixtures"]:
        fixture = json.loads((FIXTURES_DIR / fixture_id / "fixture.json").read_text())
        stage = fixture.get("stage")
        agent = STAGE_AGENTS.get(stage)
        if not agent:
            print(f"error: fixture {fixture_id} has unmapped stage {stage!r}", file=sys.stderr)
            sys.exit(2)
        stages.append({"fixture": fixture_id, "stage": stage, "agent": agent})
    return stages


def prepare_stage(agent: str, fixture_id: str, work_dir: Path, previous: Path = None) -> Path:
    args = [
        sys.executable, str(LOCAL_RUNNER),
        "--agent", agent,
        "--fixture", str(FIXTURES_DIR / fixture_id),
        "--work-dir", str(work_dir),
    ]
    if previous:
        args.extend(["--previous-work-dir", str(previous)])
    proc = run(args)
    if proc.returncode != 0:
        print(proc.stdout + proc.stderr, file=sys.stderr)
        raise RuntimeError(f"stage preparation failed for {fixture_id}")
    return work_dir / "repo"


def execute_stage(devin: str, work_dir: Path, permission_mode: str, model: str, timeout: float) -> int:
    stdout_log = work_dir / "session-stdout.log"
    export_path = work_dir / "session-export.json"
    cmd = [
        devin, "-p",
        "--prompt-file", str(work_dir / "REPLAY.md"),
        "--export", str(export_path),
        "--permission-mode", permission_mode,
        "--respect-workspace-trust", "false",
    ]
    if model:
        cmd.extend(["--model", model])
    print(f"  $ {' '.join(cmd)}", flush=True)
    started = time.time()
    try:
        proc = subprocess.run(cmd, cwd=work_dir, timeout=timeout)
        elapsed = time.time() - started
        print(f"  devin -p finished in {elapsed/60:.1f} min (exit {proc.returncode})")
        return proc.returncode
    except subprocess.TimeoutExpired:
        print(f"  devin -p TIMED OUT after {timeout/60:.0f} min", file=sys.stderr)
        return 124


def _walk_json(node, path="", hits=None):
    if hits is None:
        hits = []
    if isinstance(node, dict):
        for k, v in node.items():
            key_path = f"{path}.{k}" if path else k
            if USAGE_KEY_RE.search(str(k)):
                hits.append({"key": key_path, "value": v})
            _walk_json(v, key_path, hits)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            _walk_json(v, f"{path}[{i}]", hits)
    return hits


def extract_usage(work_dir: Path) -> dict:
    stdout_log = work_dir / "session-stdout.log"
    export_path = work_dir / "session-export.json"
    found = {"from_stdout": [], "from_export": [], "final_metrics": None, "acu_cost": None, "served_by": None, "found": False}

    if stdout_log.is_file():
        for line in stdout_log.read_text(errors="replace").splitlines():
            clean = ANSI_RE.sub("", line)
            for m in USAGE_LINE_RE.finditer(clean):
                found["from_stdout"].append({"line": clean.strip()[:200], "label": m.group(1), "value": m.group(2)})
    if export_path.is_file():
        try:
            data = json.loads(export_path.read_text())
        except json.JSONDecodeError as e:
            found["from_export"] = [{"error": f"export not valid JSON: {e}"}]
        else:
            # ATIF export (verified on a real run): final_metrics carries session
            # totals; each step carries metrics.prompt_tokens/completion_tokens
            # and extra.committed_acu_cost. Prefer the session totals.
            fm = data.get("final_metrics") or {}
            if isinstance(fm, dict) and fm:
                found["final_metrics"] = {
                    "tokens_in": fm.get("total_prompt_tokens"),
                    "tokens_out": fm.get("total_completion_tokens"),
                    "cached_tokens": fm.get("total_cached_tokens"),
                    "steps": fm.get("total_steps"),
                }
            acu = 0.0
            models = set()
            agent = data.get("agent") or {}
            if isinstance(agent, dict) and agent.get("model_name"):
                models.add(str(agent["model_name"]))
            for s in data.get("steps", []) if isinstance(data.get("steps"), list) else []:
                if isinstance(s, dict):
                    v = (s.get("extra") or {}).get("generation_model") or s.get("model_name")
                    if v:
                        models.add(str(v))
                    c = (s.get("extra") or {}).get("committed_acu_cost")
                    if isinstance(c, (int, float)):
                        acu += c
            if models:
                found["served_by"] = sorted(models)
            if acu:
                found["acu_cost"] = round(acu, 6)
            found["from_export"] = _walk_json(data)[:50]
    found["found"] = bool(found["from_stdout"] or found["final_metrics"] or found["acu_cost"] or found["from_export"])
    return found


def pick_numbers(usage: dict) -> dict:
    """Map discovered usage fields to audit semantics. Only unambiguous,
    numeric values are used -- anything else stays out of the audit trail.
    ACU is a billing unit, not USD, so it is reported separately and never
    written into cost_usd."""
    nums = {"tokens_in": None, "tokens_out": None, "cached_tokens": None, "cost_usd": None, "acu": None, "served_by": None, "sources": []}
    if usage.get("served_by"):
        nums["served_by"] = usage["served_by"]
    fm = usage.get("final_metrics")
    if fm and isinstance(fm.get("tokens_in"), (int, float)):
        nums["tokens_in"] = fm["tokens_in"]
        nums["sources"].append("export:final_metrics.total_prompt_tokens")
    if fm and isinstance(fm.get("tokens_out"), (int, float)):
        nums["tokens_out"] = fm["tokens_out"]
        nums["sources"].append("export:final_metrics.total_completion_tokens")
    if fm and isinstance(fm.get("cached_tokens"), (int, float)):
        nums["cached_tokens"] = fm["cached_tokens"]
    if isinstance(usage.get("acu_cost"), (int, float)) and usage["acu_cost"] > 0:
        nums["acu"] = usage["acu_cost"]
        nums["sources"].append("export:steps[].extra.committed_acu_cost (sum)")
    if nums["tokens_in"] is None:
        for item in usage["from_export"] + usage["from_stdout"]:
            key = str(item.get("key") or item.get("label") or "")
            raw = item.get("value")
            if isinstance(raw, str) and re.fullmatch(r"\d[\d,]*(\.\d+)?", raw):
                value = float(raw.replace(",", ""))
            elif isinstance(raw, (int, float)) and not isinstance(raw, bool):
                value = float(raw)
            else:
                continue
            lk = key.lower()
            if nums["tokens_in"] is None and "prompt" in lk:
                nums["tokens_in"] = value
                nums["sources"].append(f"export:{key}")
            elif nums["tokens_out"] is None and "completion" in lk:
                nums["tokens_out"] = value
                nums["sources"].append(f"export:{key}")
            elif nums["cost_usd"] is None and ("cost" in lk or "usd" in lk) and "acu" not in lk:
                nums["cost_usd"] = value
                nums["sources"].append(f"export:{key}")
    return nums


def record_usage(repo_dir: Path, stage: str, nums: dict, usage: dict, prices=None) -> None:
    if prices and nums["tokens_in"] is not None:
        # cost_usd computed from measured tokens x stated per-1M prices --
        # arithmetic on measured usage with a declared price assumption,
        # not a billed amount. ACU is never conflated with USD.
        cached = nums.get("cached_tokens") or 0
        uncached = max(nums["tokens_in"] - cached, 0)
        out = nums["tokens_out"] or 0
        cost = uncached * prices[0] / 1e6 + cached * prices[1] / 1e6 + out * prices[2] / 1e6
        nums["cost_usd"] = round(cost, 6)
        nums["sources"].append("computed: tokens x stated per-1M prices")
    src = ", ".join(nums["sources"]) or "no usage fields exposed by CLI"
    acu = f"; acu_cost={nums['acu']} (billing unit, not USD)" if nums["acu"] is not None else ""
    served = f"; served_by={','.join(nums['served_by'])}" if nums.get("served_by") else ""
    price_note = ""
    if prices and nums["cost_usd"] is not None:
        price_note = (f"; cost_usd={nums['cost_usd']} computed from measured tokens x stated per-1M prices "
                      f"(input ${prices[0]}, cached-input ${prices[1]}, output ${prices[2]}) -- arithmetic on "
                      "measured usage with a declared price assumption, not a billed amount")
    note = f"session-level usage captured by run_chain_agent.py from {src}{acu}{served}{price_note}"
    cmd = [sys.executable, str(PRPD_PY), "audit", "session_usage",
           "--step", f"{stage}.usage", "--note", note, "--repo-dir", str(repo_dir)]
    if nums["tokens_in"] is not None:
        cmd += ["--tokens-in", str(int(nums["tokens_in"]))]
    if nums["tokens_out"] is not None:
        cmd += ["--tokens-out", str(int(nums["tokens_out"]))]
    if nums["cost_usd"] is not None:
        cmd += ["--cost", str(nums["cost_usd"])]
    proc = run(cmd)
    if proc.returncode != 0:
        print(f"  warning: could not record usage audit entry: {proc.stderr.strip()}", file=sys.stderr)


def verify_stage(fixture_id: str, repo_dir: Path) -> bool:
    proc = run([sys.executable, str(RUN_FIXTURE), str(FIXTURES_DIR / fixture_id), "--repo-dir", str(repo_dir)])
    print(proc.stdout.strip())
    return proc.returncode == 0


def log_run(entry: dict) -> None:
    RUNS_LOG.parent.mkdir(parents=True, exist_ok=True)
    with RUNS_LOG.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--chain", help="chain id from prpd/fixtures/chains.json")
    parser.add_argument("--list-chains", action="store_true", help="list known chains and exit")
    parser.add_argument("--work-root", type=Path, help="directory for this run's stage work dirs")
    parser.add_argument("--devin-bin", default=None, help="path to the devin CLI binary")
    parser.add_argument("--permission-mode", default="dangerous",
                        choices=["auto", "accept-edits", "smart", "dangerous"],
                        help="permission mode for the unattended agent (default: dangerous)")
    parser.add_argument("--model", default=None, help="model for the headless runs")
    parser.add_argument("--stage-timeout", type=float, default=1800, help="per-stage timeout in seconds")
    parser.add_argument("--start-at", type=int, default=1, help="1-based stage number to start from (earlier stages are assumed already run)")
    parser.add_argument("--price-input", type=float, default=None, help="USD per 1M uncached input tokens for the model that runs")
    parser.add_argument("--price-cached-input", type=float, default=None, help="USD per 1M cached input tokens")
    parser.add_argument("--price-output", type=float, default=None, help="USD per 1M output tokens")
    args = parser.parse_args()

    if args.list_chains:
        for c in load_chains()["chains"]:
            print(f"{c['id']}: {c['description']}")
        return
    if not args.chain or not args.work_root:
        parser.error("--chain and --work-root are required (or use --list-chains)")

    devin = find_devin(args.devin_bin)
    stages = resolve_stages(args.chain)
    work_root = args.work_root.resolve()
    work_root.mkdir(parents=True, exist_ok=True)
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S")

    prices = None
    price_args = (args.price_input, args.price_cached_input, args.price_output)
    if any(p is not None for p in price_args):
        if all(p is not None for p in price_args):
            prices = price_args
        else:
            print("warning: partial --price-* arguments ignored; all three are required to compute cost_usd", file=sys.stderr)

    print(f"Chain: {args.chain} ({len(stages)} stages) -> {work_root}")
    print(f"Devin CLI: {devin}\n")

    previous_work_dir = None
    chain_passed = True
    totals = {"tokens_in": 0, "tokens_out": 0, "acu": 0.0, "usd": 0.0}
    for i, s in enumerate(stages, start=1):
        if i < args.start_at:
            previous_work_dir = work_root / s["stage"]
            continue
        work_dir = work_root / s["stage"]
        print(f"\n== stage {i}/{len(stages)}: {s['stage']} ({s['fixture']}) ==")
        repo_dir = prepare_stage(s["agent"], s["fixture"], work_dir, previous_work_dir)
        print(f"  prepared: {repo_dir}")

        exit_code = execute_stage(devin, work_dir, args.permission_mode, args.model, args.stage_timeout)
        usage = extract_usage(work_dir)
        nums = pick_numbers(usage)

        if nums["tokens_in"] is not None or nums["tokens_out"] is not None or nums["acu"] is not None or nums["cost_usd"] is not None:
            served = f" served_by={','.join(nums['served_by'])}" if nums.get("served_by") else ""
            print(f"  usage captured: tokens_in={nums['tokens_in']} tokens_out={nums['tokens_out']} "
                  f"acu={nums['acu']} cost_usd={nums['cost_usd']}{served}")
            totals["tokens_in"] += nums["tokens_in"] or 0
            totals["tokens_out"] += nums["tokens_out"] or 0
            totals["acu"] += nums["acu"] or 0.0
            totals["usd"] += nums["cost_usd"] or 0.0
        else:
            print("  usage: no numeric usage fields exposed by the CLI for this run "
                  "(raw stdout + export kept under the work dir; nothing fabricated)")

        stage_ok = exit_code == 0 and verify_stage(s["fixture"], repo_dir)
        record_usage(repo_dir, s["stage"], nums, usage, prices)
        log_run({
            "ts": datetime.now(timezone.utc).isoformat(),
            "run_id": run_id,
            "chain": args.chain,
            "stage": s["stage"],
            "fixture": s["fixture"],
            "devin_exit": exit_code,
            "verified": stage_ok,
            "work_dir": str(work_dir),
            "usage": {k: v for k, v in nums.items() if k != "sources"},
            "usage_sources": nums["sources"],
        })
        if not stage_ok:
            chain_passed = False
            print(f"  stage {s['stage']} FAILED -- stopping chain (see output above)")
            break
        previous_work_dir = work_dir

    print(f"\n== chain {args.chain}: {'PASSED' if chain_passed else 'FAILED'} (run {run_id}) ==")
    if totals["tokens_in"] or totals["acu"]:
        print(f"Chain usage totals: tokens_in={totals['tokens_in']} tokens_out={totals['tokens_out']} acu_cost={round(totals['acu'], 6)} usd_cost={round(totals['usd'], 4) if prices else 'n/a (no --price-* given)'}")
    print(f"Per-run log: {RUNS_LOG}")
    sys.exit(0 if chain_passed else 1)


if __name__ == "__main__":
    main()
