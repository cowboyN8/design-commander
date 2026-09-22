#!/usr/bin/env python3
"""Deterministic helpers for PR Pattern Detective.

Agent commands (see prpd/commands/) call these for all mechanical work:
baseline/ticket file IO, schema validation, and file-existence checks.
LLM output is never trusted as evidence for checks code can perform.

Usage:
    python3 prpd/tools/prpd.py <command> [options] [--repo-dir PATH]

Commands:
    baseline new <repo-name>            Create a skeleton .prpd/baseline.json
    baseline validate                   Validate baseline.json against schema
    baseline set <dot.path> <json-val>  Set a field in baseline.json
    check-files                         Verify stack/component/token/library paths exist
    ticket get <ticket-id>              Print a ticket's recorded context
    ticket upsert <ticket-id>           Merge findings/decisions into tickets.json
                                        (--finding "..." / --decision "...", repeatable)
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
SCHEMA_DIR = TOOLS_DIR.parent / "schemas"

DEFAULT_BASELINE = {
    "version": 1,
    "repo": "",
    "initialized_at": "",
    "outcome": "blocked",
    "dimensions": {
        "figma": "absent",
        "coded_system": "absent",
        "source_relationship": "not_applicable",
        "maturity": "greenfield",
    },
    "stack": {"framework": "", "styling": "", "component_dir": "", "token_files": []},
    "sources": [],
    "accessibility_target": "WCAG 2.2 AA",
    "foundations": {},
    "components": [],
    "gaps": [],
    "legacy_patterns": [],
    "exceptions": [],
    "migrations": [],
    "library_page": "",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def prpd_dir(repo_dir: Path) -> Path:
    return repo_dir / ".prpd"


def load_json(path: Path) -> dict:
    if not path.exists():
        fail(f"{path} does not exist")
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        fail(f"{path} is not valid JSON: {e}")


def save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + "\n")


def audit(repo_dir: Path, entry: dict) -> None:
    """Append one event to .prpd/audit.jsonl."""
    path = prpd_dir(repo_dir) / "audit.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": now_iso(), **entry}
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def fail(msg: str) -> None:
    print(f"error: {msg}", file=sys.stderr)
    sys.exit(1)


def ok(msg: str) -> None:
    print(f"ok: {msg}")


# ---------------------------------------------------------------- baseline

def cmd_baseline_new(args, repo_dir: Path) -> None:
    path = prpd_dir(repo_dir) / "baseline.json"
    if path.exists():
        fail(f"{path} already exists; refusing to overwrite")
    baseline = dict(DEFAULT_BASELINE)
    baseline["repo"] = args.repo_name
    baseline["initialized_at"] = now_iso()
    save_json(path, baseline)
    ok(f"created {path} (outcome=blocked until init completes)")


def cmd_baseline_validate(args, repo_dir: Path) -> None:
    path = prpd_dir(repo_dir) / "baseline.json"
    data = load_json(path)
    schema = json.loads((SCHEMA_DIR / "baseline.schema.json").read_text())
    try:
        import jsonschema  # type: ignore
        jsonschema.validate(data, schema)
        ok(f"{path} is valid")
        return
    except ImportError:
        pass  # fall back to structural checks below
    except Exception as e:
        fail(str(e))

    problems = []
    for key in schema["required"]:
        if key not in data:
            problems.append(f"missing required field: {key}")
    dims = data.get("dimensions", {})
    dim_schema = schema["properties"]["dimensions"]["properties"]
    for dim, spec in dim_schema.items():
        if dims.get(dim) not in spec["enum"]:
            problems.append(f"dimensions.{dim} must be one of {spec['enum']}")
    if data.get("outcome") not in schema["properties"]["outcome"]["enum"]:
        problems.append("outcome must be ready | ready_with_gaps | blocked")
    if problems:
        fail("invalid baseline (install `jsonschema` for full validation):\n  " + "\n  ".join(problems))
    ok(f"{path} passed structural checks (install `jsonschema` for full schema validation)")


def cmd_baseline_set(args, repo_dir: Path) -> None:
    path = prpd_dir(repo_dir) / "baseline.json"
    data = load_json(path)
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value
    keys = args.field.split(".")
    node = data
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value
    save_json(path, data)
    ok(f"set {args.field} = {json.dumps(value)}")


# ---------------------------------------------------------------- checks

def cmd_check_files(args, repo_dir: Path) -> None:
    data = load_json(prpd_dir(repo_dir) / "baseline.json")
    stack = data.get("stack", {})
    missing = []

    if stack.get("component_dir") and not (repo_dir / stack["component_dir"]).is_dir():
        missing.append(f"component_dir: {stack['component_dir']}")
    for f in stack.get("token_files", []):
        if not (repo_dir / f).is_file():
            missing.append(f"token_file: {f}")
    for comp in data.get("components", []):
        p = comp.get("path")
        if p and comp.get("status") == "approved" and not (repo_dir / p).exists():
            missing.append(f"component {comp['name']}: {p}")
    lib = data.get("library_page")
    if lib and not (repo_dir / lib).is_file():
        missing.append(f"library_page: {lib}")

    if missing:
        fail("missing expected files:\n  " + "\n  ".join(missing))
    ok("all recorded baseline paths exist")


# ---------------------------------------------------------------- tickets

def cmd_ticket_get(args, repo_dir: Path) -> None:
    tickets = load_json(prpd_dir(repo_dir) / "tickets.json")
    record = tickets.get(args.ticket_id)
    if record is None:
        fail(f"no context recorded for {args.ticket_id}")
    print(json.dumps(record, indent=2))


def cmd_ticket_upsert(args, repo_dir: Path) -> None:
    path = prpd_dir(repo_dir) / "tickets.json"
    tickets = load_json(path) if path.exists() else {}
    record = tickets.setdefault(
        args.ticket_id, {"findings": [], "approved_decisions": [], "updated_at": ""}
    )
    record["findings"].extend(args.finding or [])
    for raw in args.finding_json or []:
        try:
            record["findings"].append(json.loads(raw))
        except json.JSONDecodeError as e:
            fail(f"--finding-json is not valid JSON: {e}")
    record["approved_decisions"].extend(args.decision or [])
    record["updated_at"] = now_iso()
    tickets[args.ticket_id] = record
    save_json(path, tickets)
    ok(f"updated {path} for {args.ticket_id}")


# ---------------------------------------------------------------- cli

def cmd_audit(args, repo_dir: Path) -> None:
    audit(repo_dir, {
        "kind": "agent_event",
        "event": args.event,
        "step": args.step,
        "model": args.model,
        "tokens_in": args.tokens_in,
        "tokens_out": args.tokens_out,
        "cost_usd": args.cost,
        "note": args.note,
    })
    ok("audit event recorded")


def main() -> None:
    parser = argparse.ArgumentParser(prog="prpd")
    parser.add_argument("--repo-dir", default=".", help="target repository root")

    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--step", help="workflow step emitting this call, e.g. init.layer.color")
    common.add_argument("--model", help="model identifier for audit entries")
    common.add_argument("--tokens-in", type=int, help="input tokens for audit entries")
    common.add_argument("--tokens-out", type=int, help="output tokens for audit entries")
    common.add_argument("--cost", type=float, help="step cost in USD for audit entries")

    sub = parser.add_subparsers(dest="group", required=True)

    p_base = sub.add_parser("baseline", help="baseline.json operations")
    base_sub = p_base.add_subparsers(dest="command", required=True)

    p_tick = sub.add_parser("ticket", help="tickets.json operations")
    tick_sub = p_tick.add_subparsers(dest="command", required=True)

    p_new = base_sub.add_parser("new", parents=[common], help="create skeleton baseline.json")
    p_new.add_argument("repo_name")
    p_new.set_defaults(func=cmd_baseline_new)

    p_val = base_sub.add_parser("validate", parents=[common], help="validate baseline.json against schema")
    p_val.set_defaults(func=cmd_baseline_validate)

    p_set = base_sub.add_parser("set", parents=[common], help="set a field (dot path) in baseline.json")
    p_set.add_argument("field")
    p_set.add_argument("value")
    p_set.set_defaults(func=cmd_baseline_set)

    p_chk = sub.add_parser("check-files", parents=[common], help="verify recorded paths exist")
    p_chk.set_defaults(func=cmd_check_files)

    p_tget = tick_sub.add_parser("get", parents=[common], help="print recorded ticket context")
    p_tget.add_argument("ticket_id")
    p_tget.set_defaults(func=cmd_ticket_get)

    p_tup = tick_sub.add_parser("upsert", parents=[common], help="merge findings/decisions for a ticket")
    p_tup.add_argument("ticket_id")
    p_tup.add_argument("--finding", action="append", help="plain-text finding")
    p_tup.add_argument("--finding-json", action="append", help="finding object as JSON")
    p_tup.add_argument("--decision", action="append")
    p_tup.set_defaults(func=cmd_ticket_upsert)

    p_audit = sub.add_parser("audit", parents=[common], help="emit an audit event to audit.jsonl")
    p_audit.add_argument("event", help="event name, e.g. layer_approved, question_asked")
    p_audit.add_argument("--note", help="free-text detail")
    p_audit.set_defaults(func=cmd_audit)

    args = parser.parse_args()
    repo_dir = Path(args.repo_dir).resolve()
    entry = {
        "kind": "helper_call",
        "command": f"{args.group} {getattr(args, 'command', '')}".strip(),
        "step": args.step,
        "model": args.model,
        "tokens_in": args.tokens_in,
        "tokens_out": args.tokens_out,
        "cost_usd": args.cost,
    }
    try:
        args.func(args, repo_dir)
    except SystemExit as e:
        entry["result"] = "ok" if e.code == 0 else "fail"
        audit(repo_dir, entry)
        raise
    entry["result"] = "ok"
    audit(repo_dir, entry)


if __name__ == "__main__":
    main()
