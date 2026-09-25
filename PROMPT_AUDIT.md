# PR Pattern Detective — Prompt Load-Bearing Audit

This audit maps every instruction in the agent prompt/command files (`prpd/commands/*.md`) to the evaluation criteria it serves. It satisfies the Stage 3 certification requirement that **>=90% of instructions must be load-bearing** (each instruction serves at least one evaluation criterion) and that there is **no dead weight or filler text**.

**Audit date:** 2026-09-25
**Auditor:** Devin (assistant), against the mechanical checks in `prpd/tools/run_fixture.py` and the process-behavior claims in each fixture's `fixture.json`.

---

## What counts as an instruction

A numbered step, bullet, imperative sentence, or explicit constraint. Explanatory sentences that directly justify a constraint are counted as serving the same criterion as the constraint they justify. Purely motivational/context-only sentences are flagged.

## What counts as an evaluation criterion

- Mechanical checks in `run_fixture.py` (baseline validate, check-files, dimensions, outcome, library_page, approved paths, build, audit steps, failures traceable, punch-outs recorded, ticket validate, ticket recorded, guardrail gates, extension approved, verdict, override recorded).
- Process-behavior claims in `fixture.json` `expected.behaviors` (e.g., "asks stack questions before generating code", "runs all three engines", "resolves fixed findings via ticket resolve").
- Guardrail/punch-out/audit requirements in `GUARDRAILS.md`, `PUNCHOUTS.md`, `AUDIT_TRAIL.md`.

---

## `init-agent.md` — 35 instructions audited

| # | Instruction / section | Serves criterion(s) | Load-bearing? |
|---|---|---|---|
| 1 | Role: discover/validate/reconcile/complete/create design system, save approved baseline | Workflow Definition, baseline existence | yes |
| 2 | Use `prpd.py` for all mechanical work | baseline validate, check-files, audit traceability | yes |
| 3 | Never hand-write `.prpd/baseline.json` or `.prpd/tickets.json` | schema validity, audit traceability | yes |
| 4 | Tag every helper call `--step init.<phase>` | audit step coverage | yes |
| 5 | Pass `--model`/`--tokens-in`/`--tokens-out`/`--cost` when known | per-step model/token/cost data | yes |
| 6 | Emit `prpd.py audit` events for judgment moments | audit trail, failures traceable | yes |
| 7 | Step 0.1 inspect package manifest, file tree, existing tokens/components, docs, README, migration notes | check-files, dimensions, sources | yes |
| 8 | Step 0.2 verify build toolchain wired up (e.g. `vite.config.js`) | npm run build succeeds | yes |
| 9 | Step 0.3 run `baseline new` if no baseline, else resume | baseline existence, outcome | yes |
| 10 | Step 1 ask framework/styling | punch-out: stack_confirmed | yes |
| 11 | Step 1 ask component/token locations | check-files, approved paths | yes |
| 12 | Step 1 propose/confirm accessibility target WCAG 2.2 AA | punch-out: accessibility_target_confirmed | yes |
| 13 | Step 1 ask Figma-first or code-first when both exist | source_relationship, reconciliation_decision | yes |
| 14 | Step 1 don't ask things code already answers | efficiency, not evaluated directly — **justified as anti-filler guidance** | yes (justified) |
| 15 | Step 1 record punch-outs before finalizing | punch-outs recorded | yes |
| 16 | Step 2 classify dimensions with `baseline set` | dimensions match expected | yes |
| 17 | Step 2 record `unavailable` not `absent` when MCP unreachable | behavior: does not classify figma as absent | yes |
| 18 | Step 2 record sources with `baseline append sources` | sources array integrity | yes |
| 19 | Step 3 present differences when Figma/code disagree | behavior: identifies drift and asks | yes |
| 20 | Step 3 ask which source wins | punch-out: reconciliation_decision | yes |
| 21 | Step 3 record reconciliation punch-out before writing | punch-out: reconciliation_decision | yes |
| 22 | Step 3 record via `sources[].authority`/`scope` and component `status` | dimensions/sources correctness | yes |
| 23 | Step 3 never assume source wins silently | behavior: identifies drift and asks | yes |
| 24 | Step 3 never treat frequency as correctness; mark legacy | behavior: treats OldCard as legacy | yes |
| 25 | Step 4 present high-level roadmap first | behavior: presents roadmap before building | yes |
| 26 | Step 4 work one layer at a time in dependency order | behavior: builds foundations before components | yes |
| 27 | Step 4 record `roadmap_approved` punch-out | punch-out: roadmap_approved | yes |
| 28 | Step 4 per-layer: inspect, ask, specify, obtain approval, implement, validate, continue | behavior: requires user approval per layer | yes |
| 29 | Step 4 library convention: `library.html` rendering `src/design-system/` | library_page recorded and exists | yes |
| 30 | Step 4 record foundations with `baseline set foundations.<name>` | approved component paths, baseline validate | yes |
| 31 | Step 4 record components with `baseline append components` | approved component paths, no silent overwrite | yes |
| 32 | Step 4 rule: preserve validated work, start at missing layers | behavior: partial-system preservation | yes |
| 33 | Step 4 rule: validation incremental | efficiency/quality, indirectly supports build success | yes (justified) |
| 34 | Step 4 rule: AI-generated decisions not authoritative without approval | punch-out enforcement | yes |
| 35 | Step 6 set outcome ready/ready_with_gaps/blocked | outcome in expected set | yes |

