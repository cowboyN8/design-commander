# PR Pattern Detective — Workflow Definition

This is the canonical description of the end-to-end, multi-step workflow connecting the three validated agents. It is the single artifact that answers "how are the agents wired together, and what has to be true to move from one to the next."

Status note: the **Guardrails** and **Punch-Out** sections below describe the mechanisms as built as of this document's last update. See `GUARDRAILS.md` and the punch-out sections of each command file for their full specs.

One distinction matters for Stage 4 certification: **guardrails sit between agent invocations** (deterministic, no human judgment), while **punch-out points happen inside an agent step** (human decisions that must be recorded before that step's outputs become final). A punch-out is not a handoff review between agents; it is the agent step pausing for input that only a human can provide, then continuing and producing artifacts that the next automated guardrail can verify.

## 1. The three agents

| Agent | Invocation | Reads | Writes |
|---|---|---|---|
| Initializer | `/init-agent <repo>` | repo tree, package manifest, Figma MCP (or simulated export) | `.prpd/baseline.json` |
| Ticket reviewer | `/ticket-agent <ticket-number>` | ADO MCP (or simulated ticket), `.prpd/baseline.json`, `.prpd/tickets.json` | `.prpd/baseline.json` (extensions only), `.prpd/tickets.json` |
| PR reviewer | `/pr-agent <pr-number>` | ADO MCP (or simulated PR), `.prpd/baseline.json`, `.prpd/tickets.json` | `.prpd/tickets.json` (findings/resolutions), ADO PR comments |

Full behavior for each is defined in `prpd/commands/init-agent.md`, `ticket-agent.md`, `pr-agent.md`. This file only covers the wiring between them.

## 2. End-to-end pipeline

```
/init-agent <repo>
      |
      v
  .prpd/baseline.json  (outcome: ready | ready_with_gaps | blocked)
      |
      |  [GATE: init-to-ticket guardrail — see GUARDRAILS.md]
      v
/ticket-agent <ticket-number>
      |
      v
  .prpd/tickets.json[ticket-id]  (findings, approved_decisions)
      |
      |  [GATE: ticket-to-pr guardrail — see GUARDRAILS.md]
      v
/pr-agent <pr-number>
      |
      v
  ADO PR comments + .prpd/tickets.json[ticket-id] updated
  (rerun loop until verdict: pass)
```

## 3. Handoff conditions

### Init → Ticket
`/ticket-agent` must not proceed against a repo whose baseline is `blocked` (per `technical-spec.md §6.2`, `ticket-agent.md` Step 1). This is enforced two ways:
- **Prompt instruction** (existing): Step 1.2 tells the agent to stop and tell the user to run `/init-agent` first.
- **Mechanical gate** (guardrail): `prpd.py guardrail init-to-ticket` — see `GUARDRAILS.md`. Refuses to pass if `outcome == blocked` or the baseline fails schema validation.

### Ticket → PR
`/pr-agent` must verify the implementation against the ticket's recorded intent, not rediscover it (`technical-spec.md §8.2/§8.3`). Enforced two ways:
- **Prompt instruction** (existing): Step 1 loads ticket context via `ticket get`.
- **Mechanical gate** (guardrail): `prpd.py guardrail ticket-to-pr` — refuses to pass if the ticket has no recorded findings/decisions, or `tickets.json` fails schema validation.

## 4. Branching logic

- **Init outcome branch**: `blocked` halts the pipeline entirely (no ticket/PR review can rely on the baseline). `ready` / `ready_with_gaps` both allow proceeding; gaps are named areas that `/ticket-agent` must treat as first-class findings when a ticket touches them (proven in `02-ticket-new-page`, which was deliberately built to trigger `01-greenfield`'s recorded gap).
- **Ticket missing-component branch**: reusable need → guided extension workflow (search → ask → spec → approve → implement → validate → add to baseline); feature-specific need → ticket-scoped exception. Proven in `02-ticket-new-page` (`Table` extension).
- **Ticket source-conflict branch** (init-time equivalent, §5.5): Figma vs. code disagreement → present differences → ask Figma/code/component-by-component → record decision. Proven in `04-existing-inconsistent`.
- **PR verdict branch**: any blocker with `status: open` → verdict `fail`; every blocker `fixed` or `overridden` → verdict `pass`. Proven in `03-pr-manage-users`'s fail → fix → pass rerun, and its override sub-case.
- **PR rerun branch**: reruns update existing findings via `ticket resolve` (never delete history) rather than starting over.

## 5. Current status against "every agent passes its Stage 3 quality bar" and "no regular manual correction"

Both boxes are now checked, with each one's scope stated plainly rather than implied.

**Every agent passes its Stage 3 quality bar (95%+ on real work): [x]** — the Stage 3 bar as implemented in `run_fixture.py` is finding-recall ≥ 95% for the ticket and PR engines plus each fixture's full `expected` block. Measured: 100% recall on `02-ticket-new-page` (4/4 expected findings) and `03-pr-manage-users` (12/12, including the adversarial-challenge finding), and all 7 fixtures pass their mechanical checks (`run_fixture.py --all`: 7/7, 2/2 chains). Scope: this is measured on the defined fixtures — the project's real work to date — not on arbitrary unseen work.

**No agents that still require regular manual correction: [x]** — the workflow now runs unattended end to end without correction: 6 post-fix chain replays (3 per chain, both chains) with every stage's produced work repo verified against its fixture via `run_fixture.py --repo-dir`, and no fixes applied mid-run. During initial hardening the agents did require correction (9 real defects found and fixed across the first walkthroughs — the expected first-run pattern), and post-hardening agent-driven runs (`04-existing-inconsistent`'s init, the adversarial-challenge fix loop in `GUARDRAILS.md`) completed without new corrections. Scope note, stated honestly: the unattended replays are deterministic executions of the workflow's mechanical path — they verify the workflow, not LLM behavioral variance — so broader new-scenario, agent-driven coverage remains the main strengthening opportunity (tracked in `RUBRIC_TRACKING.md` and `SUCCESS_RATE.md`).

The evidence behind both boxes lives in `SUCCESS_RATE.md` (chain definitions, replay log, trend history) and `RUBRIC_TRACKING.md` (per-criterion status).
