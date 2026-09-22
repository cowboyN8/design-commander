# Designing PR Pattern Detective

## Creating a project-aware review system for design, accessibility, and engineering conventions

I am a Design Engineer with more than five years of experience in design systems, front-end development, and accessibility. I started this project after seeing UX patterns and accessibility regressions reach an internal product without a systematic review gate.

A non-developer and prompt engineers were able to generate and ship code, but the team did not have a reliable process for determining whether those changes followed an intentional design system. Other developers did not consistently catch the problems during review. I wanted to explore whether a multi-agent PR reviewer could provide that missing layer of scrutiny before merge.

## The original idea

My initial concept was a local PR-review system with three agents:

1. A Pattern Analyzer for UX anti-patterns
2. An Accessibility Auditor for accessibility regressions
3. A Consistency Checker for codebase conventions

Guardrails would validate and consolidate their findings, while a test runner would evaluate the system against representative PR fixtures.

I initially approached the Pattern Analyzer by recalling problems from a previous project. UI conventions could change substantially in a single release without a design check. A title might begin with one badge and later accumulate five badges with no hierarchy. In another case, a device-return action was buried among four or five stacks of accordions in the middle of a device profile. I would have placed that action in an established actions dropdown and opened the return workflow in a modal.

These examples revealed a broader problem: developers were introducing or expanding UX patterns without an approved design, an established repository precedent, or an explanation of why a new pattern was needed.

## Recognizing the missing dependency

As I tried to define universal anti-patterns, I realized the approach was wrong for the product I wanted to build. PR Pattern Detective should be reusable across different applications. My preferences and the mistakes from one previous project could not become universal UX rules.

The real dependency was not a catalog of fixed anti-patterns. It was a project-specific design-system baseline.

A reviewer cannot reliably flag inconsistent typography, hierarchy, component usage, or interaction patterns when the project has never defined what correct behavior looks like. On my previous project, there was no Figma system or coded standard at the beginning; the application was generated in code from the start. The inconsistency was partly a consequence of that missing foundation.

I therefore decided that the system must initialize the repository before it reviews PRs.

## Making initialization part of the product

Initialization is a separate first-run workflow. Its purpose is to discover, validate, complete, or establish the repository's design system and save an approved baseline for later reviews.

I want the initializer to work progressively. It should begin with typography, color, spacing, and other foundations, then move through small and interactive components, composite components, large components, and page-level patterns. This order prevents the system from designing complex components before their underlying rules are stable.

The initializer should not make unexplained design decisions on the user's behalf. It should scan the available evidence, identify ambiguity, ask targeted questions, and require human approval before generated decisions become authoritative.

## Replacing fixed setup paths with a dimension model

I initially described five setup paths:

1. A complete Figma design system that needs to be implemented in code
2. An incomplete Figma system that needs recommendations and re-validation
3. No Figma system, requiring spec-driven design-system creation
4. An existing coded design system without Figma
5. An existing application with neither Figma nor a coded design system

That captured the major situations, but it did not cover combinations such as Figma and code disagreeing, partial coded systems, external packages, multiple products, migrations, or inaccessible design files.

I chose to replace the fixed-path model with four dimensions.

### Figma state

- Absent
- Unavailable
- Partial
- Complete

### Coded design-system state

- Absent
- Partial
- Complete
- External dependency
- Multiple systems

### Relationship between sources

- Not applicable
- Aligned
- Drifted
- Authority unclear

### Repository maturity

- Greenfield
- Existing and consistent
- Existing and inconsistent
- Active migration

I chose this model because repository conditions are combinations, not a small set of mutually exclusive scenarios. The dimensions allow initialization behavior to adapt without requiring a separate hard-coded workflow for every possible case.

## How initialization responds to the dimensions

The combined state determines whether the initializer validates, recommends remediation, fills gaps, reconciles sources, or creates a system with the user.

Examples include:

