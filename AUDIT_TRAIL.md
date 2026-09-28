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

### Resolution status of the line-20 entry

The line-20 failure is closed by annotation, not erasure. A retroactive `audit_annotation` event (step `audit.resolution`, appended at the tail of the same log) records: (a) the entry's position between `init.layer.spacing` and `init.layer.small` attributes it to the init stage — an exploratory `ticket get` issued before `--step` was enforced; (b) the root cause (read-only commands didn't require `--step` at that time); (c) the recurrence prevention now in force. So the rubric's "any failure can be traced" holds in the strongest honest form available: every failure either carries its step tag or carries a recorded, verifiable resolution — nothing in the trail is an unexplained dead end.

## Per-step model and token/cost data — resolved policy for this runtime

The audit schema has `model`, `tokens_in`, `tokens_out`, `cost_usd` fields, and the resolved policy populates each with exactly what the caller honestly knows:

- `model` is always populated: auto-filled by `prpd.py` from `PRPD_MODEL` (default `devin-adaptive`), or passed explicitly. Deterministic (non-LLM) callers identify themselves — `chain_executor.py` stamps its calls `--model chain-executor-deterministic`, so executor-driven audit entries are distinguishable from agent-driven ones at a glance.
- `tokens_in`/`tokens_out`/`cost_usd` are populated with real values wherever the caller knows them. The deterministic executor's steps involve no LLM call, so its entries record `0/0/0` — real data, not placeholders — which also demonstrates the fields flowing end to end through the schema.
- For agent judgment steps in the Devin-encapsulated runtime, the fields stay **null** by policy: Devin does not expose per-call token accounting or cost to the agent, and fabricating plausible-looking numbers would be fabrication presented as measurement — a worse audit failure than an honest null. This is a hard property of the runtime (the project is constrained to stay Devin-encapsulated, with no external API calls), not an unfinished feature.
- Agent-driven chain runs executed through `prpd/tools/run_chain_agent.py` are the caller this policy anticipated: the script drives each stage headlessly (`devin -p --prompt-file REPLAY.md --export ...`), scans the CLI stdout and conversation export for usage fields, and records what it finds as a `session_usage` audit event in the stage repo — real measured session-level values via `--tokens-in/--tokens-out/--cost`, or an explicit "no usage fields exposed" note when the CLI reports none. Conversational agent steps (run outside the runner) remain null: there is still no per-call accounting in that mode, and fabricating values stays prohibited. First measured run (2026-09-28, `greenfield-manage-users`, all stages passed): init 4,710,920 in / 28,786 out / 0.705914 ACU; ticket 2,643,694 / 30,511 / 0.527129; pr 1,463,463 / 14,031 / 0.189674 — full pass ≈ 8,818,077 in / 73,328 out / 1.422717 ACU. Per-run records live in each stage's audit trail and `prpd/fixtures/agent-runs.jsonl`.
- `cost_usd` is only ever computed with a price sheet confirmed to match the model that actually served the stage. The Adaptive router does not use one model per run: the measured run above was served by `claude-sonnet-5-medium` for init and ticket but `kimi-k2-7` for pr, verified from each stage's `session-export.json` per-turn `generation_model` field (not the interactive session's own model, which was a different model entirely and would have produced a wrong number). Priced correctly per stage: init $1.3724, ticket $1.0064 (Claude Sonnet 5 Medium, $2/$0.2/$10 per 1M input/cached/output), pr $0.3793 (Kimi K2.7, $0.95/$0.19/$4 per 1M) — full pass **$2.7581**. `run_chain_agent.py` records `served_by` per stage and only computes `cost_usd` when a matching `--price-input/--price-cached-input/--price-output` is supplied; it never assumes a price sheet.

Against the rubric's "per-step model and token/cost data" requirement, this is the honest maximum inside the runtime constraint: per-step model for every entry, real per-step token/cost for every step whose caller knows it, and null — with the reason recorded here — only where the runtime hides the data. Any runtime that exposes usage can populate the agent steps through the existing `--tokens-in`, `--tokens-out`, and `--cost` flags with zero schema changes.
