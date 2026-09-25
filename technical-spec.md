Its# PR Pattern Detective — Technical Specification

## 1. Document status

Status: Draft

This is the normative, living specification for PR Pattern Detective. It records confirmed system requirements separately from the narrative and decision history in `case-study.md`.

The keywords **must**, **should**, and **may** indicate required, recommended, and optional behavior. Requirements marked **Open** are not yet finalized.

### 1.1 Documentation synchronization

Every confirmed product-related decision made in chat or during implementation must update both this specification and `case-study.md` in the same task. This includes decisions about product building blocks, features, scope, workflows, interfaces, architecture, data contracts, policies, constraints, and revisions to earlier decisions.

This specification must translate the decision into normative behavior. The case study must record the decision and Nate's established reasoning in first person. Tentative proposals must remain marked as open, and resolved decisions must be removed from the applicable open-decision lists.

## 2. Purpose

PR Pattern Detective is a project-aware review system that establishes or validates a repository's design-system baseline and uses that baseline to review planned and implemented work.

The system must:

- Adapt to different applications rather than enforce universal design preferences.
- Establish sufficient project context before evaluating tickets or pull requests.
- Detect UX-pattern conformance issues, contextual accessibility issues, and repository-convention violations.
- Preserve traceability between approved design intent and implementation.
- Keep humans responsible for ambiguous or newly generated design decisions.

## 3. Scope

### 3.1 In scope

- First-run repository and design-system initialization
- Figma and coded design-system discovery and validation
- Guided creation or completion of a design system
- Azure DevOps ticket readiness review
- Azure DevOps pull-request implementation review
- UX-pattern, accessibility, and repository-convention analysis
- Validation, prioritization, and deduplication of findings
- Fixture-based evaluation of system quality

### 3.2 Out of scope

- Treating repository frequency as proof that a pattern is correct
- Replacing deterministic linting, type checking, or tests with an LLM agent
- Automatically making ambiguous design decisions authoritative
- Treating one application's UX conventions as universal requirements

## 4. System lifecycle

The system has three lifecycle stages:

1. Repository initialization
2. Ticket-start review
3. Pull-request review

Repository initialization must complete with a usable outcome before ticket or PR review can rely on the project baseline.

### 4.1 MVP commands

Confirmed review commands:

```text
/init-agent <repo>
/ticket-agent <ticket-number>
/pr-agent <pr-number>
```

The MVP uses explicit commands instead of requiring a pipeline, local poller, or background event listener. Automation may be added later if missed invocations become an observed problem.

### 4.2 Implementation form

The commands are implemented as a hybrid:

- **LLM agent prompts** drive judgment work — dimension classification, evidence interpretation, targeted questioning, specification, and review reasoning.
- **Deterministic helpers** perform machine-checkable work — baseline and ticket-context file writes, file-existence checks, compile/build validation, and other mechanical verification.

Deterministic operations must not depend on LLM output formatting, and agent findings must not be the only evidence for checks that can be verified in code.

## 5. Repository initialization

### 5.1 Responsibilities

Initialization must:

1. Discover available design and implementation sources.
2. Determine repository and design-system state.
3. Validate existing foundations, components, and patterns.
4. Identify gaps, conflicts, legacy areas, and inaccessible sources.
5. Ask targeted questions when intent cannot be inferred reliably.
6. Reconcile, complete, or create the design system with user approval.
7. Save an approved project-specific baseline.

When multiple sources are available (for example, Figma and a coded system), the initializer must ask the user whether to work Figma-first or code-first, then process sources in that order.

AI-generated design decisions must not become authoritative without user approval.

### 5.2 Dimension model

Initialization must classify the project using four dimensions.

#### Figma state

- `absent`
- `unavailable`
- `partial`
- `complete`

#### Coded design-system state

- `absent`
- `partial`
- `complete`
- `external`
- `multiple`

#### Source relationship

- `not_applicable`
- `aligned`
- `drifted`
- `authority_unclear`

#### Repository maturity

- `greenfield`
- `existing_consistent`
- `existing_inconsistent`
- `active_migration`

Initialization behavior must be selected from the combination of these dimensions rather than from a fixed list of mutually exclusive setup paths.

