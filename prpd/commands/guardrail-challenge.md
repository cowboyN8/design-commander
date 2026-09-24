# Guardrail: Adversarial Challenge

This is a guardrail, not a fourth review engine. It runs after `/ticket-agent`
or `/pr-agent` produces a verdict, with a single narrow mandate: **argue
against the prior step's conclusion**. It must be a fresh context with no
visibility into the reviewing agent's reasoning — only its inputs (the
ticket/diff/baseline) and its outputs (the verdict and findings) — so it
can't simply agree with itself. This is what makes it "automated adversarial
review" rather than a second human manually re-reading the same review.

## Inputs

- The baseline (`.prpd/baseline.json`) and ticket record (`.prpd/tickets.json`)
- The diff or ticket content under review
- The prior verdict and finding list, presented as a claim to be tested, not
  as ground truth

## Mandate

Try to do one or more of the following. Finding nothing is a valid, useful
result — it is not required to invent a problem.

1. **Find a missed violation**: something in the diff/ticket that should have
   been a blocker or advisory finding but wasn't emitted at all.
2. **Challenge a severity call**: argue a finding should have been a blocker
   instead of advisory, or vice versa.
3. **Challenge traceability**: argue something marked `traceability: baseline`
   or `extension` doesn't actually match what was approved.
4. **Challenge the verdict itself**: argue the pass/fail computation is wrong
   given the recorded finding statuses.

## Output

Report each challenge as `{"agrees": true|false, "claim": "...", "evidence":
"..."}`. Do not modify `tickets.json` directly — if a challenge succeeds
(the reviewing agent missed something real), it becomes a new finding added
the normal way (`ticket upsert`), tagged `--step guardrail.challenge`, so it's
distinguishable in the audit trail from findings the original engines caught
on their own. A challenge that fails to find anything is still recorded via
`prpd.py audit challenge_run --note "..."` so the check is auditable even
when it produces no new finding.

## Automation note

This must be run as a separate, isolated agent invocation (fresh context) —
not a second pass by the same agent instance that produced the verdict being
challenged, and not a human manually re-reviewing. A human re-review of this
kind is Stage 2 behavior; an independent automated pass with no memory of
the original reasoning is what makes this a guardrail.