- If Figma is complete and no coded system exists, the initializer validates Figma and implements the approved system in code.
- If Figma is incomplete, it identifies gaps, recommends fixes, and re-checks the system before approval.
- If Figma and code exist and agree, it validates their mappings and avoids rebuilding valid work.
- If Figma and code disagree, it presents the differences and asks which source represents the intended future state.
- If only a coded system exists, it validates and uses that system as the baseline.
- If a coded system is partial, it preserves valid foundations and works with the user to fill its gaps.
- If an existing application has no formal system, it examines the current code, distinguishes useful precedent from accidental inconsistency, and asks clarifying questions before creating the system.
- If the project is greenfield, it creates the specification through a guided, progressively approved process rather than pretending it can infer intent from nonexistent evidence.
- If the system is external, multi-product, themed, legacy, or under migration, initialization records the applicable scope, ownership, exceptions, and target state.

I explicitly decided that frequency alone cannot establish correctness. A pattern may be common because it is legacy or repeatedly copied, not because it is intentional.

## Resolving conflicts between Figma and code

Figma is an important source, but it cannot automatically override code in every repository. Code may be newer, Figma may be incomplete, or the two sources may represent different stages of a migration.

When Figma and code conflict, the initializer should show the differences and ask whether Figma, code, or a component-by-component decision represents the intended future state. It then records that decision in the approved project baseline.

The baseline may reference:

- Approved Figma designs and component systems
- The coded design system
- Tokens and themes
- Storybook or other component documentation
- Explicit project guidance
- User-approved canonical screens and components
- Comparable established repository patterns
- Rationale supplied in a PR

This creates an evidence hierarchy without assuming that any single source is always correct.

## Approving a minimum viable baseline

I decided that initialization should not require a theoretically complete design system before the repository can use the review agents. Instead, it should approve a minimum viable baseline and explicitly record uncovered areas.

I chose this approach because design systems are rarely complete, and required coverage depends on the product. A dashboard may depend heavily on tables and filters while a marketing site may not need those patterns at all. Requiring universal completion would either block adoption indefinitely or encourage the initializer to create components without a demonstrated product need.

A repository has enough baseline coverage to proceed when:

- Its authoritative sources are identified.
- Its core foundations are approved.
- Its accessibility target is established.
- Components and patterns needed by the current product area are mapped.
- Known conflicts, gaps, and legacy areas are recorded.
- Legacy frequency is not mistaken for approved precedent.
- There is an agreed process for introducing missing components and patterns.

Initialization returns one of three outcomes:

- **Ready:** The approved baseline sufficiently covers expected work.
- **Ready with gaps:** Work may proceed, but named areas require additional review when a ticket encounters them.
- **Blocked:** The repository lacks enough authority or foundational consistency for the agents to judge future changes reliably.

Known gaps are acceptable because `/ticket-agent` provides the next decision point. When a ticket enters an uncovered area, it can surface the gap before implementation and require clarification or design-system work. This supports incremental adoption while keeping uncertainty visible and governed.

## Building the design system progressively

When initialization finds no adequate design system, I decided against generating either a complete system immediately or a complete specification before any implementation. Instead, the initializer will use progressive specification and implementation.

It first presents a high-level roadmap showing the proposed layers and scope. It then works through one layer at a time:

1. Inspect the available project evidence for that layer.
2. Ask targeted questions where intent is unresolved.
3. Present a focused specification.
4. Require user approval.
5. Implement the approved layer.
6. Validate the implementation.
7. Continue to the next dependent layer.

The sequence moves from typography, color, spacing, and other foundations through small components, interactive components, composites, and page-level patterns. This gives the user visibility into the overall direction without producing a large speculative system. It also lets later layers respond to validated implementation rather than assumptions.

The same workflow applies when deriving a system from an existing application with no formal design system. When a partial system exists, initialization preserves validated work and begins at the missing or invalid layers instead of rebuilding everything.

## Handling missing components and patterns at ticket start

I decided that `/ticket-agent` should choose between extending the design system and allowing a ticket-scoped exception based on reuse potential.