### 5.3 Figma access

Figma inspection must use the Figma MCP server to retrieve structured design context (components, variables, styles, and frames). If the MCP server or the relevant files are unreachable, the initializer must classify Figma state as `unavailable` rather than `absent` and must not substitute assumptions for evidence.

Fixtures exercising Figma-dependent behavior in an environment without a live Figma MCP connection must simulate its output as a fixture input (e.g. a `figma-export.json` alongside `fixture.json`) rather than skip the scenario — the same convention used for simulated ADO ticket/PR content in `ticket`/`pr` fixtures. The simulated data is treated as real evidence for the fixture's purposes and must be documented as simulated in the fixture description.

### 5.4 Evidence sources

The initializer may evaluate:

- Approved Figma designs and component systems
- Coded design-system packages and components
- Design tokens and themes
- Storybook or equivalent component documentation
- Explicit project and contribution guidance
- User-approved canonical screens and components
- Comparable established repository patterns
- Existing migration and deprecation documentation

Frequency alone must not make an implementation authoritative.

### 5.5 Source conflicts

When Figma and code disagree, initialization must:

1. Identify and present the relevant differences.
2. Ask whether Figma, code, or a component-by-component decision represents the intended future state.
3. Record the approved authority decision in the project baseline.

The initializer must not silently assume Figma or code always wins.

### 5.6 Progressive design-system creation

When no adequate system exists, initialization must first present a high-level roadmap and then process one layer at a time.

For each layer, it must:

1. Inspect available evidence.
2. Ask targeted questions where intent is unresolved.
3. Present a focused specification.
4. Obtain user approval.
5. Implement the approved layer.
6. Validate the implementation.
7. Continue to the next dependent layer.

Before generating code, initialization must collect key implementation details from the user, including the target framework (for example, React) and styling approach. Generated decisions must not assume a stack that was not provided or detected.

Initialization must also verify that the repository's build toolchain is actually wired up to run the chosen stack — for example, that a framework dependency declared in the package manifest (such as `@vitejs/plugin-react`) is registered in the build config (such as `vite.config.js`) — before generating layer code on top of it. A declared dependency is not evidence that the toolchain is configured; initialization must check the config itself and fix or flag gaps as part of Step 0 rather than surfacing them as a mid-layer runtime failure.

Initialization writes approved layers directly into the repository rather than producing per-layer PRs or specs for later implementation. It must also produce a committed design-system library that renders the generated foundations and components so the user can review and test them visually.

The library must be served by the repository's own dev server at a local route — for a Vite app, a `library.html` entry at the repo root rendering `src/design-system/` components, with no router dependency required. The library must present every approved foundation (typography scale, color, spacing) and every approved component in all variants and relevant states (default, hover, disabled, loading, error), organized by layer order. Its entry path is recorded in `baseline.json` as `library_page`.

The expected dependency order is:

1. Typography
2. Color
3. Spacing and other foundational tokens
4. Small components
5. Interactive components
6. Composite components
7. Large components and page-level patterns

The exact foundation and component taxonomy remains extensible to project needs.

When a partial system exists, initialization must preserve validated work and begin at missing or invalid layers rather than rebuilding the entire system.

Validation is incremental: once a layer or the library has passed validation, later additions must validate only the new changes rather than revalidating the full system.

### 5.7 Initialization outcomes

Initialization must return one of these outcomes:

- `ready`: The approved baseline sufficiently covers expected work.
- `ready_with_gaps`: Work may proceed, but named areas require ticket-time review.
- `blocked`: The repository lacks sufficient authority or foundational consistency for reliable review.

A minimum viable baseline requires:

- Identified authoritative sources
- Approved core foundations
- An established accessibility target
- Mapped components and patterns for the current product area
- Recorded conflicts, gaps, and legacy areas
- A distinction between approved precedent and legacy frequency
- A process for introducing missing components and patterns

Baseline checks must be verified programmatically wherever verification is possible in code — for example, confirming that expected token and component files exist, that generated code compiles, and that the design-system library page builds. User confirmation is required only for judgment calls that code cannot decide, such as source authority, gap significance, and whether a frequent pattern is precedent or legacy.

