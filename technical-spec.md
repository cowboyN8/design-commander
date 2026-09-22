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

Ticket findings and approved decisions must be persisted to `.prpd/tickets.json` and remain available to `/pr-agent`. Pull-request review must verify implementation against this context rather than rediscovering intent without history.

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
  "override": null
}
```

Enforcement is binary:

- `blocker` findings fail the check until resolved or overridden.
- `advisory` findings are informational and never block.
- Any finding with `traceability: "none"` (a component or pattern with no approval trail) must be a blocker.
- A developer may override a blocker by providing reasons. The override must be recorded as `{"reasons": "...", "by": "...", "at": "<timestamp>"}` on the finding and surfaced in the report. The finding text must be clear enough that a reviewer can evaluate the override rationale.

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
- A developer overrides a blocker by replying in its thread with reasons; the override is recorded on the finding and in `tickets.json`, and the thread is resolved as overridden rather than fixed.
- Enforcement relies on ADO's required comment-resolution branch policy: unresolved blocker threads prevent completion.
- Rerunning `/pr-agent` must update the summary comment, resolve threads for findings that are fixed or overridden, and open threads for new findings.
- A required external PR status check may be added later if comment resolution proves insufficiently enforceable.

## 9. Guardrails

Guardrails must:

- Validate agent output
- Apply reporting and confidence policies
- Prioritize findings
- Deduplicate or combine overlapping findings
- Preserve which review perspective produced each underlying issue

Guardrails must apply the per-engine confidence thresholds and the blocker/advisory enforcement model defined in §7.4, including override recording. Deduplication and merge rules for overlapping findings are **Open**.

## 10. Test runner

The system must be evaluated against representative fixtures rather than only plausible agent output.

The fixture suite must eventually include:

- Tickets and PRs that should pass
- Tickets and PRs containing known violations
- Ambiguous cases requiring clarification
- Cross-agent overlap cases
- Approved exceptions
- Legacy and migration scenarios

Accuracy targets, false-positive targets, fixture format, and completion criteria are **Open**.

## 11. Audit trail

Every workflow step must be traceable. The system must maintain `.prpd/audit.jsonl` — an append-only log of JSON events.

- Every `prpd.py` helper call automatically logs a `helper_call` entry: timestamp, command, workflow step tag, and result (`ok`/`fail`).
- Agents must emit `agent_event` entries via `prpd.py audit <event>` for judgment moments: questions asked, approvals granted or denied, overrides, layer completions, and engine runs.
- Agent-emitted entries should include `step` (for example `init.layer.color`, `pr.engine.accessibility`), `model`, `tokens_in`, `tokens_out`, and `cost_usd` when known, so per-step model and cost data is available.
- Any failure must be traceable to its origin step. Guardrail rejections and validation failures must appear in the log with the producing step.

## 12. Open technical decisions

- Deduplication and disagreement policy
- Fixture format and measurable success criteria