When the requested solution represents a reusable need—especially one likely to appear across multiple screens or future features—the ticket pauses for a guided design-system extension. The system searches Figma and the repository first, asks clarifying questions, specifies the addition with the user, obtains approval, implements and validates it, and adds it to the approved baseline before feature development depends on it.

When the need is genuinely specific to one feature and does not justify a reusable abstraction, `/ticket-agent` may approve a ticket-scoped implementation. The exception must document why an existing pattern is insufficient, why a shared addition is not appropriate, what established foundations it still follows, and the scope within which it is allowed.

I chose this conditional approach because always adding to the design system would create speculative or overly specialized components, while always permitting one-off solutions would recreate uncontrolled pattern drift. Reuse potential provides the decision boundary, with a bias toward extending the system when future reuse is reasonably likely.

If `/pr-agent` finds a new component or pattern that was neither approved as a reusable extension nor documented as a ticket-scoped exception, it produces a blocking finding by default. I chose to block because the implementation bypassed the agreed ticket-start decision process rather than merely differing in subjective design preference.

The developer can resolve the block by providing evidence of prior approval, documenting and obtaining approval for a valid ticket-scoped exception, replacing the implementation with an approved existing solution, or completing the design-system extension workflow. The agent should not silently convert the unreviewed implementation into precedent.

## Refining the three review agents

Once initialization became the dependency, I revisited the responsibilities of the three agents. The original Pattern Analyzer and Consistency Checker overlapped too much. I chose to give each agent a distinct layer of responsibility. I later decided that these agents should be reusable review engines across the ticket lifecycle rather than agents that operate only after a PR is opened.

### Agent 1: UX Pattern Conformance Analyzer

This agent reviews compositions rather than isolated primitive styling. It evaluates groups of components, layouts, workflows, visual hierarchy, information architecture, and page-level patterns against the approved baseline.

Its core question is:

> Does this composition create a coherent experience that follows the project's approved patterns?

A design system can contain valid badges, accordions, dropdowns, and modals while a screen still combines them poorly. This agent detects that composition-level problem. It can flag unjustified pattern drift, misuse of valid components, failure to reuse an established pattern, or a new pattern introduced without sufficient precedent or rationale.

### Agent 2: Contextual Accessibility Auditor

I questioned whether this agent still needed to inspect components after initialization had established an accessible design system. I concluded that approved components reduce accessibility risk but do not guarantee accessible usage.

An accessible icon button can still be rendered without a name. Correct headings can be composed in the wrong semantic order. A new table column can lack a meaningful header. Form errors can be visible without being programmatically associated with their fields.

This agent therefore reviews new and modified components as well as their configuration, composition, and workflow context. It should avoid repeatedly auditing unchanged internals of already approved components unless a PR affects them.

Its core question is:

> Can people with disabilities successfully use this implementation?

### Agent 3: Repository Convention Auditor

The original Consistency Checker was not sufficiently distinct from the Pattern Analyzer. I decided to narrow and rename it.

The Repository Convention Auditor focuses on engineering and architectural conventions that require repository context. It can check shared-component reuse, token usage, file placement, established state and data patterns, variant conventions, duplicated abstractions, exports, and expected test structure.

Its core question is:

> Does this implementation belong in this codebase?

Generic formatting, syntax, and mechanically enforceable naming rules should remain the responsibility of linters, type checking, and deterministic tests. This agent is justified only when evaluation requires an understanding of repository-specific architecture.

## Keeping the agent boundaries clear

The agents may inspect the same change, but they do so from different perspectives.

If a PR adds five status badges beside a title:

- The UX Pattern Conformance Analyzer may flag the broken hierarchy or unsupported composition.
- The Contextual Accessibility Auditor may flag meaning communicated through color alone.
- The Repository Convention Auditor may flag one-off styling that bypasses the shared badge component and approved tokens.

Guardrails can later merge related findings into a reviewer-friendly result without erasing the distinction between these responsibilities.

## Supporting layers

### Guardrails

