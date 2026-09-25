# PR Pattern Detective — Iteration Log

This log records the evolution of the prompts, evaluation criteria, and measured results across the project. It satisfies the Stage 3 certification requirement for an iteration log showing prompt evolution with baseline scores, hypotheses, changes, measured results, and reasoning.

**Log format (one entry per iteration):**
- Iteration number and date
- Scope: what part of the system changed
- Hypothesis: what we expected to find or prove
- Changes made: concrete edits to prompts, code, or fixtures
- Baseline scores / measured results: pass/fail or counts before and after
- Reasoning: why the change was the right response to the result

---

## Iteration 0 — Initial three-agent spec and greenfield init fixture

**Date:** 2026-09-22 (earlier session)  
**Scope:** Establish the three-agent model (`/init-agent`, `/ticket-agent`, `/pr-agent`) and walk through the first fixture.

### Hypothesis
If the initializer is given a greenfield repo with no existing design system, it can ask the right questions, record an approved baseline, generate a working design system, and leave the repo buildable and documented.

### Changes made
- Wrote `prpd/commands/init-agent.md`, `ticket-agent.md`, `pr-agent.md`.
- Built `prpd/tools/prpd.py` helper to mechanically read/write `.prpd/baseline.json` and `.prpd/tickets.json`.
- Created `prpd/fixtures/01-greenfield` with a minimal Vite + React repo and `fixture.json`.
- Added `prpd/tools/run_fixture.py` to validate fixture state against expectations.

### Measured results
- First run: **FAIL** — the fixture did not reach its expected state.
- Defects found and fixed:
  1. CLI flag ordering in `prpd.py` made `--repo-dir` fail when placed after positional arguments.
  2. `baseline append` for arrays was missing; every array write had to be a full replacement.
  3. Vite plugin wiring was missing in `vite.config.js` despite the dependency being present.
- After fixes: **PASS** — fixture met all expected checks.

### Reasoning
A greenfield case is the easiest possible init scenario. If the simplest path fails, more complex paths cannot be trusted. Fixing these three structural defects before adding features prevented them from being repeated in every later fixture.

---

## Iteration 1 — Ticket review workflow

**Date:** 2026-09-24 (earlier session)  
**Scope:** Add a ticket-time review stage that extends the baseline when a ticket needs a missing reusable component (`Table`).

### Hypothesis
A ticket that needs a component not yet in the baseline should pause, ask whether the component is reusable, run a guided extension workflow, and record the extension so `/pr-agent` can verify it later.

### Changes made
- Extended `ticket-agent.md` with the reuse-vs-exception decision and extension workflow.
- Created `prpd/fixtures/02-ticket-new-page` on top of `01-greenfield`.
- Added a `Table` component extension and updated the baseline/library page.
- Extended `run_fixture.py` to score the `ticket` stage.

### Measured results
- First run: **FAIL** — `ticket get` exited non-zero when no prior context existed, treating a normal first review as an error.
- Defects found and fixed:
  1. `ticket get` now returns empty context with exit 0 instead of failing.
  2. Added missing `ticket validate` command so ticket records can be sanity-checked before PR review.
- After fixes: **PASS**.

### Reasoning
A first ticket review naturally has no prior context; treating that as an error would block every new ticket. The fix made the workflow robust for the normal case rather than only the rerun case.

---

## Iteration 2 — PR review workflow and finding lifecycle

**Date:** 2026-09-24 (earlier session)  
**Scope:** Run `/pr-agent` against a PR and prove the fail → fix → pass loop, including overrides.

### Hypothesis
The PR agent can detect traceability, accessibility, and convention violations against the baseline, report them, and re-run after fixes until the verdict is `pass`.

### Changes made
- Extended `pr-agent.md` with the three engines and finding schema.
- Created `prpd/fixtures/03-pr-manage-users` with deliberate and organic violations.
- Extended `run_fixture.py` to score the `pr` stage.
- Added `ticket resolve` command to `prpd.py` so findings can be marked `fixed` or `overridden`.
- Added the override flow test: one blocker accepted with recorded reason.

### Measured results
- First run: **FAIL** — correctly caught planted violations.
- Additional organic findings: an unreachable empty state and a reintroduced contrast failure from hardcoded colors.
- Correctness fix: engine attribution on one finding was wrong.
- Major gap closed: there was no way to mark a finding "fixed," so reruns would have kept failing forever. `ticket resolve` added with status lifecycle.
- Override flow: after recording an override, verdict correctly returned to **PASS**.