### 5.8 Project baseline

Initialization must persist an approved project baseline for later review stages.

The baseline must be capable of representing:

- Source locations and authority
- Validated foundations
- Approved components and patterns
- Figma-to-code relationships when applicable
- Canonical examples
- Known gaps
- Legacy or deprecated patterns
- Migration targets
- Approved exceptions

The baseline must be stored as a committed file at `.prpd/baseline.json` so it is versioned, shared, and reviewable in pull requests. Per-ticket context (findings and approved decisions produced by `/ticket-agent`) must be stored separately in `.prpd/tickets.json`, also committed, so ticket history does not bloat the design-system record.

### 5.9 Baseline schema

`baseline.json` must use the following top-level structure:

```json
{
  "version": 1,
  "repo": "<repo identifier>",
  "initialized_at": "<ISO-8601 timestamp>",
  "outcome": "ready | ready_with_gaps | blocked",
  "dimensions": {
    "figma": "absent | unavailable | partial | complete",
    "coded_system": "absent | partial | complete | external | multiple",
    "source_relationship": "not_applicable | aligned | drifted | authority_unclear",
    "maturity": "greenfield | existing_consistent | existing_inconsistent | active_migration"
  },
  "stack": {
    "framework": "<e.g. react>",
    "styling": "<styling approach>",
    "component_dir": "<path>",
    "token_files": ["<paths>"]
  },
  "sources": [
    {
      "type": "figma | code | tokens | storybook | guidance | canonical_example",
      "location": "<url or path>",
      "authority": "authoritative | reference | deprecated",
      "scope": ["<areas this source governs>"]
    }
  ],
  "accessibility_target": "<e.g. WCAG 2.1 AA>",
  "foundations": {
    "<foundation name>": { "status": "approved | gap | legacy", "source": "<source ref>", "notes": "" }
  },
  "components": [
    {
      "name": "<component name>",
      "status": "approved | gap | legacy | deprecated",
      "source": "<source ref>",
      "path": "<repo path>",
      "figma_ref": "<figma node url, optional>",
      "variants": ["<variant names>"],
      "notes": ""
    }
  ],
  "gaps": [
    { "area": "<area>", "description": "<what is uncovered>" }
  ],
  "legacy_patterns": [
    { "description": "...", "location": "<path>", "note": "<why it is not approved precedent>" }
  ],
  "exceptions": [
    { "ticket": "<ADO id>", "scope": "<paths>", "rationale": "...", "approved_at": "<date>" }
  ],
  "migrations": [
    { "from": "<old pattern/component>", "to": "<replacement>", "status": "planned | in_progress" }
  ],
  "library_page": "<path to generated library page>"
}
```

`tickets.json` must key records by ticket identifier and store each ticket's findings, approved decisions, and last-updated timestamp:

```json
{
  "ADO-4821": {
    "findings": ["<finding>"],
    "approved_decisions": ["<decision>"],
    "updated_at": "<ISO-8601 timestamp>"
  }
}
```

## 6. Ticket-start review

### 6.1 Invocation

```text
/ticket-agent <ticket-number>
```

### 6.2 Inputs

The ticket agent should retrieve, when available:

- ADO ticket title and description
- Acceptance criteria
- Linked Figma designs
- Parent, child, and related work items
- Referenced components or product areas
- The approved project baseline
- Prior ticket-agent findings and decisions

Azure DevOps access must use the ADO MCP server for work-item and pull-request retrieval. The same integration applies to `/pr-agent` inputs.

### 6.3 Responsibilities

The ticket agent must assess:

- Whether the ticket contains enough information to begin implementation
- Whether proposed work uses approved components and patterns
- Whether a missing component or pattern is required
- Whether loading, empty, error, disabled, permission, and responsive states are sufficiently defined when applicable
- Whether accessibility requirements are sufficiently defined
- Whether Figma and coded-system coverage are adequate for the work
- Whether unresolved design or product decisions should pause implementation

### 6.4 Missing component or pattern

When the baseline does not cover a ticket need, `/ticket-agent` must evaluate expected reuse.

#### Reusable need