Guardrails will validate agent output, apply confidence and reporting policies, prioritize findings, and deduplicate or combine overlap between agents.

### Test runner

The test runner will evaluate the system against known good, bad, and ambiguous PR fixtures. This is how I plan to measure detection quality and false positives rather than relying only on plausible-looking agent responses.

## Moving review earlier than the PR

I questioned whether a PR was the right time to discover pattern and accessibility mismatches. By that point, a screen may already be implemented, tested, and connected to application logic. A composition-level correction could require substantial redesign instead of a small code change.

I first considered three review checkpoints: ticket start, end of development, and pull request. That model offered early prevention, a private preflight, and final verification, but it also raised the question of how to detect development completion without a pipeline or background automation.

For the MVP, I chose two explicit commands:

```text
/ticket-agent <ticket-number>
/pr-agent <pr-number>
```

`/ticket-agent` runs when work begins. It examines the ADO ticket, linked Figma work, design-system coverage, acceptance criteria, planned patterns, accessibility requirements, and unresolved states before implementation begins.

`/pr-agent` runs after the developer has coded and tested the ticket and created its PR. It loads the linked ticket and prior decisions, reviews the submitted implementation with all three review engines, and produces the final findings. A draft PR can provide an earlier correction loop when needed: the developer can run the command, revise the implementation, and rerun it before marking the PR ready.

I chose explicit commands over a pipeline, local poller, or background automation because two commands are manageable for an MVP and keep the workflow understandable and debuggable. Automation can be added later if missed invocations become an observed problem. The PR remains important, but it is no longer the first point of discovery because ticket review establishes intent before coding.

The findings and decisions from `/ticket-agent` should remain attached to the ticket context so `/pr-agent` can verify them rather than repeating discovery without history.

## Current product model

The current lifecycle is:

1. Run `/init-agent <repo>` to initialize the repository.
2. Determine the available Figma, coded-system, source-alignment, and repository-maturity states.
3. Validate, reconcile, complete, or create the design system with the user.
4. Save the approved project-specific baseline.
5. Run `/ticket-agent <ticket-number>` at the start of each ADO ticket to review design readiness, intended patterns, accessibility requirements, and repository context.
6. Develop and test the ticket, then create its PR.
7. Run `/pr-agent <pr-number>` to review the implementation with all three engines as the final verification gate; rerun it on a draft PR when an earlier correction loop is useful.
8. Validate and consolidate findings through guardrails at each checkpoint, with policies appropriate to that stage.
9. Evaluate the system continuously with representative ticket and PR fixtures.

## Documenting the journey as part of the work

I decided that this case study should remain a living record rather than a retrospective written only after implementation. It will be updated whenever I make or revise a meaningful decision, resolve an open question, begin work on one of the agents or supporting systems, or learn something during implementation and testing that changes the direction of the product.

I chose this approach because the reasoning, uncertainty, and course corrections are part of the case study. Recording only the final architecture would hide how the project evolved and why its boundaries were chosen. Decisions will be described in my first-person voice without inventing motivations that were not established through the work.

## Creating a living technical specification

As the product architecture became more concrete, I decided to create `technical-spec.md` while continuing the design process rather than waiting until every decision was finished. The case study and specification serve different purposes: this case study preserves my first-person reasoning and changes in direction, while the technical specification defines the system's current normative behavior.

I chose to develop them together so implementation requirements do not have to be reconstructed later from a long conversation. Confirmed decisions become requirements in the specification, while unresolved proposals remain explicitly marked as open.

I made synchronization a formal project rule: every confirmed decision in chat or implementation that contributes to the product must update both documents in the same task. This applies to building blocks, features, scope, workflows, interfaces, architecture, data contracts, policies, constraints, and revisions to earlier decisions. I chose not to defer these updates to later summaries because that would allow the documented journey and the implementable requirements to drift apart.

The first draft consolidates the initialization dimension model, minimum-baseline requirements, progressive design-system workflow, ticket and PR commands, three review-engine boundaries, component traceability policy, and the remaining technical decisions. This marks the beginning of formal technical specification work, not the completion of the architecture.

