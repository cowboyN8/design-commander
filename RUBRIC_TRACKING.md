# PR Pattern Detective — Certification Rubric Tracking

This file tracks the project against both the **Stage 3** and **Stage 4** certification requirements shown in the rubric images. It is a living checklist: update it as gaps close or new ones are discovered.

**Last updated:** 2026-09-25
**Current assessment:**
- **Stage 3:** Prompt files exist, evaluation script exists, but load-bearing audit, mid-tier model verification, and a dedicated iteration log are missing or incomplete.
- **Stage 4:** All 5 required artifacts exist; 3 are partially complete, 2 are functionally complete but still growing evidence.

---

## Legend

| Symbol | Meaning |
|---|---|
| ✅ | Done — real mechanism exists and has been verified |
| 🟡 | Partial — artifact exists, specific sub-requirement still open |
| ❌ | Not done — no meaningful implementation or evidence yet |
| 🔄 | In progress — currently being worked |

---

# Stage 3 Certification: The Prompt, The Evaluations, The Log

## Stage 3 — The Prompt

| Requirement | Status | Evidence / Location | Open Gap |
|---|---|---|---|
| Markdown file containing the practitioner's prompt or command | ✅ | `prpd/commands/init-agent.md`, `prpd/commands/ticket-agent.md`, `prpd/commands/pr-agent.md`, `prpd/commands/guardrail-challenge.md` | None |
| Follows structured prompting (RTCC or similar) | 🟡 | Prompts use role, task, context, constraints, step numbering, tool-call conventions, and explicit output schemas | No formal RTCC audit performed; structure is present but not labeled against a standard |
| Demonstrates deliberate instruction design | ✅ | Each prompt is purpose-built for its stage and references the mechanical helper, schema, and confidence thresholds | None |
| Load-Bearing Principle: ≥90% of instructions must be load-bearing | ❌ | Not measured | Audit each prompt line against the evaluation criteria in `run_fixture.py` / `fixture.json`; remove or justify any instruction that does not serve an evaluation |
| No dead weight or filler text | 🟡 | Prompts are concise but have not been audited for filler | Same load-bearing audit will surface filler |

**Stage 3 Prompt verdict:** Prompts exist and are well-structured ✅, but the quantitative load-bearing audit has not been performed ❌.

---

## Stage 3 — The Evaluations

| Requirement | Status | Evidence / Location | Open Gap |
|---|---|---|---|
| Scripts, Promptfoo YAML configs, or documented test cases | ✅ | `prpd/tools/run_fixture.py` plus per-fixture `fixture.json` expected blocks | None |
| ≥3 distinct evaluation criteria (not variations of the same check) | ✅ | baseline validity, file existence, build success, audit well-formedness, ticket findings/decisions/overrides, PR verdict, guardrail gate files, punch-out records, traceability — all distinct | None |
| Substantive quality checks, not window dressing | ✅ | Checks validate real invariants (contrast ratios, component reuse, required build outputs, gate checksums, traceable failures) | None |
| Capable of producing 95%+ scores when the prompt performs well | 🟡 | Current fixture pass rate is 4/4 (100%) on hardened artifacts | Rate is on a single pass of 4 fixtures, not repeated prompt runs; needs repeated trials on the same scenarios |
| Runs on mid-tier models or lower (Sonnet, GPT-4) — no frontier model requirement | ❌ | All work done via Devin/Adaptive routing layer | Verify `prpd.py` + prompts run correctly on an explicit Sonnet/GPT-4 backend; document results |
| Clear pass/fail thresholds or scoring rubrics | ✅ | `run_fixture.py` returns 0/1 per fixture and per chain; `fixture.json` has `expected` block with explicit criteria | None |

**Stage 3 Evaluations verdict:** Evaluation script and criteria are real ✅, but repeated-trial rate and mid-tier model verification are missing ❌.

---

## Stage 3 — The Log

