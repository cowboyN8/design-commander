# PR Pattern Detective — End-to-End Success Rate

Per the certification rubric: *"A report showing the end-to-end success rate across the full workflow... the end-to-end number, not just per-step accuracy... if you don't know your end-to-end number, you haven't reached Stage 4."*

## Current number

```
python3 prpd/tools/run_fixture.py --all   # scores everything, appends a trend entry
python3 prpd/tools/run_fixture.py --report  # prints the trend log
```

**As of the last recorded run: 2/2 end-to-end chains passing (100%).**

## What counts as "end-to-end," and why fixture count ≠ chain count

An individual fixture (e.g. `03-pr-manage-users`) only proves one *stage* works. The end-to-end number the rubric asks for is measured over **chains** — a fixture set where init → ticket → PR all operate on the same repo, defined in `prpd/fixtures/chains.json`:

| Chain | Fixtures | Status |
|---|---|---|
| `greenfield-manage-users` | `01-greenfield` → `02-ticket-new-page` → `03-pr-manage-users` | **PASS** |
| `greenfield-landing-page` | `05-landing-init` → `06-landing-ticket` → `07-landing-pr-clean` | **PASS** |

A chain only counts as passing if **every** fixture in it currently passes — one broken link fails the whole chain, not just its own score. This was verified directly: setting `01-greenfield`'s `outcome` to `blocked` (simulating an init regression) correctly dropped the chain result to `0/2 (0%)` when two chains were defined, and correctly returned to `2/2 (100%)` once restored. That's the concrete proof this is measuring the full pipeline, not averaging isolated per-step numbers that could each look fine while the pipeline as a whole is actually broken.

Both chains have been replayed unattended from their initial git refs using `prpd/tools/chain_executor.py` (a deterministic replay of the same prpd.py commands and file operations an agent would perform) without human approval between steps. Results are logged in `prpd/fixtures/chain-runs.jsonl`:

```
$ tail -6 prpd/fixtures/chain-runs.jsonl
{"ts": "2026-09-28T18:25:04.574988+00:00", "chain_id": "greenfield-manage-users", "passed": true, "work_root": "/private/tmp/prpd-revalidated-1-manage"}
{"ts": "2026-09-28T18:25:05.949032+00:00", "chain_id": "greenfield-landing-page", "passed": true, "work_root": "/private/tmp/prpd-revalidated-1-landing"}
{"ts": "2026-09-28T18:25:07.632665+00:00", "chain_id": "greenfield-manage-users", "passed": true, "work_root": "/private/tmp/prpd-revalidated-2-manage"}
{"ts": "2026-09-28T18:25:09.024011+00:00", "chain_id": "greenfield-landing-page", "passed": true, "work_root": "/private/tmp/prpd-revalidated-2-landing"}
{"ts": "2026-09-28T18:25:10.666257+00:00", "chain_id": "greenfield-manage-users", "passed": true, "work_root": "/private/tmp/prpd-revalidated-3-manage"}
{"ts": "2026-09-28T18:25:12.036944+00:00", "chain_id": "greenfield-landing-page", "passed": true, "work_root": "/private/tmp/prpd-revalidated-3-landing"}
```

### Replay evidence re-validated after an executor bug fix

An audit of the certification evidence found the earlier `greenfield-landing-page` replay claims were invalid: `chain_executor.py` hardcoded the `01-greenfield` init fixture for every chain, so the landing chain replayed the manage-users init, never exercised `05-landing-init`, and never verified the landed landing-page implementation (`07-landing-pr-clean` had no `App.jsx` content check, so its clean pass was vacuous). The executor also verified only the committed fixture repos after each stage — not the state each replay actually produced — so "passed" meant "the commands ran," not "the produced state satisfied the fixture."

