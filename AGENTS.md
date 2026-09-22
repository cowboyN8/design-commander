# Project Rules

## Case study maintenance

`case-study.md` is the canonical record of this project's product and implementation journey.

Update `case-study.md` whenever:

- A product, design, architecture, scope, or implementation decision is made or changed.
- A previously open decision is resolved.
- Work begins on an initializer, agent, guardrail, test runner, or other major project stage.
- Implementation results, testing, failures, constraints, or course corrections materially affect the project story.

Write decision-making portions from Nate's first-person perspective. Explain what he decided and why, based only on evidence from the conversation or completed work; do not invent motivations. Preserve meaningful changes in direction so the document captures the journey rather than only the final state.

Keep unresolved matters clearly labeled as open decisions. When one is resolved, update the relevant narrative and remove it from the open list. Treat `case-study.md`, not `decisions.md`, as the authoritative project record.

## Technical specification maintenance

`technical-spec.md` is the normative, living specification for the system.

Every confirmed decision made in chat or during implementation that contributes to the product must update both `case-study.md` and `technical-spec.md` in the same task. This includes product building blocks, features, scope, workflows, interfaces, architecture, data contracts, policies, constraints, and changes to previous decisions.

In `case-study.md`, record the decision and Nate's established reasoning in first person. In `technical-spec.md`, translate the same decision into current normative behavior or requirements. Do not postpone either update until a later summary.

Keep tentative proposals explicitly marked as open rather than presenting them as requirements. When an open decision is resolved, update the relevant sections in both documents and remove it from their open-decision lists. Keep the documents synchronized: the case study explains the journey and reasoning, while the technical specification defines the current required behavior.