When reuse across screens or future features is reasonably likely, the system must guide a design-system extension before feature development depends on it. The extension workflow must:

1. Search Figma and the repository for an existing solution.
2. Ask clarifying questions.
3. Specify the addition with the user.
4. Obtain approval.
5. Implement and validate it.
6. Add it to the approved baseline.

#### Feature-specific need

When the implementation is genuinely specific to one feature and does not justify a reusable abstraction, the system may approve a ticket-scoped exception.

The exception must record:

- Why existing patterns are insufficient
- Why a shared addition is inappropriate
- Which approved foundations still apply
- The scope within which the exception is permitted

When reuse potential is uncertain, the system must ask the user. It should bias toward a shared extension when future reuse is reasonably likely.

### 6.5 Ticket context persistence

Ticket findings and approved decisions must be persisted to `.prpd/tickets.json` and remain available to `/pr-agent`. Pull-request review must verify implementation against this context rather than rediscovering intent without history. `tickets.json` must be validated against its schema (`prpd.py ticket validate`) as part of persistence, the same way `baseline.json` is validated after initialization.

Reading prior ticket context (`prpd.py ticket get <ticket-number>`) must succeed whether or not anything was previously recorded for that ticket — no prior context is a normal, expected first-review case, not an error condition.

If requirements or component needs change during development, the developer should rerun:

```text
/ticket-agent <ticket-number>
```

before treating the changed plan as approved.

## 7. Review engines

The three agents are reusable review engines. Ticket review uses them to assess intent and readiness; PR review uses them to assess implementation.

### 7.1 UX Pattern Conformance Analyzer

Core question:

> Does this composition create a coherent experience that follows the project's approved patterns?

It must evaluate, where relevant:

- Groups and compositions of components
- Layout and information architecture
- Workflow and action hierarchy
- Visual hierarchy
- Page-level patterns
- Reuse of comparable approved patterns
- New or expanded patterns and their rationale

It should not enforce one application's patterns universally.

### 7.2 Contextual Accessibility Auditor

Core question:

> Can people with disabilities successfully use this implementation?

It must evaluate, where relevant:

- New and modified components
- Configuration and composition of approved components
- Semantic structure
- Accessible names
- Keyboard and focus behavior
- Form relationships and error communication
- Table relationships
- Dynamic status announcements
- Page- and workflow-level accessibility

It should not repeatedly audit unchanged internals of approved components unless the change affects them.

The default accessibility target is **WCAG 2.2 AA**. Initialization must confirm the target with the user per repository, since individual projects may have different obligations, and must record the confirmed value in `baseline.json` under `accessibility_target`.

### 7.3 Repository Convention Auditor

Core question:

> Does this implementation belong in this codebase?

It must evaluate project-specific conventions that require repository context, including where applicable:

- Shared-component reuse
- Token usage
- File placement and exports
- State and data-access patterns
- Component variant conventions
- Duplicated abstractions
- Expected test structure

It must not duplicate generic formatting, syntax, type checking, or other rules better enforced deterministically.

### 7.4 Finding model

Every engine emits findings with this schema:

```json
{
  "id": "<engine>-<seq>",
  "engine": "ux_pattern | accessibility | convention",
  "severity": "blocker | advisory",
  "title": "<short title>",
  "location": { "file": "<path>", "lines": [1, 20] },
  "description": "<what is wrong and why>",
  "suggested_fix": "<actionable correction>",
  "confidence": 0.0,
  "traceability": "baseline | extension | exception | none",
  "low_confidence": false,
  "status": "open | fixed | overridden",
  "override": null
}
```

Enforcement is binary:

- `blocker` findings fail the check until resolved or overridden.
- `advisory` findings are informational and never block.
- Any finding with `traceability: "none"` (a component or pattern with no approval trail) must be a blocker.
- A developer may override a blocker by providing reasons. The override must be recorded as `{"reasons": "...", "by": "...", "at": "<timestamp>"}` on the finding and surfaced in the report. The finding text must be clear enough that a reviewer can evaluate the override rationale.

