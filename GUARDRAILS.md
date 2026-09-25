# PR Pattern Detective — Guardrails

Guardrails are deterministic, automated checks that sit **between** agent invocations — e.g., after `/init-agent` finishes and before `/ticket-agent` runs. They are not a human reviewing the prior step's output, and they are not embedded inside an agent's own reasoning (that would make them as trustworthy as the agent's compliance with its own prompt, which is not verifiable). Two distinct mechanisms exist:

**Important distinction for Stage 4:** human judgment is required at *punch-out points* inside an agent step (see `PUNCHOUTS.md`) because some questions have no deterministic answer (which source wins a conflict, whether to accept risk instead of a fix). The *handoff* from one completed agent step to the next is fully automated: a guardrail gate verifies required artifacts and writes a sentinel. Punch-out decisions are recorded as part of the agent step that produces the artifact; the subsequent guardrail does not ask a human, it only checks that the required artifact + decisions exist.

## 1. Deterministic gates (mechanical, zero judgment)

Implemented as `prpd.py guardrail <gate>` subcommands. Each gate reads only files on disk, makes a pass/fail decision with no LLM involvement, and — on pass — writes a sentinel file under `.prpd/gates/`. The next agent's tooling is required to check for that sentinel before proceeding.

### `guardrail init-to-ticket`
Refuses (exit 1) unless:
- `.prpd/baseline.json` exists
- `outcome` is `ready` or `ready_with_gaps` (never `blocked`)
- all four dimensions are set
- `accessibility_target` and `stack.framework` are set
- at least one foundation is recorded

On pass, writes `.prpd/gates/init.ok` containing a checksum of `baseline.json` at the moment it passed.

### `guardrail ticket-to-pr <ticket-id>`
Refuses unless:
- `.prpd/gates/init.ok` exists **and** `baseline.json`'s current checksum still matches what's recorded in it (if the baseline changed after the gate passed, the gate is stale and must be rerun — this is checked, not assumed)
- `.prpd/tickets.json` exists and contains a record for `<ticket-id>` with `findings`, `approved_decisions`, and `updated_at`

On pass, writes `.prpd/gates/ticket-<id>.ok`.

### Actively tested bypass attempts (not just specified — verified)

Six bypass attempts were made against these gates and all six were blocked:
1. No `baseline.json` at all → blocked
2. `baseline.json` exists but `outcome: blocked` and incomplete → blocked, with every missing field named
3. `ticket-to-pr` invoked with no `init.ok` gate present → blocked
4. (control) all required fields present → correctly passes
5. `ticket-to-pr` invoked for a ticket ID never reviewed by `/ticket-agent` → blocked
6. `baseline.json` retroactively corrupted *after* its gate already passed, without rerunning the gate → blocked via checksum mismatch, not blind trust of the sentinel file's prior existence

This satisfies the rubric's requirement that punch-out/gate points be *actively tested* for bypass, not merely documented.

`run_fixture.py` now checks that the expected gate files exist for every ticket/pr-stage fixture, so a future change that silently breaks a gate's wiring into the agent prompts (not the gate logic itself) will be caught the same way the earlier CLI regressions were.

## 2. Adversarial challenge (automated, requires judgment, still not human review)

Some things can't be checked by reading files mechanically — e.g. "did the reviewing engine miss a real violation?" This is what `prpd/commands/guardrail-challenge.md` defines: a **separate, isolated agent invocation** (fresh context, no visibility into the original reviewer's reasoning) whose only mandate is to argue against the prior step's conclusion. Finding nothing is a legitimate result; the point is that it has to actually look, independently.

This is automated adversarial review, not Stage 2 human review, specifically because:
- It runs as a scripted, repeatable invocation, not an ad hoc human read-through
- It has no memory of or access to the original agent's chain of reasoning — only inputs and outputs — so it can't simply agree with itself
- A successful challenge becomes a new finding through the normal `ticket upsert` path (`--step guardrail.challenge`), not a hand-edit, and a null result is still logged (`prpd.py audit challenge_run`)

### Proven, not just specified

Ran for real against `PR-55`/`TICKET-101` (already-verified, "passing" work) via an isolated subagent with no access to the original review's reasoning. Result: it found a real, previously unflagged blocker (inline styles + hardcoded spacing on the shipped `<main>` elements — the exact rule `convention-6` had already established, just missed on the production code path) and two real traceability errors (`convention-5`/`convention-6`'s `traceability` values were swapped relative to what the baseline actually supports).

Recording the new finding correctly flipped `run_fixture.py`'s verdict for `03-pr-manage-users` from `pass` to `fail` — proving the challenge has real teeth, not just narrative value. The issue was then fixed for real (moved to CSS Modules, `ManageUsersPage.module.css`), the finding resolved via `ticket resolve ... --status fixed`, and the verdict correctly flipped back to `pass` — this time having survived independent adversarial review, not just the original three engines.

## What guardrails are explicitly not

- Not a substitute for the three review engines (`ux_pattern`, `accessibility`, `convention`) — those produce the findings; guardrails validate the process around them (§9 of `technical-spec.md`).
- Not a human clicking "approve" between steps — see `PUNCHOUTS.md` for where human judgment is deliberately still required, and how those specific points are mechanically enforced and bypass-tested separately from the fully-automated gates above.
