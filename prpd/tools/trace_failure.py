#!/usr/bin/env python3
"""Trace every recorded failure in .prpd/audit.jsonl to its origin step.

Per the audit-trail requirement: any failure must be traceable to the exact
step that produced it. This tool doesn't infer or guess -- it reports
exactly what the log does and does not support, including flagging entries
that have no step tag at all (which means they are NOT traceable, a real
gap this tool is designed to surface rather than paper over).

Usage:
    python3 prpd/tools/trace_failure.py <repo-dir>
"""

import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 2:
        print(__doc__)
        sys.exit(2)

    repo_dir = Path(sys.argv[1]).resolve()
    audit_path = repo_dir / ".prpd" / "audit.jsonl"
    if not audit_path.is_file():
        print(f"error: {audit_path} does not exist", file=sys.stderr)
        sys.exit(1)

    failures = []
    for i, line in enumerate(audit_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("result") == "fail":
            failures.append((i, entry))

    if not failures:
        print(f"no failures recorded in {audit_path}")
        return

    print(f"Found {len(failures)} recorded failure(s) in {audit_path}:\n")
    untraceable = 0
    for line_no, entry in failures:
        step = entry.get("step")
        traceable = step is not None
        if not traceable:
            untraceable += 1
        status = "TRACEABLE" if traceable else "NOT TRACEABLE -- no step tag recorded"
        print(f"  line {line_no}: {entry['ts']}  command={entry.get('command')!r}")
        print(f"    origin step: {step!r}  [{status}]")

    print(f"\n{len(failures) - untraceable}/{len(failures)} failures trace to an exact origin step.")
    if untraceable:
        print(
            f"{untraceable} failure(s) cannot be traced -- this is a real gap, not a false negative "
            "in this tool. Every prpd.py invocation must be called with --step so future failures "
            "don't repeat this."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