Findings are append-only and must never be deleted, including once fixed or superseded — `status` records their current resolution state (default `open` when absent) so history stays intact while enforcement only counts currently-open blockers. A ticket-time blocker that was resolved through an approved decision (not a built extension) must stay `open` until `/pr-agent` verifies the implementation actually reflects that decision — recording a decision is not the same as implementing it, and only the later stage can confirm the code matches.

Confidence thresholds by engine:

| Engine | Threshold |
|---|---|
| Accessibility | 0.90 |
| UX pattern | 0.75 |
| Convention | 0.85 |

Findings below threshold must be emitted with `low_confidence: true`, flagged as "needs review," counted in report statistics, and must never block.

## 8. Pull-request review

### 8.1 Invocation

```text
/pr-agent <pr-number>
```

### 8.2 Inputs

The PR agent should retrieve, when available:

- PR title and description
- Source and target revisions
- Changed files and diff
- Linked ADO ticket
- Ticket-agent findings and approved decisions
- The approved project baseline
- Existing review findings from prior runs

### 8.3 Responsibilities

The PR agent must:

1. Verify that the PR is linked to the relevant reviewed ticket or surface missing context.
2. Compare implementation with approved ticket intent.
3. Run all three review engines against the implementation.
4. Validate and consolidate findings through guardrails.
5. Support reruns after changes.

A draft PR may be used as an early correction loop before the PR is marked ready.

### 8.4 Traceability requirement

Every new component or pattern must trace to:

- The approved project baseline,
- An approved reusable extension, or
- An approved ticket-scoped exception.

A component or pattern without corresponding approval requires resolution before PR approval. This is a process-integrity failure, not proof that the implementation itself is inherently incorrect.

The developer may resolve it by:

- Providing evidence of prior approval
- Obtaining approval for a ticket-scoped exception
- Replacing it with an approved existing solution
- Completing the design-system extension workflow

The system must not silently convert an unreviewed implementation into approved precedent.

### 8.5 ADO reporting and enforcement

PR findings are reported through Azure DevOps pull-request comments via the ADO MCP server:

- One maintained **summary comment** per PR contains the complete report — verdict (fail/pass), all findings ordered blockers → advisory → needs-review, overrides, and finding statistics.
- Each finding tied to specific code gets an **inline thread** at its file and line. Threads stay active while unresolved.
- A developer overrides a blocker by replying in its thread with reasons; the override is recorded on the finding (`status: "overridden"` plus the `override` object) and in `tickets.json`, and the thread is resolved as overridden rather than fixed.
- Enforcement relies on ADO's required comment-resolution branch policy: unresolved blocker threads prevent completion.
- Rerunning `/pr-agent` must update the summary comment, mark findings `fixed`/`overridden` (never delete them) via `prpd.py ticket resolve`, resolve their threads, and open threads for new findings. Verdict is `fail` while any blocker's `status` is `open` (the default), `pass` once every blocker is `fixed` or `overridden`.
- A required external PR status check may be added later if comment resolution proves insufficiently enforceable.

## 9. Guardrails

Guardrails must:

- Validate agent output
- Apply reporting and confidence policies
- Prioritize findings
- Deduplicate or combine overlapping findings
- Preserve which review perspective produced each underlying issue

Guardrails must apply the per-engine confidence thresholds and the blocker/advisory enforcement model defined in §7.4, including override recording. Deduplication and merge rules for overlapping findings are **Open**; a concrete observed case exists (`PR-55` in `prpd/fixtures/03-pr-manage-users/`, where the same ad hoc component was flagged separately by the convention engine as untraced and by the ux_pattern engine as visually inconsistent) and should inform whatever rule is decided rather than being resolved arbitrarily in the meantime — findings are kept distinct, not merged, until this is resolved.

### 9.1 Deterministic between-step gates

In addition to the per-finding policies above, the system must enforce deterministic, automated gates positioned **between** agent steps — not human review, and not logic embedded inside an agent's own reasoning. A gate must read only committed state (never trust an agent's self-report that a prior step succeeded), decide pass/fail with no LLM judgment involved, and on pass write a sentinel file recording what it verified and a checksum of the artifact it certified, so a later change to that artifact without rerunning the gate is itself detected as a failure.

