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
    baseline set <dot.path> <json-val>  Set a field in baseline.json (replaces the whole value)
    baseline append <dot.path> <json>   Append one item to an array field (e.g. components, sources, gaps)
    check-files                         Verify stack/component/token/library paths exist
    ticket validate                     Validate tickets.json against schema
    ticket get <ticket-id>              Print a ticket's recorded context (no error if none yet)
    ticket upsert <ticket-id>           Merge findings/decisions into tickets.json
                                        (--finding "..." / --decision "...", repeatable)
    ticket resolve <ticket-id> <finding-id> --status fixed|overridden
                                        Mark an existing finding fixed/overridden on rerun
                                        (--reasons/--by required for overridden)
"""

import argparse
import hashlib
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


def gates_dir(repo_dir: Path) -> Path:
    return prpd_dir(repo_dir) / "gates"


def punchouts_path(repo_dir: Path) -> Path:
    return prpd_dir(repo_dir) / "punchouts.jsonl"


def record_punchout(repo_dir: Path, point_id: str, decision: str, by: str) -> None:
    path = punchouts_path(repo_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    entry = {"ts": now_iso(), "point_id": point_id, "decision": decision, "by": by}
    with path.open("a") as f:
        f.write(json.dumps(entry) + "\n")


def has_punchout(repo_dir: Path, point_id: str) -> bool:
    path = punchouts_path(repo_dir)
    if not path.exists():
        return False
    for line in path.read_text().splitlines():
        if line.strip() and json.loads(line).get("point_id") == point_id:
            return True
    return False


def file_checksum(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


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


REQUIRED_PUNCHOUTS_FOR_OUTCOME = ["stack_confirmed", "accessibility_target_confirmed"]


def cmd_baseline_set(args, repo_dir: Path) -> None:
    path = prpd_dir(repo_dir) / "baseline.json"
    data = load_json(path)
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        value = args.value

    # Punch-out enforcement: finalizing an outcome is a human decision point,
    # not a mechanical one. This is a real gate, not a prompt reminder --
    # refuse outright if the required sign-offs were never recorded.
    if args.field == "outcome" and value in ("ready", "ready_with_gaps"):
        missing = [p for p in REQUIRED_PUNCHOUTS_FOR_OUTCOME if not has_punchout(repo_dir, p)]
        if missing:
            fail(
                "PUNCH-OUT BLOCKED: cannot set outcome to "
                f"{value!r} -- missing required human sign-off(s): {missing}. "
                "Record them first with `prpd.py punchout record <point_id> --decision ... --by ...`."
            )

    keys = args.field.split(".")
    node = data
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    node[keys[-1]] = value
    save_json(path, data)
    ok(f"set {args.field} = {json.dumps(value)}")


def cmd_baseline_append(args, repo_dir: Path) -> None:
    path = prpd_dir(repo_dir) / "baseline.json"
    data = load_json(path)
    try:
        value = json.loads(args.value)
    except json.JSONDecodeError:
        fail(f"--value is not valid JSON: {args.value!r}")

    # Punch-out enforcement: approving a new design-system extension is a
    # human decision (reuse-vs-exception), not something an agent may decide
    # unilaterally. Require the sign-off to already be on record.
    if args.field == "components" and isinstance(value, dict):
        source = str(value.get("source", ""))
        if "extension" in source or "ticket-agent" in source:
            point_id = f"extension_approved:{value.get('name')}"
            if not has_punchout(repo_dir, point_id):
                fail(
                    f"PUNCH-OUT BLOCKED: cannot add component {value.get('name')!r} sourced from "
                    f"an extension without a recorded sign-off. Record it first with "
                    f"`prpd.py punchout record {point_id} --decision ... --by ...`."
                )

    keys = args.field.split(".")
    node = data
    for key in keys[:-1]:
        node = node.setdefault(key, {})
    target = node.setdefault(keys[-1], [])
    if not isinstance(target, list):
        fail(f"{args.field} is not an array field")
    target.append(value)
    save_json(path, data)
    ok(f"appended to {args.field} (now {len(target)} item(s))")


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

def cmd_ticket_validate(args, repo_dir: Path) -> None:
    path = prpd_dir(repo_dir) / "tickets.json"
    data = load_json(path)
    schema = json.loads((SCHEMA_DIR / "tickets.schema.json").read_text())
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
    required = schema["additionalProperties"]["required"]
    valid_engines = schema["additionalProperties"]["properties"]["findings"]["items"]["anyOf"][1]["properties"]["engine"]["enum"]
    valid_severities = schema["additionalProperties"]["properties"]["findings"]["items"]["anyOf"][1]["properties"]["severity"]["enum"]
    for ticket_id, record in data.items():
        for key in required:
            if key not in record:
                problems.append(f"{ticket_id}: missing required field: {key}")
        for finding in record.get("findings", []):
            if not isinstance(finding, dict):
                continue
            if finding.get("engine") not in valid_engines:
                problems.append(f"{ticket_id}: finding {finding.get('id')} has invalid engine: {finding.get('engine')!r}")
            if finding.get("severity") not in valid_severities:
                problems.append(f"{ticket_id}: finding {finding.get('id')} has invalid severity: {finding.get('severity')!r}")
    if problems:
        fail("invalid tickets.json (install `jsonschema` for full validation):\n  " + "\n  ".join(problems))
    ok(f"{path} passed structural checks (install `jsonschema` for full schema validation)")


def cmd_ticket_get(args, repo_dir: Path) -> None:
    path = prpd_dir(repo_dir) / "tickets.json"
    tickets = json.loads(path.read_text()) if path.exists() else {}
    record = tickets.get(args.ticket_id)
    if record is None:
        # No prior context is a normal, expected case (e.g. a ticket's first
        # review), not an error -- exit 0 so callers don't have to parse
        # stderr to tell "nothing recorded yet" apart from a real failure.
        ok(f"no prior context recorded for {args.ticket_id}")
        return
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

def cmd_ticket_resolve(args, repo_dir: Path) -> None:
    """Mark an existing finding as fixed or overridden (never delete history)."""
    path = prpd_dir(repo_dir) / "tickets.json"
    tickets = load_json(path)
    record = tickets.get(args.ticket_id)
    if record is None:
        fail(f"no context recorded for {args.ticket_id}")

    match = None
    for finding in record.get("findings", []):
        if isinstance(finding, dict) and finding.get("id") == args.finding_id:
            match = finding
            break
    if match is None:
        fail(f"no finding {args.finding_id!r} recorded for {args.ticket_id}")

    if args.status == "overridden":
        if not args.reasons or not args.by:
            fail("--reasons and --by are required to record an override")
        match["override"] = {"reasons": args.reasons, "by": args.by, "at": now_iso()}
        # An override IS a punch-out point (a human accepting risk instead of
        # a fix) -- log it to the same ledger automatically so there is one
        # place to see every human decision across the whole workflow.
        record_punchout(repo_dir, f"blocker_override:{args.finding_id}", args.reasons, args.by)
    match["status"] = args.status
    record["updated_at"] = now_iso()
    save_json(path, tickets)
    ok(f"{args.ticket_id} finding {args.finding_id} marked {args.status}")


# ---------------------------------------------------------------- guardrails
#
# Guardrails are deterministic, automated checks that sit BETWEEN agent
# steps -- not human review, and not embedded inside an agent's own
# reasoning. A passing guardrail writes a sentinel "gate" file under
# .prpd/gates/; the *next* agent's tooling refuses to proceed if the gate
# for the prior step is missing or stale (checksum mismatch against the
# file it certified). A failing guardrail writes nothing and exits 1.

MIN_BASELINE_FOUNDATIONS = 1  # at least one approved/gap/legacy foundation recorded


def cmd_guardrail_init_to_ticket(args, repo_dir: Path) -> None:
    baseline_path = prpd_dir(repo_dir) / "baseline.json"
    if not baseline_path.exists():
        fail("guardrail init-to-ticket: no baseline.json -- /init-agent has not run")

    data = load_json(baseline_path)
    problems = []

    if data.get("outcome") not in ("ready", "ready_with_gaps"):
        problems.append(f"outcome is {data.get('outcome')!r}, must be ready or ready_with_gaps")

    dims = data.get("dimensions", {})
    for dim in ("figma", "coded_system", "source_relationship", "maturity"):
        if not dims.get(dim):
            problems.append(f"dimensions.{dim} is not set")

    if not data.get("accessibility_target"):
        problems.append("accessibility_target is not set")

    if not data.get("stack", {}).get("framework"):
        problems.append("stack.framework is not set")

    if len(data.get("foundations", {})) < MIN_BASELINE_FOUNDATIONS:
        problems.append("no foundations recorded (baseline has no approved/gap/legacy foundations)")

    if problems:
        fail("guardrail init-to-ticket BLOCKED:\n  " + "\n  ".join(problems))

    gates_dir(repo_dir).mkdir(parents=True, exist_ok=True)
    gate = {
        "gate": "init-to-ticket",
        "passed_at": now_iso(),
        "baseline_outcome": data["outcome"],
        "baseline_checksum": file_checksum(baseline_path),
    }
    save_json(gates_dir(repo_dir) / "init.ok", gate)
    ok("guardrail init-to-ticket PASSED -- .prpd/gates/init.ok written")


def cmd_guardrail_ticket_to_pr(args, repo_dir: Path) -> None:
    init_gate_path = gates_dir(repo_dir) / "init.ok"
    if not init_gate_path.exists():
        fail("guardrail ticket-to-pr BLOCKED: init-to-ticket gate has not passed (.prpd/gates/init.ok missing)")

    baseline_path = prpd_dir(repo_dir) / "baseline.json"
    init_gate = load_json(init_gate_path)
    if baseline_path.exists() and init_gate.get("baseline_checksum") != file_checksum(baseline_path):
        fail("guardrail ticket-to-pr BLOCKED: baseline.json changed since init-to-ticket gate passed -- rerun that gate")

    tickets_path = prpd_dir(repo_dir) / "tickets.json"
    if not tickets_path.exists():
        fail(f"guardrail ticket-to-pr BLOCKED: {tickets_path} does not exist -- /ticket-agent has not run")

    tickets = load_json(tickets_path)
    record = tickets.get(args.ticket_id)
    if record is None:
        fail(f"guardrail ticket-to-pr BLOCKED: no record for {args.ticket_id} in tickets.json -- "
             f"/ticket-agent has not reviewed this ticket")

    problems = []
    for key in ("findings", "approved_decisions", "updated_at"):
        if key not in record:
            problems.append(f"ticket record missing required field: {key}")
    if problems:
        fail("guardrail ticket-to-pr BLOCKED:\n  " + "\n  ".join(problems))

    gates_dir(repo_dir).mkdir(parents=True, exist_ok=True)
    gate = {
        "gate": "ticket-to-pr",
        "ticket_id": args.ticket_id,
        "passed_at": now_iso(),
        "tickets_checksum": file_checksum(tickets_path),
    }
    save_json(gates_dir(repo_dir) / f"ticket-{args.ticket_id}.ok", gate)
    ok(f"guardrail ticket-to-pr PASSED for {args.ticket_id} -- .prpd/gates/ticket-{args.ticket_id}.ok written")


# ---------------------------------------------------------------- punch-outs
#
# Explicit human decision points where the workflow must stop for sign-off.
# Distinct from guardrails (which are fully automated, zero-judgment gates):
# a punch-out point is where the system deliberately refuses to decide on
# its own, and the refusal is enforced in code (see cmd_baseline_set /
# cmd_baseline_append above), not just documented as a prompt instruction.

def cmd_punchout_record(args, repo_dir: Path) -> None:
    record_punchout(repo_dir, args.point_id, args.decision, args.by)
    ok(f"punch-out recorded: {args.point_id} (by {args.by})")


def cmd_punchout_log(args, repo_dir: Path) -> None:
    path = punchouts_path(repo_dir)
    if not path.exists():
        ok("no punch-outs recorded yet")
        return
    for line in path.read_text().splitlines():
        if line.strip():
            print(json.dumps(json.loads(line), indent=2))


def cmd_guardrail_status(args, repo_dir: Path) -> None:
    gdir = gates_dir(repo_dir)
    if not gdir.exists() or not any(gdir.iterdir()):
        ok("no gates have passed yet")
        return
    for gate_file in sorted(gdir.iterdir()):
        print(json.dumps(json.loads(gate_file.read_text()), indent=2))


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
    common.add_argument("--repo-dir", default=argparse.SUPPRESS, help="target repository root")
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

    p_guard = sub.add_parser("guardrail", help="deterministic between-step gates (see GUARDRAILS.md)")
    guard_sub = p_guard.add_subparsers(dest="command", required=True)

    p_punch = sub.add_parser("punchout", help="explicit human decision points (see PUNCHOUTS.md)")
    punch_sub = p_punch.add_subparsers(dest="command", required=True)

    p_new = base_sub.add_parser("new", parents=[common], help="create skeleton baseline.json")
    p_new.add_argument("repo_name")
    p_new.set_defaults(func=cmd_baseline_new)

    p_val = base_sub.add_parser("validate", parents=[common], help="validate baseline.json against schema")
    p_val.set_defaults(func=cmd_baseline_validate)

    p_set = base_sub.add_parser("set", parents=[common], help="set a field (dot path) in baseline.json")
    p_set.add_argument("field")
    p_set.add_argument("value")
    p_set.set_defaults(func=cmd_baseline_set)

    p_append = base_sub.add_parser(
        "append", parents=[common],
        help="append a JSON object to an array field (dot path) in baseline.json, e.g. components, sources, gaps",
    )
    p_append.add_argument("field")
    p_append.add_argument("value")
    p_append.set_defaults(func=cmd_baseline_append)

    p_chk = sub.add_parser("check-files", parents=[common], help="verify recorded paths exist")
    p_chk.set_defaults(func=cmd_check_files)

    p_tval = tick_sub.add_parser("validate", parents=[common], help="validate tickets.json against schema")
    p_tval.set_defaults(func=cmd_ticket_validate)

    p_tget = tick_sub.add_parser("get", parents=[common], help="print recorded ticket context")
    p_tget.add_argument("ticket_id")
    p_tget.set_defaults(func=cmd_ticket_get)

    p_tup = tick_sub.add_parser("upsert", parents=[common], help="merge findings/decisions for a ticket")
    p_tup.add_argument("ticket_id")
    p_tup.add_argument("--finding", action="append", help="plain-text finding")
    p_tup.add_argument("--finding-json", action="append", help="finding object as JSON")
    p_tup.add_argument("--decision", action="append")
    p_tup.set_defaults(func=cmd_ticket_upsert)

    p_tres = tick_sub.add_parser(
        "resolve", parents=[common],
        help="mark an existing finding fixed or overridden (rerun workflow; never deletes history)",
    )
    p_tres.add_argument("ticket_id")
    p_tres.add_argument("finding_id")
    p_tres.add_argument("--status", choices=["fixed", "overridden"], required=True)
    p_tres.add_argument("--reasons", help="required when --status overridden")
    p_tres.add_argument("--by", help="required when --status overridden")
    p_tres.set_defaults(func=cmd_ticket_resolve)

    p_gi2t = guard_sub.add_parser(
        "init-to-ticket", parents=[common],
        help="deterministic gate: refuses unless baseline is ready/ready_with_gaps and complete; writes .prpd/gates/init.ok",
    )
    p_gi2t.set_defaults(func=cmd_guardrail_init_to_ticket)

    p_gt2p = guard_sub.add_parser(
        "ticket-to-pr", parents=[common],
        help="deterministic gate: refuses unless init.ok exists and the ticket has recorded findings/decisions; writes .prpd/gates/ticket-<id>.ok",
    )
    p_gt2p.add_argument("ticket_id")
    p_gt2p.set_defaults(func=cmd_guardrail_ticket_to_pr)

    p_gstat = guard_sub.add_parser("status", parents=[common], help="print all gates that have passed")
    p_gstat.set_defaults(func=cmd_guardrail_status)

    p_prec = punch_sub.add_parser("record", parents=[common], help="record a human decision at an explicit punch-out point")
    p_prec.add_argument("point_id")
    p_prec.add_argument("--decision", required=True)
    p_prec.add_argument("--by", required=True)
    p_prec.set_defaults(func=cmd_punchout_record)

    p_plog = punch_sub.add_parser("log", parents=[common], help="print every recorded punch-out decision")
    p_plog.set_defaults(func=cmd_punchout_log)

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
