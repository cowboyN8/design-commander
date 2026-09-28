# Stage 4 Final Steps — Session Checklist

Run this checklist in **3 separate Devin sessions**. Each session is independent; close the previous one before starting the next.

## Per-session steps

1. **Open this repo in a new Devin session.**
   ```bash
   cd /Users/short_000/NateShortStage4
   ```

2. **Run both chains unattended.** Replace `N` with the session number (1, 2, or 3).
   ```bash
   python3 prpd/tools/chain_executor.py --chain greenfield-manage-users --work-root /tmp/prpd-session-N-manage
   python3 prpd/tools/chain_executor.py --chain greenfield-landing-page --work-root /tmp/prpd-session-N-landing
   ```
   Both should end with `All three stages passed.`

3. **Verify committed fixtures still pass.**
   ```bash
   python3 prpd/tools/run_fixture.py --all
   ```
   Expected result: `7/7 fixture(s) fully passed` and `2/2 chains (100%)`.

4. **Commit the updated logs.**
   ```bash
   git add prpd/fixtures/chain-runs.jsonl prpd/fixtures/results.jsonl
   git commit -m "Unattended chain replays session N"
   ```

5. **Close this Devin session.** Do not keep it open for the next session.

## If a run fails

- Fix the root cause in the prompts or tooling.
- **Restart the count from session 1.** A failure means the "no manual correction" claim is not yet proven.

## After all 3 sessions succeed

1. **Open `AUDIT_TRAIL.md`** and add this note near the top:
   > Per-step `tokens_in`, `tokens_out`, and `cost_usd` are intentionally null because Devin's local agent runtime does not expose per-call token counts or cost. Fabricating values would break audit integrity. The schema supports these fields if a future runtime provides them.

2. **Open `RUBRIC_TRACKING.md`** and update:
   - Audit Trail → Per-step token/cost data: change `[ ]` to `[~]` with note "Devin runtime limitation; documented as out of scope."
   - Stage 3 Evaluations → Mid-tier model: change `[~]` note to "Cannot be verified inside Devin's routing layer; accepted as runtime limitation."
   - Bottom line: mark Stage 4 as Done `[x]`, citing 3 separate sessions and 2 chains passing.

3. Run one final verification:
   ```bash
   python3 prpd/tools/run_fixture.py --all
   ```

4. Commit the documentation updates.

## Goal

`prpd/fixtures/chain-runs.jsonl` contains at least 3 successful separate-session entries for each chain, with no failures or fixes during the runs.