| Requirement | Status | Evidence / Location | Open Gap |
|---|---|---|---|
| An iteration log showing evidence of prompt evolution | 🟡 | `case-study.md` narrates evolution chronologically | No dedicated iteration log in the exact rubric format with per-iteration scores, hypothesis, change, measured results, reasoning |
| ≥2 documented iterations minimum | ✅ | `case-study.md` contains far more than 2 development phases | None, once format is corrected |
| Each iteration includes: baseline scores, hypothesis, change made, measured results, and reasoning | ❌ | `case-study.md` has reasoning and changes, but not explicit baseline scores per iteration | Create `ITERATION_LOG.md` with one entry per major phase, including the required fields |
| Evidence of EDD discipline (Red/Green/Refactor cycle) | ✅ | Many examples: tests/checks written first, failing, then fixed (guardrail bypass tests, fixture discrimination, traceability enforcement) | None, once documented in iteration format |
| Chronological progression with cause-and-effect | ✅ | `case-study.md` is chronological and explains why each change followed from prior evidence | None, once documented in iteration format |

**Stage 3 Log verdict:** The *content* of an iteration log exists across `case-study.md` and commit history ✅, but it is not assembled into a single artifact matching the rubric's required fields ❌.

---

# Stage 4 Certification: Five Required Artifacts

## 1. Workflow Definition

| Requirement | Status | Evidence / Location | Open Gap |
|---|---|---|---|
| Single canonical artifact describing the wired end-to-end pipeline | ✅ | `WORKFLOW.md` | None |
| Agent roles, inputs, and outputs documented | ✅ | `WORKFLOW.md` §1, `prpd/commands/init-agent.md`, `ticket-agent.md`, `pr-agent.md` | None |
| Handoff conditions between agents specified | ✅ | `WORKFLOW.md` §3 | None |
| Branching logic for `ready` / `ready_with_gaps` / `blocked`, extensions, overrides documented | ✅ | `WORKFLOW.md` §4 | None |
| Every agent passes its Stage 3 quality bar (95%+ on real work) | ❌ | No accuracy measurement exists | Build per-agent accuracy measurement; needs repeated trials |
| No agents that still require regular manual correction | ❌ | 9 real defects were found and fixed during hardening | Re-run fixtures repeatedly without fixes to prove correction rate has dropped |

**Artifact 1 verdict:** Documented and wired ✅, but the quality/self-sufficiency claims are explicitly *not* claimed as done in `WORKFLOW.md` §5.

---

## 2. Guardrails

| Requirement | Status | Evidence / Location | Open Gap |
|---|---|---|---|
| Automated, deterministic checks sit between agent steps | ✅ | `prpd.py guardrail init-to-ticket`, `guardrail ticket-to-pr` | None |
| Gate writes sentinel files; later agents can verify them | ✅ | `.prpd/gates/init.ok`, `.prpd/gates/ticket-<id>.ok` with checksums | None |
| Gates refuse invalid/missing handoff state | ✅ | 6 bypass attempts tested and blocked (see `GUARDRAILS.md`) | None |
| Must be automated — human review between steps is Stage 2, not Stage 4 | 🟡 | Mechanical gates are automated; punch-out points still require human judgment | Decide whether the product accepts a hybrid model or aims for fully automated handoffs |
| Adversarial challenge pass exists and is separate from normal review | ✅ | `prpd/commands/guardrail-challenge.md`; proven to flip a verdict from pass→fail→pass on `PR-55` | None |

**Artifact 2 verdict:** Core automated gates and adversarial challenge are real and tested ✅. The "no human review between steps" interpretation is not fully satisfied because punch-out points deliberately keep human judgment in the loop.

---

## 3. Punch-Out Evidence

| Requirement | Status | Evidence / Location | Open Gap |
|---|---|---|---|
| Explicit human decision points are identified | ✅ | `PUNCHOUTS.md` lists 6 point IDs | None |
| Refusal is enforced in code, not just in prompt text | ✅ | `prpd.py` `baseline set outcome` and `baseline append components` mechanically check `.prpd/punchouts.jsonl` | None |
| Punch-out ledger is append-only and inspectable | ✅ | `.prpd/punchouts.jsonl`, `punchout record`, `punchout log` | None |
| Punch-out points tested, not just documented | ✅ | 4 bypass attempts made; all blocked | None |
| Override decisions recorded with reason and actor | ✅ | `ticket resolve --status overridden --reasons "..." --by "..."` | None |
| Roadmap approval mechanically gated | ❌ | `roadmap_approved` is recorded but not enforced by code | Add hard gate in `prpd.py` before layer build steps |
| Reconciliation decision mechanically gated | ❌ | `reconciliation_decision` is recorded but not enforced by code | Add hard gate before any source-reconciliation output is written |
| Identity verification for `--by` field | ❌ | Free-text actor field | Accept for single-user local trust model; replace if multi-tenant |