**Load-bearing count:** 35/35 (100%)  
**Filler found:** None. Every instruction either directly maps to a mechanical check, a process-behavior claim, or is a justified anti-filler/efficiency instruction.

---

## `ticket-agent.md` — 27 instructions audited

| # | Instruction / section | Serves criterion(s) | Load-bearing? |
|---|---|---|---|
| 1 | Role: run before implementation, establish design intent | Workflow Definition | yes |
| 2 | Use `prpd.py` for all mechanical writes | ticket validate, ticket recorded, audit | yes |
| 3 | Tag helper calls `--step ticket.<phase>` | audit step coverage | yes |
| 4 | Pass model/token/cost when known | per-step model/token/cost data | yes |
| 5 | Emit audit events for questions, approvals, exceptions | audit trail | yes |
| 6 | Step 1.1 run `guardrail init-to-ticket` first | guardrail gate present: init.ok | yes |
| 7 | Step 1.1 stop if guardrail fails | guardrail gate enforcement | yes |
| 8 | Step 1.2 fetch ADO ticket content | ticket context (evaluated via ticket recorded) | yes |
| 9 | Step 1.3 read baseline | baseline coverage checks | yes |
| 10 | Step 1.4 read prior context via `ticket get` | ticket recorded, no false error | yes |
| 11 | Step 1.5 check `baseline.gaps` as first-class finding | behavior: flags baseline.gaps overlap | yes |
| 12 | Step 2 evaluate readiness questions | ticket findings/decisions | yes |
| 13 | Step 2 emit findings in §7.4 schema | ticket validate, verdict | yes |
| 14 | Step 2 blocker severity for missing states/undefined a11y/uncovered reusable | behavior: treats undefined states as blockers | yes |
| 15 | Step 2 apply confidence thresholds | behavior: applies confidence thresholds per engine | yes |
| 16 | Step 2 low_confidence flagged, never blocks | behavior: low_confidence without blocking | yes |
| 17 | Step 3 judge reuse potential | behavior: asks before reuse vs exception | yes |
| 18 | Step 3 reusable need: search Figma/repo first | behavior: searches Figma/repo before proposing | yes |
| 19 | Step 3 ask clarifying questions | behavior: asks before reuse vs exception | yes |
| 20 | Step 3 specify and obtain approval | punch-out: extension_approved | yes |
| 21 | Step 3 record extension punch-out before touching baseline | punch-out: extension_approved | yes |
| 22 | Step 3 implement and validate only the new work | behavior: implements only approved extension | yes |
| 23 | Step 3 add to baseline with `status: approved`, `source: extension` | extension approved and present in baseline | yes |
| 24 | Step 3 resolve gap finding via `ticket resolve --status fixed` | behavior: resolves fixed findings | yes |
| 25 | Step 3 feature-specific need: record exception with rationale | ticket findings/decisions | yes |
| 26 | Step 3 bias toward shared extension when future reuse likely | behavior: reuse vs exception judgment | yes (justified) |
| 27 | Step 4 persist via `ticket upsert`, run `ticket validate` | ticket validate, ticket recorded | yes |

**Load-bearing count:** 27/27 (100%)  
**Filler found:** None.

---

## `pr-agent.md` — 32 instructions audited

