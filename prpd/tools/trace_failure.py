#!/usr/bin/env python3
"""Trace every recorded failure in .prpd/audit.jsonl to its origin step.

Per the audit-trail requirement: any failure must be traceable to the exact
step that produced it. This tool doesn't infer or guess -- it reports
exactly what the log does and does not support, including flagging entries
that have no step tag at all (which means they are NOT traceable, a real
gap this tool is designed to surface rather than paper over).

An untagged failure can be *resolved* -- never erased -- by a later
`audit_annotation` agent_event whose note explicitly references the
failure's timestamp. Resolution means the failure's origin has been
retroactively attributed with recorded reasoning; the original entry stays
in the log unmodified (the trail is append-only). Resolved failures are
reported distinctly from natively traceable ones: the tool never pretends
a tag existed that didn't.

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
    annotations = []
    for i, line in enumerate(audit_path.read_text().splitlines(), start=1):
        if not line.strip():
            continue
        entry = json.loads(line)
        if entry.get("result") == "fail":
            failures.append((i, entry))
        if entry.get("event") == "audit_annotation":
            annotations.append((i, entry))

    if not failures:
        print(f"no failures recorded in {audit_path}")
        return

    def resolved_by(entry):
        """Return the annotation line no. if an audit_annotation references
        this failure's timestamp, else None."""
        ts = entry.get("ts")
        if not ts:
            return None
        # match on the second-precision prefix so "2026-09-22T18:12:01Z" in a
        # note resolves an entry stamped "2026-09-22T18:12:01.593786+00:00"
        ts_key = ts[:19]
        for line_no, ann in annotations:
            if ts_key in str(ann.get("note", "")):
                return line_no
        return None

    print(f"Found {len(failures)} recorded failure(s) in {audit_path}:\n")
    untraceable = 0
    resolved = 0
    for line_no, entry in failures:
        step = entry.get("step")
        ann_line = resolved_by(entry)
        if step is not None:
            status = "TRACEABLE"
        elif ann_line is not None:
            status = f"RESOLVED -- retroactively attributed by audit_annotation at line {ann_line} (original entry untagged, preserved)"
            resolved += 1
        else:
            status = "NOT TRACEABLE -- no step tag recorded and no resolution annotation"
            untraceable += 1
        print(f"  line {line_no}: {entry['ts']}  command={entry.get('command')!r}")
        print(f"    origin step: {step!r}  [{status}]")

    print(f"\n{len(failures) - untraceable}/{len(failures)} failures are accounted for "
          f"({len(failures) - untraceable - resolved} natively traceable, {resolved} resolved by annotation).")
    if untraceable:
        print(
            f"{untraceable} failure(s) cannot be traced or resolved -- this is a real gap, not a false "
            "negative in this tool. Every prpd.py invocation must be called with --step so future "
            "failures don't repeat this."
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