`/ticket-agent` must run `prpd.py guardrail init-to-ticket` before doing anything else, and must stop if it fails rather than proceeding on its own reading of the baseline. `/pr-agent` must run `prpd.py guardrail ticket-to-pr <ticket-id>` before reading ticket context, for the same reason. Full gate criteria and proof of active bypass-testing are recorded in `GUARDRAILS.md`.

### 9.2 Adversarial challenge

The system must include an automated adversarial review pass, distinct from the three review engines, that argues against a prior step's conclusion using a fresh, isolated context with no visibility into the original reasoning — only its inputs and outputs. This is what distinguishes it from Stage 2 human re-review: it is scripted and repeatable, not ad hoc, and it cannot simply agree with itself. A successful challenge (finding something the original review missed or got wrong) is persisted as a new finding through the normal `ticket upsert` path, tagged with the step that produced it; a challenge that finds nothing is still logged via `prpd.py audit challenge_run` so the check itself is auditable. Full specification: `prpd/commands/guardrail-challenge.md`. Proof this catches real issues, not just theoretical ones, is recorded in `GUARDRAILS.md`.

### 9.3 Punch-out points

Explicit human decision points must be enforced in code, not only documented as prompt instructions. `baseline set outcome` must refuse to finalize `ready`/`ready_with_gaps` unless `stack_confirmed` and `accessibility_target_confirmed` are on record in `.prpd/punchouts.jsonl`; `baseline append components` must refuse an extension-sourced component unless `extension_approved:<name>` is on record; overriding a blocker (`ticket resolve --status overridden`) must automatically log itself as a punch-out, since accepting risk instead of fixing something is itself a human decision point. Bypass attempts against each of these must be actively tested, not assumed to work from the specification alone. Full point registry and bypass-test results: `PUNCHOUTS.md`.

## 10. Test runner

The system must be evaluated against representative fixtures rather than only plausible agent output.

The fixture suite must eventually include:

- Tickets and PRs that should pass
- Tickets and PRs containing known violations
- Ambiguous cases requiring clarification
- Cross-agent overlap cases
- Approved exceptions
- Legacy and migration scenarios

### 10.1 Fixture format

A fixture is a directory containing:

- `repo/` (init fixtures) — a repository in the state the fixture is meant to exercise; for `init` fixtures, this is the completed, committed result of a run. Ticket/PR-stage fixtures instead reference an existing init fixture's repo via `target_repo`, since ticket and PR review operate on a repo that already has a baseline rather than a fresh scaffold.
- `fixture.json` — `id`, `stage`, a human `description`, an `expected` block (stage-specific: `dimensions`/`outcome` for `init`, `readiness_verdict`/`extension_approved` for `ticket`, etc., plus free-text `behaviors` describing expected process), and, for stages that require simulated input, a `user_simulation` block recording the answers a user would give and (for `ticket`/`pr` stages) a `ticket`/`pr` block simulating the fetched work item, since there is no live ADO integration in these fixtures.