## Locking down how initialization runs

With the initialization workflow defined, I worked through the remaining structural decisions about how it is invoked, where its output lives, and how generated code lands.

I named the initialization command `/init-agent <repo>` so it matches `/ticket-agent` and `/pr-agent`. The three commands form one family of agents across the lifecycle.

For the approved project baseline, I chose a single committed file at `.prpd/baseline.json`. The baseline encodes design authority for the repository, so I want it versioned, shared with the team, and reviewable in pull requests rather than hidden on one developer's machine. I considered a multi-file `.prpd/` directory for readability at scale, but I preferred the simplicity of one file for the MVP; the field-level schema is still open.

I also decided that the initializer writes approved layers directly into the repository instead of producing per-layer PRs or specs for developers to implement later. The per-layer approval step already gives me control over what gets built, so adding a separate PR or ticket pipeline for each layer would slow initialization without adding meaningful oversight. Per-layer PRs can be reconsidered later if teams want code-level review of generated layers.

Before the initializer generates any code, it must ask for the key implementation details it cannot safely assume — the target framework such as React, the styling approach, and related stack decisions. And to make generated work reviewable beyond code diffs, I decided the initializer produces a design-system library page that renders the generated foundations and components for visual testing. I want to see the system it built, not just trust the specification.

For Figma access, I chose the Figma MCP server over raw REST calls or manual exports because it gives the agent structured design context — components, variables, styles, and frames — without me hand-parsing API responses. If the MCP server or files are unreachable, the initializer records Figma as `unavailable` rather than `absent`; an inaccessible source is different evidence than a missing one.

For the minimum-baseline criteria, I decided the initializer verifies in code wherever verification is possible: expected token and component files exist, generated code compiles, and the library page builds. I only want to be asked about judgment calls that code cannot decide — source authority, how much a gap matters, whether a frequent pattern is precedent or legacy. This keeps my approval focused on intent instead of mechanical checks the machine can do itself.

When both Figma and code are available, I decided the initializer asks me which source to start from — Figma-first or code-first — and then works through them in that order. Which source should lead depends on the project, and it is a judgment call I want to make rather than have the tool assume.

I also decided validation is incremental. Once a layer or the library has passed, later additions only need to validate the new changes — revalidating the entire library every time something is added would waste effort on work that already passed.

For Azure DevOps access, I decided to use the ADO MCP server for ticket and pull-request retrieval, consistent with the Figma MCP choice. Both external integrations go through MCP servers rather than raw API calls.

For how the commands are actually implemented, I chose a hybrid: LLM agent prompts drive the judgment work — classification, questioning, specification, and review reasoning — while deterministic helpers handle baseline writes, file checks, and build validation. Mechanical checks should not depend on how reliably a model formats its output, and agent responses should not be the only evidence for something code can verify directly.

I set the default accessibility target to WCAG 2.2 AA — the current standard and a superset of 2.1 AA. Initialization still confirms the target per repository because different projects can carry different obligations, and the confirmed value is stored in the baseline.

I then defined the `baseline.json` schema. It records the classification dimensions (so later stages can see why decisions were made), the confirmed stack, the authority of each source per scope, the approved/gap/legacy status of every foundation and component, known gaps, legacy patterns, ticket-scoped exceptions, migrations, the accessibility target, and the library page path. Per-ticket context — findings and approved decisions from `/ticket-agent` — lives in a separate `.prpd/tickets.json` file rather than inside the baseline, so ticket history does not bloat the design-system record.

## Beginning initializer implementation

With every initialization decision closed, I started scaffolding `/init-agent` under `prpd/`. The structure mirrors the hybrid decision: `prpd/commands/init-agent.md` is the agent prompt that drives judgment work, `prpd/schemas/` holds the JSON Schemas for `baseline.json` and `tickets.json`, and `prpd/tools/prpd.py` is the deterministic helper CLI for baseline writes, schema validation, file-existence checks, and per-ticket context. The agent prompt explicitly forbids hand-writing the JSON files so all mechanical output stays schema-valid. I verified the helper end-to-end against a scratch repository before committing to this structure.

