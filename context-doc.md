Stage 4 Project: PR Pattern Detective — DEEP DIVE WORKSHEET

Goal: Work through this system layer by layer so Nate becomes the expert on his own design.

Approach: Don't hand you a complete spec. Instead, we'll deep-dive into each agent one at a time, answer hard questions, build real examples, and you'll write the actual requirements.

How to use this: Paste this into Devin chat and say: "Let's work through this together. I want to understand every part of this system deeply before we build it. Start with Agent 1."

CONTEXT (For Devin)

Who I am: Nate Short, Design Engineer based in Atlanta. 5+ years in design systems, front-end, accessibility.

Why this system: On my last project, a non-developer teammate and prompt-engineers shipped code with terrible UX patterns and a11y regressions. Other developers didn't catch it because there was no systematic review gate. This system automates that gate.

What we're building: A multi-agent PR reviewer (three agents + guardrails + test runner) that flags bad patterns before merge. Local only, company project.

My role in building this: I want to be the brain. I'm going to understand every piece deeply, answer the hard questions, provide the real examples. Then we'll build it together.

PHASE 1: AGENT 1 DEEP DIVE — PATTERN ANALYZER

What this agent does: Reviews a PR diff and identifies UX anti-patterns that violate your established design conventions.

Step 1: Identify Your Real Anti-Patterns

Start here. Don't give me generic examples. Think about your last project.

Questions:

What are the 3-5 UX anti-patterns you saw that made you mad?
Example from your last project: "The non-developer added a button with no hover state, making it look disabled"
What was wrong with it? Why did it matter?
Give me at least 3-5 specific, real examples.
For each anti-pattern, define it clearly:
Name: What do you call this problem?
Why it's bad: What user experience suffers?
How to fix it: What's the right way?
How an agent would spot it: What would the agent look for in code?
Step 2: Good vs Bad Examples

For each anti-pattern, create two real code examples:

Bad example (violates pattern):

Show actual React/TSX code
Be specific (actual component, actual mistakes)
Explain why this is wrong

Good example (follows pattern):

Show how the same component should be built
Follows your conventions
Explain why this is right
Step 3: Agent Instructions

Once you define the patterns and examples, we'll write the agent prompt (pattern-analyzer.md).

The agent needs:

Clear definition of each pattern
Examples of good vs bad
How to recognize violations in code
Output format (what it should return when it finds a violation)
PHASE 2: AGENT 2 DEEP DIVE — ACCESSIBILITY AUDITOR

What this agent does: Scans PR diffs for a11y regressions and issues.

Step 1: Your A11y Baseline

Questions:

What's your target compliance? (WCAG 2.1 AA? AAA?)
What a11y issues came up most on your last project?
Missing alt text?
Missing ARIA labels?
Color contrast problems?
Form validation not announced?
Other?
Of those, which ones hurt users the most?
Which ones are easiest to miss in code review?
Step 2: Specific A11y Rules

For each issue type you want to catch, define:

What it is: Clear description
Why it matters: Real impact on users
How to spot it in code: What would indicate the violation?
How to fix it: What's the right approach?
Step 3: Examples

Bad a11y example:

Show code that violates your a11y standards
Explain what's missing or wrong

Good a11y example:

Show how the same code should be written
Explain why it's accessible
PHASE 3: AGENT 3 DEEP DIVE — CONSISTENCY CHECKER

What this agent does: Flags when code doesn't match your codebase conventions and patterns.

Step 1: Define Your Consistency Rules

Questions:

What defines "consistent code" in your world?
Naming conventions? (ButtonPrimary vs PrimaryButton?)
How components are structured?
State management approach?
File organization?
Hook usage patterns?
Other?
Which 3-5 consistency rules are non-negotiable?
If a new developer broke one, you'd catch it immediately
Things that matter across every component
For each rule, define:
The rule: What's expected?
Why it matters: Why does consistency here matter?
How to spot violations: What does bad code look like?
Real example of violation: Show code that breaks the rule
Real example of compliance: Show code that follows it
Step 2: Edge Cases

Are there exceptions to your consistency rules?

Times when it's okay to break convention?
How would an agent know the difference?
PHASE 4: GUARDRAILS DEEP DIVE

What guardrails do: Validate agent output, filter by confidence, deduplicate findings.

Step 1: Output Validation

Question: What counts as a "valid" agent response?

For each agent finding, it should include:

Issue title
Severity (critical, high, medium, low?)
Location (file, line number)
Description (what's wrong)
Actionable fix (how to correct it)
Confidence (how sure is the agent?)

Your task: Define what fields are required. What's optional? What does the output look like?

Step 2: Confidence Threshold

Questions:

How confident must an agent be before flagging something?
95% confidence = catch fewer issues, fewer false positives
70% confidence = catch more, but more false positives
50% confidence = catch everything, lots of noise
Should different agents have different thresholds?
Maybe a11y issues require 95% confidence (safer than UX patterns)
Maybe pattern issues can be 75% (more subjective)
Maybe consistency checks need 85% (pretty clear-cut)
When confidence is below threshold, what should happen?
Mark as "review required"?
Skip it entirely?
Both (flag separately)?
Step 3: Deduplication

Questions:

If all three agents flag the same issue, how should it appear?
As one finding or three?
How do you prioritize severity?
How do you avoid overwhelming the reviewer?
If two agents disagree about an issue, which wins?
Majority rules?
Depends on severity?
Both get reported?
PHASE 5: FIXTURES DEEP DIVE

What fixtures are: Fake PR diffs that represent real scenarios (bad patterns, good patterns, edge cases).

Step 1: Bad PR Scenarios

Create 3-5 realistic "bad" PRs that represent your actual problems:

For each bad PR:

Show the code change (as a simplified diff)
What's wrong with it?
Which agent(s) should catch it?
Why is this realistic to your last project?
Step 2: Good PR Scenarios

Create 2-3 realistic "good" PRs that should pass all checks:

For each good PR:

Show the code change
Why is this correct?
Why should all agents pass it?
Step 3: Edge Cases

Create 1-2 tricky PRs:

For each edge case:

What makes it ambiguous?
Should it pass or fail?
Why?
PHASE 6: SUCCESS CRITERIA

Once you've defined everything above, we need to agree on:

Accuracy target: What % of bad patterns must the system catch?
80%? 90%? 95%?
False positive rate: How many good PRs is it okay to wrongly flag?
1 in 10? 1 in 20? 1 in 100?
What "done" means:
When do we stop iterating and call it complete?
What proof do we need?
