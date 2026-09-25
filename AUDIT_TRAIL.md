# PR Pattern Detective — Audit Trail

`.prpd/audit.jsonl` is an append-only, structured log. Every `prpd.py` helper call automatically logs a `helper_call` entry (timestamp, command, step, result); agents additionally emit `agent_event` entries for judgment moments via `prpd.py audit <event>`.

## Coverage of all workflow steps — now enforced, not just requested

Every mutating, decision-producing command (`baseline new/set/append`, `ticket upsert/resolve`, `guardrail init-to-ticket/ticket-to-pr`, `punchout record`, `audit`) now requires `--step` — argparse refuses to run without it. Read-only inspection commands (`validate`, `check-files`, `ticket get`, `guardrail status`, `punchout log`) don't produce new state, so `--step` stays optional there.

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

## Per-step model and token/cost data — honest status, not fabricated numbers

The schema has always had `model`, `tokens_in`, `tokens_out`, `cost_usd` fields. Checking the real data across all 4 fixtures: **every one of these fields is null in every entry recorded so far.** The plumbing exists; the data was never populated, because doing so honestly requires something this project doesn't currently have.

Here's the actual constraint, stated plainly rather than worked around with plausible-looking fake numbers: **an interactively-run agent (this session) has no runtime access to its own per-call token counts or cost.** I am not exposed to that accounting information about my own inference — inventing specific-looking numbers here would be fabrication, not measurement, and would fail worse than leaving the field honestly null.

What *can* be done honestly:
- `--model` can be populated with the identifier the system actually discloses (in this environment: "Devin, powered by Adaptive" — a routing layer, not a specific foundation model name). This is now the convention going forward for interactive sessions.
- `tokens_in`/`tokens_out`/`cost_usd` are correctly populated **only when `prpd.py` is invoked by something that actually has that data** — e.g. a wrapper script driving the LLM API directly, which receives `usage.prompt_tokens`/`usage.completion_tokens` and a computed cost in the API response, and passes them straight through:

```python
response = client.chat.completions.create(...)
subprocess.run([
    "python3", "prpd.py", "ticket", "upsert", ticket_id,
    "--finding-json", finding_json,
    "--step", "ticket.readiness",
    "--model", response.model,
    "--tokens-in", str(response.usage.prompt_tokens),
    "--tokens-out", str(response.usage.completion_tokens),
    "--cost", str(estimate_cost(response)),
    "--repo-dir", repo_dir,
])
```

This is exactly the automated/unattended execution mode discussed as an open item elsewhere (`technical-spec.md §10.2`, `SUCCESS_RATE.md`) — token/cost data becomes available as a natural side effect of *that* architecture, not as a separate thing to bolt on. Populating it accurately in an interactive session is not currently possible, and the doc says so instead of quietly leaving four always-null fields looking like an oversight.