The fix (2026-09-28): the init fixture is now a per-chain parameter; `05-landing-init` starts from its true scaffold state via a new `initial_ref_repo` fixture field (its own repo path did not exist at its `initial_ref` commit — it was committed directly in final state); the landing PR stage copies the merged `App.jsx`; every stage's **work repo** is scored against its fixture's `expected` block via a new `run_fixture.py --repo-dir` override; and the executor's finding records are now schema-valid. `07-landing-pr-clean` now requires `App.jsx` to contain the landing implementation (`expected_files`), and that check was negative-tested — a scaffold `App.jsx` fails it with the missing markers named. Work-repo scoring also surfaced and fixed two latent defects the committed-repo checks had masked: a nonexistent `tokens.css` path written into the baseline, and schema-violating finding records.

All six replays shown above are post-fix: 3 per chain, every stage's produced work state mechanically verified, no fixes applied during the runs. Pre-fix landing entries in `chain-runs.jsonl` are superseded and not counted toward the rate.

`04-existing-inconsistent` is **not** counted toward the end-to-end rate — it's an init-only fixture with no ticket/PR built on top of it yet, so it hasn't exercised a full chain. It's reported separately so it doesn't inflate the number.

## Finding-accuracy metrics (per-stage recall)

In addition to the end-to-end chain rate, `run_fixture.py` reports finding-accuracy recall for ticket and PR fixtures. Each ticket/PR fixture's `fixture.json` lists `expected_findings` — the known violations the stage should emit — and the runner checks that every expected finding ID is present in `.prpd/tickets.json`, grouped by engine.

**Current finding-accuracy recall:**
- `02-ticket-new-page`: 100% (4/4 expected findings, all engines)
- `03-pr-manage-users`: 100% (12/12 expected findings, all engines, including the adversarial-challenge finding)

Per-engine recall is also reported in `run_fixture.py` output. This satisfies the rubric's "95%+ scores" requirement for the current fixtures; it is not yet a repeated-trial or new-scenario accuracy number.

## Honest limitations (read this before citing "100%" anywhere)

- **Sample size is 2 chains**, with **6 post-fix unattended replays (3 per chain)** whose produced work state passed every fixture's mechanical checks. The replays are deterministic executions in isolated work roots within one runtime session — not independent agent sessions — so the honest claim is "repeated isolated unattended replays with per-stage work-repo verification," not statistical confidence across independent trials. What does demonstrate stability over time is the trend log: the same end-to-end checks have passed on every recorded invocation from 2026-09-24 through 2026-09-28 (30+ trend entries and growing). "100%" here means "both defined chains passed every time they were replayed unattended," not "100% reliability on arbitrary new work." These are not the same claim, and conflating them would misrepresent the number.
- The trend log (`prpd/fixtures/results.jsonl`, viewable via `--report`) has 30+ recorded data points spanning four days, including the pre-fix history, the defect-fix loops, and the post-fix revalidation runs. The set of scenarios is still limited to the 2 hardened chains.
- This measures whether each fixture's **artifacts** meet its `expected` block (`run_fixture.py`'s mechanical checks) — it is not (yet) a measure of whether an agent run *from scratch* against a brand-new, never-before-seen scenario succeeds unattended. Every fixture to date was built and hardened through a manual, human-supervised walkthrough (see `case-study.md`). The number reported here is "does the hardened result still hold across repeated unattended replays," which is the correct and honest thing to measure given the current architecture, but it is a narrower claim than "the agents succeed autonomously N% of the time on new work." That broader claim would require the automated/unattended execution capability discussed as an open item in `technical-spec.md §10`.

## Growing this number honestly

The right way to increase both the numerator and the confidence behind it:
1. Run `run_fixture.py --all` at the start of every future session, before making changes — this is now a zero-cost regression check and directly grows the trend log.
2. Add more chains (new repos/scenarios), not just more standalone fixtures — chain count is what the end-to-end rate is measured over.
3. Eventually, re-run a fixture's underlying scenario from scratch (not just re-check its already-committed artifacts) to get a real repeated-trial number instead of a single hardened result — this is the difference between "it passed once" and an actual success *rate*.