This format is proven by `prpd/fixtures/01-greenfield/` (init), `prpd/fixtures/02-ticket-new-page/` (ticket — the first fixture to exercise `/ticket-agent`'s reuse-vs-exception extension workflow end to end), `prpd/fixtures/03-pr-manage-users/` (pr — the first fixture to exercise `/pr-agent`'s traceability check, all three engines, and the fail-then-fix-then-pass rerun loop end to end), and `prpd/fixtures/04-existing-inconsistent/` (init — the first fixture to exercise dimension classification away from the greenfield defaults and §5.5's source-conflict reconciliation, using a simulated Figma MCP export the same way ticket/PR fixtures simulate ADO content).

### 10.2 End-to-end success rate

Per-fixture pass/fail is not sufficient; the system must report a success rate measured over **chains** — a defined sequence of fixtures where init → ticket → PR operate on the same repo (`prpd/fixtures/chains.json`). A chain counts as passing only if every fixture in it currently passes; one broken link fails the whole chain rather than being averaged away by unrelated passing fixtures. `run_fixture.py --all` computes this automatically and appends a timestamped record to `prpd/fixtures/results.jsonl`; `run_fixture.py --report` prints the resulting trend. Fixtures not yet part of a complete chain (e.g. an init-only scenario with no ticket/PR built on top of it) must be reported separately, not folded into the end-to-end number. Full methodology and current honest limitations (sample size, what this number does and does not claim): `SUCCESS_RATE.md`.

### 10.3 Test runner v1 (mechanical checker)

`prpd/tools/run_fixture.py` is a deterministic, dependency-free script (`python3 prpd/tools/run_fixture.py --all` or `<fixture-dir>`) that scores a fixture's target repo against its `fixture.json` `expected` block using only end-state, code-verifiable checks. For `init` fixtures:

- `baseline validate` and `check-files` both pass
- recorded `dimensions` exactly match `expected.dimensions`
- recorded `outcome` is a member of `expected.outcome`
- `library_page` is recorded and the file exists
- every `approved` component/foundation's recorded path exists
- the repo's build succeeds (skipped, not silently passed, if dependencies are not installed)
- `.prpd/audit.jsonl` is well-formed and contains the fixture stage's minimum required step tags

For `ticket` fixtures:

- `ticket validate`, `baseline validate`, and `check-files` all pass
- the ticket ID has recorded findings and approved decisions in `tickets.json`
- any `expected.extension_approved` component is present in the baseline as `approved` with an existing file

For `pr` fixtures:

- `ticket validate`, `baseline validate`, and `check-files` all pass
- the verdict computed from the linked ticket's findings (`fail` if any blocker has `status: open`, `pass` otherwise) matches `expected.final_verdict`

It exits non-zero if any check fails, and separately lists which `expected.behaviors` entries it does **not** cover, since those describe process during a run (e.g. "asks stack questions before generating code") rather than the finished repo state, and cannot be verified from artifacts alone.

This mechanical checker only scores an already-completed fixture; it does not invoke an agent or simulate a user. Whether and how to add an automated, unattended run (an agent executing a command against a fixture using its `user_simulation` block, without a human approving each step) is still **Open** — everything in this system runs locally, so this would not require external orchestration, but the approach for scripting the simulated-user side is undecided.

Remaining open items: accuracy/false-positive targets, mechanical or LLM-assisted verification of process-level `behaviors`, and the automated-run approach above.

## 11. Audit trail

Every workflow step must be traceable. The system must maintain `.prpd/audit.jsonl` — an append-only log of JSON events.

- Every `prpd.py` helper call automatically logs a `helper_call` entry: timestamp, command, workflow step tag, and result (`ok`/`fail`).
- Agents must emit `agent_event` entries via `prpd.py audit <event>` for judgment moments: questions asked, approvals granted or denied, overrides, layer completions, and engine runs.
- Agent-emitted entries should include `step` (for example `init.layer.color`, `pr.engine.accessibility`), `model`, `tokens_in`, `tokens_out`, and `cost_usd` when known, so per-step model and cost data is available.
- Any failure must be traceable to its origin step. Guardrail rejections and validation failures must appear in the log with the producing step.
- `--step` is a required argument (not merely recommended) for every mutating command: `baseline new/set/append`, `ticket upsert/resolve`, `guardrail init-to-ticket/ticket-to-pr`, `punchout record`, and `audit`. It remains optional for read-only commands (`validate`, `check-files`, `ticket get`, `guardrail status`, `punchout log`), which produce no new state to trace. `prpd/tools/trace_failure.py <repo-dir>` reports which recorded failures trace to an origin step and exits non-zero if any do not.
- `model`/`tokens_in`/`tokens_out`/`cost_usd` can only be populated accurately by a caller that actually has that data (e.g. a wrapper script driving the LLM API directly and passing through the response's `usage` fields) — an interactive agent session has no runtime access to its own token/cost accounting and must not fabricate these values. See `AUDIT_TRAIL.md` for the current honest status and the architecture that would populate them for real.

## 12. Open technical decisions

- Deduplication and disagreement policy
- Accuracy/false-positive targets for the test runner
- Mechanical or LLM-assisted verification of process-level fixture `behaviors`
- Whether/how to script an automated, unattended agent run against a fixture's `user_simulation` block
