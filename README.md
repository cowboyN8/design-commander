# PR Pattern Detective (design-commander)

Multi-agent PR reviewer that catches UX anti-patterns, accessibility regressions, and codebase consistency violations before merge.

## Examiner's map — Stage 4 artifacts

| Required artifact | File | Verify it yourself |
|---|---|---|
| Workflow definition | `WORKFLOW.md` | Agent wiring, handoff conditions, branching logic; commands in `prpd/commands/` |
| Guardrails | `GUARDRAILS.md` | Gate logic in `prpd/tools/prpd.py` (`guardrail` subcommands); sentinel files under each fixture's `.prpd/gates/` |
| Punch-out evidence | `PUNCHOUTS.md` | Enforcement in `prpd.py` (`baseline`/`ticket` refusal paths); records in each fixture's `.prpd/punchouts.jsonl` |
| End-to-end success rate | `SUCCESS_RATE.md` | `python3 prpd/tools/run_fixture.py --all` (scores + appends trend); `--report` prints `prpd/fixtures/results.jsonl` history |
| Audit trail | `AUDIT_TRAIL.md` | `python3 prpd/tools/trace_failure.py prpd/fixtures/01-greenfield/repo`; raw logs in each fixture's `.prpd/audit.jsonl` |

## Repo layout

- `prpd/commands/` — agent prompt specs (`init-agent`, `ticket-agent`, `pr-agent`, `guardrail-challenge`)
- `prpd/tools/` — `prpd.py` (mechanical CLI: baseline/ticket/guardrail/punchout/audit), `run_fixture.py` (fixture scorer + trend log), `chain_executor.py` (deterministic unattended chain replay), `run_chain_agent.py` (agent-driven chain runner with usage capture), `local_runner.py`, `trace_failure.py`
- `prpd/fixtures/` — 7 stage fixtures + 2 end-to-end chains (`chains.json`); each fixture's `repo/.prpd/` holds its real baseline/tickets/gates/punchouts/audit evidence
- `prpd/schemas/` — `baseline.schema.json`, `tickets.schema.json`
- `case-study.md`, `technical-spec.md` — project record and normative spec (supporting context, not examined artifacts)

## Quick verification

```sh
python3 prpd/tools/run_fixture.py --all      # end-to-end chains + per-fixture checks
python3 prpd/tools/run_fixture.py --report   # success-rate trend log
python3 prpd/tools/trace_failure.py prpd/fixtures/01-greenfield/repo  # failure traceability
```
