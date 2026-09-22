# PR Pattern Detective — Decision Log

This document records confirmed product and architecture decisions. It should be updated as decisions are made during the deep dive.

## Product lifecycle

The system has two stages:

1. Initialize and approve the repository's design-system baseline.
2. Run three review agents against every PR using that project-specific baseline.

The system must remain flexible across repositories. It must not hard-code one application's design conventions or treat generic UX preferences as universal rules.

## Design-system initialization

Initialization runs when the system is first added to a repository. It is a separate workflow from PR review.

Its responsibilities are to:

- Discover available design sources and repository context.
- Validate existing design-system foundations and components.
- Identify inconsistencies, missing coverage, and conflicts between sources.
- Recommend fixes or gap-fillers before approving an incomplete system.
- Ask targeted questions whenever intent cannot be inferred reliably.
- Establish and save an approved, project-specific baseline for future PR reviews.
- Build out a design system with the user when an adequate one does not exist.

When building or completing a system, initialization proceeds from foundations to larger compositions. The expected order begins with typography, color, spacing, and other foundational tokens; continues through small and interactive components; and ends with composite components, large components, and page-level patterns.

AI-generated design decisions do not become authoritative without user approval.

## Dimension-based initialization model

Initialization is selected using a combination of dimensions rather than a fixed list of mutually exclusive paths.

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

The combination of these dimensions determines whether the initializer validates, recommends remediation, fills gaps, reconciles sources, or creates a system with the user.

## Initialization behavior by context

Confirmed contexts include:

- A valid Figma system without a coded implementation: validate Figma and implement the approved system in code.
- An incomplete Figma system: identify gaps, recommend changes, re-check it, and approve it only after it satisfies the agreed criteria.
- Figma and code both exist and agree: validate their mappings and use them as the baseline without rebuilding unnecessarily.
- Figma and code disagree: surface the differences and ask which source represents the intended future state.
- No Figma but an existing coded system: validate and use the coded system as the baseline.
- A partial coded system: preserve valid foundations and work with the user to fill its gaps.
- No Figma or coded system in an existing application: analyze current code, distinguish useful precedent from accidental inconsistency, ask clarifying questions, and create a system with the user.
- A greenfield project with no meaningful source material: create the specification through questions and progressive, user-approved implementation.
- An external design-system dependency: determine what can be changed and establish an application-specific extension layer when necessary.
- Multiple products, themes, or systems: scope each application or directory to the correct baseline.
- An active migration: record the approved current system, deprecated patterns, temporary exceptions, and migration targets.
- Figma is declared but inaccessible: mark initialization as blocked or provisional rather than treating Figma as absent.

Repository frequency alone does not establish correctness. A frequently repeated pattern may still be legacy, accidental, or incorrect.

## Source authority and conflicts

The system may use:

- Approved Figma designs and component systems
- The coded design system
- Design tokens and themes
- Component documentation or Storybook
- Explicit project guidance
- User-approved canonical screens and components
- Comparable established repository patterns
- Rationale supplied with a PR

When Figma and code conflict, the initializer must not silently assume that either source wins. It asks the user whether Figma, code, or a component-by-component decision represents the intended future state, then records that decision in the project baseline.

## Per-PR review agents

### 1. UX Pattern Conformance Analyzer

Reviews compositions rather than isolated primitive styling.

It evaluates groups of components, layouts, workflows, visual and information hierarchy, and page-level patterns against the approved project baseline. It detects unjustified pattern drift, misuse of otherwise valid components, failure to reuse an established pattern, and new patterns introduced without sufficient precedent or rationale.

Core question: **Does this composition create a coherent experience that follows the project's approved patterns?**

### 2. Contextual Accessibility Auditor

Reviews accessibility in the context of each changed implementation.

Approved components reduce risk but do not guarantee accessible usage. This agent checks new and modified components, component configuration and composition, semantic structure, accessible names, keyboard and focus behavior, table relationships, forms, dynamic announcements, and page- or workflow-level accessibility.

It should avoid repeatedly auditing unchanged internals of an already approved component unless the PR affects them.

Core question: **Can people with disabilities successfully use this implementation?**

### 3. Repository Convention Auditor

Reviews project-specific engineering and architectural conventions that require repository context.

It checks shared-component reuse, token usage, file placement, established data and state patterns, component variant conventions, duplicated abstractions, exports, tests, and other approved repository practices.

Generic formatting and mechanically enforceable syntax rules belong in linters, type checking, and deterministic tests rather than this agent.

Core question: **Does this implementation belong in this codebase?**

## Agent boundaries

The three agents may evaluate the same change from different perspectives:

- The UX Pattern Conformance Analyzer asks whether the experience and composition are appropriate.
- The Contextual Accessibility Auditor asks whether the implementation is accessible in context.
- The Repository Convention Auditor asks whether the engineering approach follows repository conventions.

Related findings can be combined later by guardrails, but the agents retain distinct responsibilities.

## Supporting system

### Guardrails

Guardrails validate agent output, apply confidence and reporting policies, prioritize findings, and deduplicate or combine overlapping findings.

### Test runner

The test runner evaluates the system against known good, bad, and ambiguous PR fixtures to measure detection quality and false positives.

## Open decisions

The following have not yet been finalized:

- Exact initialization commands and PR-review invocation syntax
- How Figma access and scanning will be implemented
- The persisted project-profile schema and location
- The criteria required for a design system to pass initialization
- Whether initialization writes application code directly at every layer or proposes changes for separate approval and implementation
- How newly needed components are handled before coding and when detected during PR review
- Whether an unjustified new component blocks a PR or produces a non-blocking recommendation
- Agent output schema, severities, confidence thresholds, and deduplication rules
- Accessibility compliance target
- Fixture suite and measurable success criteria