I also nailed down the library-page convention: a committed page inside the repo, served by the repo's own dev server at a local route — for Vite, a root `library.html` entry rendering `src/design-system/` components, no router required. It renders every approved foundation and every component in all variants and states, organized by layer order, so I can run `npm run dev` and visually test what the initializer built. I chose deferring full fixture testing until product completion rather than testing each stage in isolation — the components are prompts and small helpers that are cheap to change, and I want the end-to-end test to exercise the real workflow.

For testing, I defined the fixture approach: each fixture is a directory under `prpd/fixtures/` containing a `fixture.json` manifest — expected dimension classification, expected outcome, expected behaviors, and simulated-user answers — plus a `repo/` directory holding the target repository. I built the first fixture, `01-greenfield`: a minimal Vite + React scaffold with no design system, which exercises the full generative path. The fixture format itself remains open until more fixtures prove it out.

## Defining the finding model

Before building `/ticket-agent`, I settled how agent findings are represented and enforced. I rejected a four-level severity ladder — the difference between "major" and "blocker" felt arbitrary. Instead, enforcement is binary: a finding is a **blocker** (fails the check) or **advisory** (informational). A developer can override a blocker, but only by giving reasons; the override and rationale are recorded on the finding and shown in the report, so overrides stay visible and auditable rather than silent. A component or pattern with no approval trail (`traceability: "none"`) is always a blocker.

I set per-engine confidence thresholds — accessibility 0.90, UX pattern 0.75, convention 0.85 — because accessibility false alarms erode trust fastest, while pattern judgments are inherently more subjective. Below-threshold findings are still reported, flagged "needs review" and counted in the stats; dropping them entirely would hide where the engines are uncertain.

I then wrote `prpd/commands/ticket-agent.md`, the second command. It loads the ADO ticket via MCP, reads the baseline and any prior ticket context, assesses implementation readiness (including the open states checklist and accessibility requirements), applies the missing-component rule — reusable needs pause for a guided design-system extension while genuinely feature-specific needs may get a recorded ticket-scoped exception — and persists findings and decisions to `tickets.json` so `/pr-agent` verifies rather than rediscovers.

For PR reporting I confirmed the comment-based approach: one maintained summary comment with verdict and statistics, inline threads per finding at the file and line, and ADO's required comment-resolution branch policy as the merge gate. Overrides happen in the thread — the developer replies with reasons, which get recorded on the finding and in `tickets.json`, and the thread resolves as overridden rather than fixed. A required status check stays on the table for later if comment resolution proves too weak.

I then wrote `prpd/commands/pr-agent.md`, the third command. It verifies the PR links to a reviewed ticket, checks that every new component or pattern traces to an approval, runs all three engines with their distinct perspectives, applies the confidence and blocker/advisory policy, consolidates findings through guardrails, and reports through the ADO comment model with rerun support.

Mapping the Stage 4 certification criteria onto the project surfaced a gap: no audit trail. I added `.prpd/audit.jsonl`, an append-only event log maintained by `prpd.py`. Every helper call logs automatically, and agents emit structured events — questions, approvals, overrides, engine runs — tagged with workflow step and model/token/cost data. This gives the exam's required failure-to-origin tracing and per-step cost data, and doubles as punch-out evidence since every human approval point is recorded.

## Running `/init-agent` for the first time

Rather than finish every command before testing anything, I decided to actually walk `01-greenfield` through the `/init-agent` workflow by hand, playing the user myself. This reverses the earlier call to defer fixture testing until the product was complete — once the prompt and helper existed, I wanted to know whether the real workflow held up before writing two more commands on top of an unverified foundation.

Running it for real immediately paid for itself. Two problems surfaced that a read-through of the prompts would not have caught:

- `prpd.py` only accepted `--repo-dir` *before* the subcommand (`prpd.py --repo-dir . baseline set ...`), but every agent command file documents it *after* the subcommand (`prpd.py baseline set ... --repo-dir .`). Every agent invocation as written would have failed. I fixed the CLI to accept `--repo-dir` in either position.
- The fixture repo's `package.json` listed `@vitejs/plugin-react` as a dependency but had no `vite.config.js` wiring it up, so Vite fell back to the classic JSX transform and threw `React is not defined` the moment I rendered the first generated component. This was a gap in the target repo's own toolchain, not a mistake in the generated component.

The second finding changed how I think about Step 0. Initialization can't assume that a repo's declared dependencies are actually wired up correctly — it has to verify the toolchain will run the code it's about to generate, not just that the framework is chosen. I'm folding that into initialization's responsibilities rather than treating it as a one-off fix to this fixture.

With both fixed, I approved and implemented the first layer — Typography — end to end: system font stack, a modular 1.25 scale from a 16px base, four semantic roles (heading-1, heading-2, body, caption) as CSS custom properties plus a CSS-modules stylesheet, and a `Text` component that routes all heading/body/caption usage through the approved roles instead of ad hoc styling. I verified it the way the spec requires: recorded through `prpd.py` (never hand-written), then validated by actually running the Vite dev server and looking at `library.html` rendering the roles, not just trusting that the generated code looked right.

I continued through Color (five 9-step hue ramps plus semantic aliases, with status text pinned to each hue's 700-step specifically to hold WCAG 2.2 AA contrast), Spacing (a 4px-base scale plus radius, border-width, and shadow tokens), and the first small components, Button and Badge. Building Button and Badge surfaced a third gap: `baseline set` only replaces a field's whole value, so recording a second approved component meant reading, mutating, and rewriting the `components` array myself — hand-touching the JSON through a side door, which is exactly what the helper exists to prevent. I added a proper `baseline append <field> <json>` command for array fields (`components`, `sources`, `gaps`, `exceptions`) and updated `init-agent.md` and `ticket-agent.md` to call it instead of `baseline set` wherever they touch those arrays.

Three real gaps in three layers is a pattern worth naming: prompts and schemas that look complete on a read-through still had file-level, config-level, and CLI-level assumptions that only broke under actual execution. Running the workflow end to end, not just reviewing it, is what caught all three.

I carried the same discipline through Interactive components (TextInput, Select, Checkbox — all native form elements with label association via `useId`, help/error text wired through `aria-describedby`) and Composites (Card; Modal built on the native `<dialog>` element specifically so focus trapping, background inerting, and Escape/backdrop-close come from the browser instead of a reimplemented focus trap). Every layer was recorded through `prpd.py`, then validated by actually looking at the rendered result in `library.html` rather than trusting that the generated code looked right on paper.

Layer 7 — large components and page-level patterns — became the first real test of the minimum-viable-baseline philosophy I'd only defined on paper before. `01-greenfield`'s scaffold has no real product area yet, just a placeholder `App.jsx`. Building a page-level pattern here would mean inventing a page with no demonstrated need, exactly what I'd already decided initialization shouldn't do. I chose to record it as a gap in `baseline.json` instead of fabricating an example, and set the outcome to `ready_with_gaps`. This is the behavior the spec describes — `/ticket-agent` is the next decision point that will trigger this layer once a real ticket needs it — but seeing it hold up under an actual run, instead of just reading correctly in the spec, is what makes me trust it.

The completed run: three foundation layers and eight components (Text, Button, Badge, TextInput, Select, Checkbox, Card, Modal) approved and validated, one gap honestly recorded, `outcome: ready_with_gaps`, `baseline validate` and `check-files` both passing, and the app still builds (`npm run build`) after every layer. This is the first fixture to make it through the full `/init-agent` workflow end to end, and it did so with three real implementation bugs found and fixed along the way rather than zero — which is exactly the value of running it instead of just writing it.

## Decisions still to make

The following questions remain open:
- How should overlapping findings be consolidated?
- What fixture suite and measurable targets will define success?
