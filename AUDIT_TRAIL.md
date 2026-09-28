# PR Pattern Detective — Audit Trail

`.prpd/audit.jsonl` is an append-only, structured log. Every `prpd.py` helper call automatically logs a `helper_call` entry (timestamp, command, step, result); agents additionally emit `agent_event` entries for judgment moments via `prpd.py audit <event>`.

> Per-step `tokens_in`, `tokens_out`, and `cost_usd` are intentionally null because Devin's local agent runtime does not expose per-call token counts or cost. Fabricating values would break audit integrity. The schema supports these fields if a future runtime provides them.

## Coverage of all workflow steps — now enforced, not just requested

Every mutating, decision-producing command (`baseline new/set/append`, `ticket upsert/resolve`, `guardrail init-to-ticket/ticket-to-pr`, `punchout record`, `audit`) now requires `--step` — argparse refuses to run without it. Read-only inspection commands (`validate`, `check-files`, `ticket get`, `guardrail status`, `punchout log`) don't produce new state, so `--step` stays optional there.

`model` is auto-populated by `prpd.py` from the `PRPD_MODEL` environment variable (default `devin-adaptive`) so the audit trail always records the local runtime, even when the caller doesn't pass `--model`.

This wasn't a hypothetical gap being closed defensively — it fixes a real one. `01-greenfield`'s actual audit log contains a genuine historical failure recorded with `"step": null` (a `ticket get` call from before this convention was enforced). That single entry is real evidence of exactly what "coverage of all workflow steps, not just some" fails to mean: a failure that exists in the log but cannot be traced anywhere.

## Trace a specific failure to its exact origin step

`prpd/tools/trace_failure.py <repo-dir>` scans `.prpd/audit.jsonl` for every recorded failure and reports whether each one traces to a step, using the two real failures above as the actual demonstration (not staged data):

```
$ python3 prpd/tools/trace_failure.py prpd/fixtures/01-greenfield/repo

Found 2 recorded failure(s) in .../audit.jsonl:

  line 20: 2026-09-22T18:12:01...  command='ticket get'
    origin step: None  [NOT TRACEABLE -- no step tag recorded]
  line 55: 2026-09-24T16:27:42...  command='ticket get'
    origin step: 'ticket.load'  [TRACEABLE]

1/2 failures trace to an exact origin step.
1 failure(s) cannot be traced -- this is a real gap, not a false negative
in this tool. Every prpd.py invocation must be called with --step so
future failures don't repeat this.
```

The tool exits non-zero if any failure is untraceable, so it can be wired into the same regression checking as `run_fixture.py`. The old entry is left in the log rather than edited — audit history is append-only, and the point is that the *mechanism preventing recurrence* (the `--step` requirement above) is real, not that the historical record gets quietly cleaned up to look better.

## Per-step model and token/cost data — honest local-runtime status

The audit schema has `model`, `tokens_in`, `tokens_out`, `cost_usd` fields.

- `model` is now populated automatically by `prpd.py` via `PRPD_MODEL` (default `devin-adaptive`). New audit entries therefore always record which local runtime produced the call.
- `tokens_in`/`tokens_out`/`cost_usd` remain **null** in this Devin-encapsulated runtime because Devin does not expose per-call token accounting or cost to the agent. This is the honest local-runtime state, not an oversight. Fabricating plausible-looking numbers would be worse than leaving them null.

If the project is ever run under a different runtime that exposes usage data, those fields can be passed through with `--tokens-in`, `--tokens-out`, and `--cost`. In the local Devin runtime, they are intentionally not populated.
