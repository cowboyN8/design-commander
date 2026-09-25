# PR Pattern Detective — Punch-Out Evidence

A punch-out point is an explicit place where the workflow deliberately stops and refuses to decide on its own — a human must sign off. This is distinct from guardrails (`GUARDRAILS.md`), which are fully automated and involve no judgment call at all. Punch-out points are exactly where judgment calls exist; what makes them qualify for this artifact is that the refusal is **enforced in code**, and that enforcement has been **actively tested by attempting to bypass it**.

## Registered punch-out points

| Point ID | When it fires | Mechanically enforced by |
|---|---|---|
| `stack_confirmed` | Init: framework/styling approach confirmed | `baseline set outcome ready\|ready_with_gaps` refuses without it |
| `accessibility_target_confirmed` | Init: accessibility target confirmed | Same |
| `roadmap_approved` | Init: layer-build roadmap approved | `baseline append foundations`/`components` refuses to add layers without it |
| `extension_approved:<name>` | Ticket: a reusable design-system extension approved | `baseline append components` refuses to add an extension-sourced component without it |
| `blocker_override:<finding-id>` | PR: developer accepts risk instead of fixing a blocker | Auto-recorded by `ticket resolve --status overridden` (which itself requires `--reasons`/`--by`) |
| `reconciliation_decision` | Init: Figma-vs-code conflict resolution (§5.5) | `baseline set dimensions.source_relationship`, `baseline set outcome`, and `baseline append sources` refuse when `source_relationship` is `drifted`/`authority_unclear` without it |

All records are append-only in `.prpd/punchouts.jsonl` (`prpd.py punchout record <point_id> --decision "..." --by "..."`, `prpd.py punchout log` to review).

## Actively tested bypass attempts

Per the requirement that "punch-out points that exist on paper but were never tested do NOT qualify," these were actually attempted, not just designed:

1. **Finalize outcome with zero sign-offs recorded** (an agent trying to skip asking the user entirely) → blocked, both required point IDs named in the error.
2. **Finalize outcome with only one of two required sign-offs** → still blocked, only the missing one named.
3. **Record the second sign-off, retry** → succeeds — proving the gate isn't just always-fail, it's actually checking state.
4. **Add an extension-sourced component with no recorded approval** (an agent building something and self-approving it) → blocked, with the exact command needed to unblock it printed.
5. **Append `foundations` with no recorded roadmap** → blocked.
6. **Set `dimensions.source_relationship` to `drifted` with no recorded reconciliation decision** → blocked.
7. **Set `outcome` to `ready` while `source_relationship` is `drifted` and no reconciliation decision is recorded** → blocked.
8. **Append a `sources` entry while `source_relationship` is `drifted` and no reconciliation decision is recorded** → blocked.

All eight behaved as specified. See `GUARDRAILS.md` for the parallel bypass-testing of the fully-automated gates (a different category — those require no human judgment at all, these do).

## Clear separation: fail workflow (automated) vs. punch-to-human (manual)

- **Fail workflow** = a guardrail gate (`prpd.py guardrail ...`) refusing because a deterministic, code-checkable condition wasn't met (schema invalid, prior gate stale, required field missing). No judgment involved; the same input always produces the same result.
- **Punch to human** = a punch-out point refusing because a *decision* hasn't been made yet — the system genuinely cannot determine the right answer from evidence alone (which styling approach, which source wins a conflict, whether to accept risk instead of fixing something). The block is lifted only by an explicit recorded decision, not by satisfying a mechanical condition.

Both are enforced in code; the difference is what's being checked.

## Known limitations (honest, not swept under the rug)

- The `--by` field is free text supplied by whoever calls the command — there is no identity verification. It records *who claimed* to make the decision, not a cryptographically verified identity. Sufficient for this system's current trust model (local, single-user, company-internal), not sufficient if this were ever multi-tenant.