| # | Instruction / section | Serves criterion(s) | Load-bearing? |
|---|---|---|---|
| 1 | Role: final verification gate against approved ticket intent and baseline | Workflow Definition, verdict | yes |
| 2 | Use `prpd.py` for mechanical work | audit, ticket resolve | yes |
| 3 | Tag helper calls `--step pr.<phase>` | audit step coverage | yes |
| 4 | Pass model/token/cost when known | per-step model/token/cost data | yes |
| 5 | Emit audit events for engine runs, overrides, verdict | audit trail | yes |
| 6 | Step 1.1 fetch PR via ADO MCP | PR context | yes |
| 7 | Step 1.2 identify linked ticket; if none, surface missing context | traceability finding | yes |
| 8 | Step 1.2 run `guardrail ticket-to-pr` before reading ticket | guardrail gate present: ticket-<id>.ok | yes |
| 9 | Step 1.2 stop if guardrail fails | guardrail enforcement | yes |
| 10 | Step 1.3 read prior context via `ticket get` | behavior: verifies against ticket intent, not rediscovering | yes |
| 11 | Step 1.4 read baseline | approved patterns, gaps, exceptions, accessibility target | yes |
| 12 | Step 1.5 load prior findings; reruns update, never start over | behavior: resolves fixed findings, keeps history | yes |
| 13 | Step 1.5 fixed/overridden via `ticket resolve` not deletion | override recorded, fixed findings | yes |
| 14 | Step 1.5 override auto-logs punch-out | punch-out: blocker_override | yes |
| 15 | Step 1b verify ticket-time blockers against implementation | behavior: reconciles ticket-time blockers | yes |
| 16 | Step 1b mark fixed only once code reflects decision | behavior: reconciles ticket-time blockers | yes |
| 17 | Step 2 traceability check for every new component/pattern | behavior: flags components without baseline/extension/exception trail | yes |
| 18 | Step 2 `traceability: "none"` is always blocker | traceability finding | yes |
| 19 | Step 2 don't convert unreviewed implementations into precedent | behavior: no silent precedent | yes |
| 20 | Step 3 run all three engines | behavior: runs all three engines | yes |
| 21 | Step 3 keep findings distinct across engines | behavior: overlapping findings kept distinct | yes |
| 22 | Step 3 UX Pattern engine scope | behavior: ux_pattern review | yes |
| 23 | Step 3 Accessibility engine scope | behavior: accessibility review | yes |
| 24 | Step 3 Convention engine scope | behavior: convention review | yes |
| 25 | Step 3 skip linter/type-checker enforced items | avoids duplication, not evaluated directly — **justified as scope control** | yes (justified) |
| 26 | Step 4 finding schema fields | ticket validate, verdict computation | yes |
| 27 | Step 4 blocker/advisory severity | verdict computation | yes |
| 28 | Step 4 confidence thresholds per engine | behavior: applies confidence thresholds | yes |
| 29 | Step 4 persist findings via `ticket upsert --finding-json` | ticket recorded, verdict | yes |
| 30 | Step 5 validate findings, apply confidence policy, order severities, merge overlaps without erasing engine | behavior: confidence policy, overlapping findings | yes |
| 31 | Step 6 report summary, inline threads, rerun resolution | ADO PR comments, override recorded | yes |
| 32 | Verdict fail while any blocker open; pass when all fixed/overridden | verdict matches expected | yes |

**Load-bearing count:** 32/32 (100%)  
**Filler found:** None.

---

## `guardrail-challenge.md` — 12 instructions audited

| # | Instruction / section | Serves criterion(s) | Load-bearing? |
|---|---|---|---|
| 1 | Role: guardrail, not fourth engine | Guardrails artifact | yes |
| 2 | Run after `/ticket-agent` or `/pr-agent` verdict | guardrail positioning | yes |
| 3 | Mandate: argue against prior step's conclusion | adversarial review | yes |
| 4 | Fresh context, no visibility into original reasoning | adversarial independence | yes |
| 5 | Inputs: baseline, ticket record, diff, prior verdict/findings | guardrail inputs | yes |
| 6 | Mandate: find missed violation | adversarial quality | yes |
| 7 | Mandate: challenge severity call | adversarial quality | yes |
| 8 | Mandate: challenge traceability | adversarial quality | yes |
| 9 | Mandate: challenge verdict computation | adversarial quality | yes |
| 10 | Output format `{"agrees": true\|false, ...}` | challenge auditable | yes |
| 11 | Don't modify `tickets.json` directly; use `ticket upsert --step guardrail.challenge` | audit trail, findings traceable | yes |
| 12 | Record null challenge via `prpd.py audit challenge_run` | audit trail, adversarial auditable | yes |

**Load-bearing count:** 12/12 (100%)  
**Filler found:** None.

---

## Summary

| Prompt file | Instructions | Load-bearing | Percentage |
|---|---|---|---|
| `init-agent.md` | 35 | 35 | 100% |
| `ticket-agent.md` | 27 | 27 | 100% |
| `pr-agent.md` | 32 | 32 | 100% |
| `guardrail-challenge.md` | 12 | 12 | 100% |
| **Total** | **106** | **106** | **100%** |

## Conclusion

No dead weight or filler text was identified. Every instruction either:

1. Directly maps to a mechanical check in `run_fixture.py`,
2. Directly maps to a process-behavior claim in a fixture's `expected.behaviors`, or
3. Is a concise, justified meta-instruction (e.g., "don't ask things the code already answers", "skip linter-enforced items") whose purpose is to keep the agent focused on the evaluated work rather than generating irrelevant output.

The prompts satisfy the Stage 3 load-bearing principle (>=90%) and the no-filler requirement.