### Reasoning
The finding lifecycle is as important as the finding detection. Without a way to resolve findings, the system could only ever report problems, never confirm they were addressed. The override flow ensures human risk acceptance is recorded, not silently ignored.

---

## Iteration 3 — Existing-repo init reconciliation

**Date:** 2026-09-25  
**Scope:** Test `/init-agent` on a messier repo with drifted sources and legacy code.

### Hypothesis
The dimension model and conflict-resolution logic in §5.5 can handle a repo that is not greenfield: partial coded system, drifted Figma, legacy duplicate components, and unclear authority.

### Changes made
- Created `prpd/fixtures/04-existing-inconsistent` with an existing React repo, a simulated Figma export (`figma-export.json`), and duplicate `Card` implementations (`Card.jsx` and `OldCard.jsx`).
- Walked through component-by-component reconciliation: Figma won for color and Button; code won for aligned Card; `OldCard` marked legacy; Badge built from Figma spec.

### Measured results
- Classification landed on real non-default values: `figma: partial`, `coded_system: partial`, `source_relationship: drifted`, `maturity: existing_inconsistent`.
- After reconciliation and rebuild: **PASS**.
- Zero new tool bugs found — evidence that Iterations 0–2 fixes were structural, not scenario-specific.

### Reasoning
Greenfield success does not prove the dimension model works. This fixture forced the conflict-resolution path to run for the first time and confirmed that frequency is not precedent (`OldCard` had more usage but was still legacy).

---

## Iteration 4 — Certification hardening: guardrails, punch-outs, success rate, audit trail

**Date:** 2026-09-25  
**Scope:** Close the five Stage 4 certification artifacts and the underlying Stage 3 evaluation/log requirements.

### Hypothesis
The system has real behavior but lacks the artifacts an external examiner can read and verify. Adding deterministic between-step gates, mechanical punch-out enforcement, chain-based success-rate measurement, and step-traced audit records will make the workflow defensible.

### Changes made
- Added `prpd.py guardrail init-to-ticket` and `guardrail ticket-to-pr` with sentinel files and checksums.
- Added `prpd/commands/guardrail-challenge.md` and ran a real adversarial review against `PR-55`.
- Added `punchout record` and mechanical enforcement on `baseline set outcome` and `baseline append components`.
- Added `SUCCESS_RATE.md`, `chains.json`, and `--report` mode in `run_fixture.py`.
- Made `--step` mandatory for all mutating commands in `prpd.py`.
- Added `prpd/tools/trace_failure.py` and demonstrated a real untraceable historical failure next to a traceable one.
- Updated `WORKFLOW.md`, `GUARDRAILS.md`, `PUNCHOUTS.md`, `AUDIT_TRAIL.md`, `RUBRIC_TRACKING.md`.

### Measured results
- Before hardening: no gate files, no punch-out ledger, no chain-based rate, audit entries with `step: null`.
- After hardening:
  - 6 guardrail bypass attempts: **all blocked**.
  - 4 punch-out bypass attempts: **all blocked**.
  - Adversarial review found a real missed blocker and two traceability errors; verdict correctly flipped **pass → fail → pass** after fixing.
  - End-to-end success rate: **1/1 chain passing (100%)** — caveated as a single-chain sample.
  - `trace_failure.py`: found 1 untraceable historical failure, 1 traceable failure.

### Reasoning
Documentation-only artifacts would fail the rubric's "actively tested" requirement. Every mechanism was attacked to prove it actually refused bypass. The adversarial pass proved the challenge is not theater: it changed the verdict. The honest caveats in `SUCCESS_RATE.md` and `AUDIT_TRAIL.md` keep the project from overclaiming while still satisfying the artifact requirement.

---

## Summary of trend

| Iteration | Focus | Defects/gaps found | Result after fixes |
|---|---|---|---|
| 0 | Greenfield init | 3 | PASS |
| 1 | Ticket review | 2 | PASS |
| 2 | PR review + lifecycle | 2 bugs + 1 correctness fix + 1 major lifecycle gap | PASS |
| 3 | Existing-repo reconciliation | 0 (structural fixes held) | PASS |
| 4 | Certification artifacts | Guardrails, punch-outs, rate, audit all verified | PASS |

All four fixtures currently pass together via `python3 prpd/tools/run_fixture.py --all`. The next iteration should address the remaining gaps in `RUBRIC_TRACKING.md`: load-bearing prompt audit, mid-tier model verification, repeated-trial success-rate data, hard-gating the remaining two punch-out points, and an API-driven execution wrapper for real token/cost data.
