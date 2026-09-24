# PR Pattern Detective — End-to-End Success Rate

Per the certification rubric: *"A report showing the end-to-end success rate across the full workflow... the end-to-end number, not just per-step accuracy... if you don't know your end-to-end number, you haven't reached Stage 4."*

## Current number

```
python3 prpd/tools/run_fixture.py --all   # scores everything, appends a trend entry
python3 prpd/tools/run_fixture.py --report  # prints the trend log
```

**As of the last recorded run: 1/1 end-to-end chains passing (100%).**

## What counts as "end-to-end," and why fixture count ≠ chain count

An individual fixture (e.g. `03-pr-manage-users`) only proves one *stage* works. The end-to-end number the rubric asks for is measured over **chains** — a fixture set where init → ticket → PR all operate on the same repo, defined in `prpd/fixtures/chains.json`:

| Chain | Fixtures | Status |
|---|---|---|
| `greenfield-manage-users` | `01-greenfield` → `02-ticket-new-page` → `03-pr-manage-users` | **PASS** |

A chain only counts as passing if **every** fixture in it currently passes — one broken link fails the whole chain, not just its own score. This was verified directly: setting `01-greenfield`'s `outcome` to `blocked` (simulating an init regression) correctly dropped the chain result to `0/1 (0%)`, and correctly returned to `1/1 (100%)` once restored. That's the concrete proof this is measuring the full pipeline, not averaging isolated per-step numbers that could each look fine while the pipeline as a whole is actually broken.

`04-existing-inconsistent` is **not** counted toward the end-to-end rate — it's an init-only fixture with no ticket/PR built on top of it yet, so it hasn't exercised a full chain. It's reported separately so it doesn't inflate the number.

## Honest limitations (read this before citing "100%" anywhere)

- **Sample size is 1 chain**, and each chain has been executed exactly once per fixture-build session, not repeated as independent statistical trials. "100%" here means "the one chain that exists currently passes," not "100% reliability across many attempts." These are not the same claim, and conflating them would misrepresent the number.
- The trend log (`prpd/fixtures/results.jsonl`, viewable via `--report`) currently has 2 data points, both from the same session, both reflecting the same underlying state (one right after the certification work, one after a cleanup pass). Real trend evidence — "stable or improving over time" — requires this to be run repeatedly across genuinely separate future sessions as the codebase changes, not backfilled with fabricated historical timestamps. It will accumulate honestly from here.
- This measures whether each fixture's **artifacts** meet its `expected` block (`run_fixture.py`'s mechanical checks) — it is not (yet) a measure of whether an agent run *from scratch* against a brand-new, never-before-seen scenario succeeds unattended. Every fixture to date was built and hardened through a manual, human-supervised walkthrough (see `case-study.md`). The number reported here is "does the hardened result still hold," which is the correct and honest thing to measure given the current architecture, but it is a narrower claim than "the agents succeed autonomously N% of the time on new work." That broader claim would require the automated/unattended execution capability discussed as an open item in `technical-spec.md §10`.

## Growing this number honestly

The right way to increase both the numerator and the confidence behind it:
1. Run `run_fixture.py --all` at the start of every future session, before making changes — this is now a zero-cost regression check and directly grows the trend log.
2. Add more chains (new repos/scenarios), not just more standalone fixtures — chain count is what the end-to-end rate is measured over.
3. Eventually, re-run a fixture's underlying scenario from scratch (not just re-check its already-committed artifacts) to get a real repeated-trial number instead of a single hardened result — this is the difference between "it passed once" and an actual success *rate*.