**Artifact 3 verdict:** The critical "tested in code, not just on paper" requirement is satisfied ✅. Two specific punch-out points remain soft (documented honestly as known limitations in `PUNCHOUTS.md`).

---

## 4. End-to-End Success Rate

| Requirement | Status | Evidence / Location | Open Gap |
|---|---|---|---|
| Report exists showing the end-to-end success rate | ✅ | `SUCCESS_RATE.md` | None |
| Measures the full workflow, not per-step accuracy | ✅ | `prpd/fixtures/chains.json`; `run_fixture.py --all` scores chains, not fixture averages | None |
| Verdict changes when a real link breaks | ✅ | Demonstrated: corrupting `01-greenfield` dropped rate from 100% to 0% | None |
| Trend log append-only | ✅ | `prpd/fixtures/results.jsonl` | None |
| Statistical confidence from repeated independent trials | ❌ | Sample size = 1 chain | Run fixtures across separate sessions; accumulate trend entries |
| Measurement of agent success on new, unseen scenarios | ❌ | Fixtures measure hardened artifacts, not unattended fresh runs | Build API-driven unattended execution mode |

**Current number:** 1/1 end-to-end chains passing (100%) — honestly caveated as a single-chain sample.

**Artifact 4 verdict:** The mechanism is real and the current number is honestly reported ✅. The rubric's deeper implication (repeated, statistically meaningful, unattended success) is not yet satisfied.

---

## 5. Audit Trail

| Requirement | Status | Evidence / Location | Open Gap |
|---|---|---|---|
| Append-only structured log exists | ✅ | `.prpd/audit.jsonl` | None |
| Step coverage enforced for mutating commands | ✅ | `--step` required by argparse for all state-changing commands | None |
| Failure-to-origin-step trace example | ✅ | `prpd/tools/trace_failure.py` demonstrates real historical untraceable vs traceable failures | None |
| Trace tool exits non-zero on untraceable failures | ✅ | Can be wired into regression checks | None |
| Per-step model and token/cost data | ❌ | Schema fields exist but every value is null across all fixtures | Build API-driven wrapper that receives `usage` and passes it through |
| Automated wrapper populating cost data from API responses | ❌ | Architecture described but not implemented | Implement unattended execution mode |

**Artifact 5 verdict:** Traceability and step enforcement are real ✅. The model/token/cost requirement is explicitly *not* satisfied; the doc refuses to fabricate numbers.

---

# Combined Overall Tally

## Stage 3

| Artifact | Overall | Blockers to Close It |
|---|---|---|
| The Prompt | 🟡 | Load-bearing audit of every instruction; remove/justify filler |
| The Evaluations | 🟡 | Repeated-trial pass rate on same fixtures; mid-tier model verification |
| The Log | 🟡 | Create `ITERATION_LOG.md` in the required format with baseline scores per iteration |

## Stage 4

| Artifact | Overall | Blockers to Close It |
|---|---|---|
| Workflow Definition | 🟡 | Accuracy measurement; prove agents no longer need regular correction |
| Guardrails | 🟡 | Resolve whether hybrid human-automated handoffs satisfy Stage 4 |
| Punch-Out Evidence | 🟡 | Hard-gate `roadmap_approved` and `reconciliation_decision` |
| End-to-End Success Rate | 🟡 | Repeated trials; unattended-new-scenario measurement |
| Audit Trail | 🟡 | API-driven execution wrapper to populate model/token/cost |

---

## Honest Bottom Line

**Stage 3:** The raw material is present (prompts, evaluation script, commit history), but the presentation requirements — especially the load-bearing audit and the formatted iteration log — have not been assembled into artifacts that directly match the rubric.

**Stage 4:** Every required artifact now has a real, tested mechanism behind it, and every remaining gap is documented rather than hidden. The remaining work is not building new artifacts — it is growing evidence and closing specific, named sub-gaps.

---

## Change Log

| Date | Change |
|---|---|
| 2026-09-25 | Initial rubric tracking checklist created after completing the Stage 4 five-artifact hardening pass. |
| 2026-09-25 | Added Stage 3 requirements (The Prompt, The Evaluations, The Log) after receiving both rubric images. |
