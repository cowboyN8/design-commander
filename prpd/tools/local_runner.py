#!/usr/bin/env python3
"""Local Devin unattended fixture runner.

Prepares an isolated work directory for a fixture and emits a replay prompt
that a Devin agent (this assistant or a subagent) can execute without human
intervention. All user answers come from the fixture's `user_simulation` block.

This stays fully inside the Devin/local runtime — no external APIs.

Usage:
    python3 prpd/tools/local_runner.py \
        --agent init-agent \
        --fixture prpd/fixtures/01-greenfield \
        --work-dir /tmp/prpd-run-01

Output: a replay prompt file at <work-dir>/REPLAY.md plus a one-line command
summary. The replay prompt tells the executing agent exactly which files to
read, which answers to use, and how to verify the result.

For a chain, run the stages in order into adjacent work directories and use
--previous-work-dir to point the next stage at the repo produced by the prior
stage. Example:

    python3 prpd/tools/local_runner.py --agent init-agent \
        --fixture prpd/fixtures/01-greenfield --work-dir /tmp/prpd-chain/init
    # (execute replay)
    python3 prpd/tools/local_runner.py --agent ticket-agent \
        --fixture prpd/fixtures/02-ticket-new-page \
        --work-dir /tmp/prpd-chain/ticket \
        --previous-work-dir /tmp/prpd-chain/init/repo
    # (execute replay)
"""

import argparse
import io
import json
import shutil
import subprocess as sp
import sys
import tarfile
from pathlib import Path

TOOLS_DIR = Path(__file__).resolve().parent
REPO_ROOT = TOOLS_DIR.parent.parent
COMMANDS_DIR = TOOLS_DIR.parent / "commands"
RUN_FIXTURE_PY = TOOLS_DIR / "run_fixture.py"


def load_json(path: Path) -> dict:
    return json.loads(path.read_text())


def _extract_repo_at_ref(src_repo: Path, dest_repo: Path, ref: str) -> None:
    """Extract the contents of src_repo as it existed at git ref into dest_repo."""
    rel = src_repo.relative_to(REPO_ROOT).as_posix()
    proc = sp.run(
        ["git", "-C", str(REPO_ROOT), "archive", ref, f"{rel}/"],
        stdout=sp.PIPE, check=True,
    )
    dest_repo.mkdir(parents=True, exist_ok=True)
    prefix = rel + "/"
    # Buffer the archive in memory so tarfile can seek member contents.
    archive = io.BytesIO(proc.stdout)
    with tarfile.open(fileobj=archive, mode="r:") as tar:
        for member in tar.getmembers():
            if member.name.startswith(prefix):
                member.name = member.name[len(prefix):]
                tar.extract(member, dest_repo)


def setup_work_dir(fixture_dir: Path, work_dir: Path, previous_repo: Path = None) -> Path:
    """Create an isolated work directory with a copy of the target repo.

    For non-init fixtures the target repo is the `target_repo` of the fixture,
    which normally points at a sibling fixture's repo. We resolve it relative
    to the fixture directory. If --previous-work-dir is given, we copy from
    there instead, allowing chains.

    If the fixture declares `initial_ref`, the work repo is extracted from
    that git commit so the agent starts from the fixture's initial state rather
    than its committed final state. `initial_ref_repo` optionally names a
    different repo directory (relative to the fixture dir) to extract at that
    ref -- for fixtures whose own repo path did not exist at the ref (e.g.
    05-landing-init, whose starting state is 01-greenfield's scaffold).
    """
    fixture = load_json(fixture_dir / "fixture.json")
    work_dir = Path(work_dir).resolve()
    work_dir.mkdir(parents=True, exist_ok=True)

    if previous_repo:
        src_repo = Path(previous_repo).resolve()
    elif fixture.get("target_repo"):
        src_repo = (fixture_dir / fixture["target_repo"]).resolve()
    else:
        src_repo = fixture_dir / "repo"

    if not src_repo.is_dir():
        raise FileNotFoundError(f"source repo not found: {src_repo}")

    dest_repo = work_dir / "repo"
    if dest_repo.exists():
        shutil.rmtree(dest_repo)

    ref = fixture.get("initial_ref")
    if ref and not previous_repo:
        ref_repo = fixture.get("initial_ref_repo")
        extract_src = (fixture_dir / ref_repo).resolve() if ref_repo else src_repo
        _extract_repo_at_ref(extract_src, dest_repo, ref)
    else:
        shutil.copytree(src_repo, dest_repo)

    return dest_repo


def build_replay_prompt(agent: str, fixture_dir: Path, work_dir: Path, dest_repo: Path) -> str:
    fixture = load_json(fixture_dir / "fixture.json")
    prompt_path = COMMANDS_DIR / f"{agent}.md"
    if not prompt_path.is_file():
        raise FileNotFoundError(f"agent prompt not found: {prompt_path}")

    user_sim = fixture.get("user_simulation", {})
    user_sim_json = json.dumps(user_sim, indent=2) if user_sim else "(none provided)"

    parts = [
        f"# Unattended replay: /{agent} on {fixture['id']}",
        "",
        "Execute this agent against a fixture in **unattended** mode. Do not pause for human input.",
        "Use the user-simulation answers below whenever the agent prompt asks a question.",
        "",
        "## Work directory",
        f"`{work_dir}`",
        f"The target repo is at: `{dest_repo}`",
        "",
        "## Agent prompt to follow",
        f"Read and follow exactly: `{prompt_path}`",
        "",
        "## Fixture context",
        f"- Fixture ID: `{fixture['id']}`",
        f"- Stage: `{fixture['stage']}`",
        f"- Description: {fixture.get('description', '')}",
    ]

    if "ticket" in fixture:
        parts.extend([
            "",
            "### Simulated ticket",
            "```json",
            json.dumps(fixture["ticket"], indent=2),
            "```",
        ])
    if "pr" in fixture:
        parts.extend([
            "",
            "### Simulated PR",
            "```json",
            json.dumps(fixture["pr"], indent=2),
            "```",
        ])

    parts.extend([
        "",
        "## User-simulation answers",
        "Use these answers whenever the agent prompt asks a user question. Do not ask the user.",
        "```json",
        user_sim_json,
        "```",
        "",
        "## Execution rules",
        "1. Run all `prpd.py` commands against the repo directory above (`--repo-dir <repo-path>`).",
        "2. When a punch-out point is required, record it with `prpd.py punchout record ... --by unattended-runner`.",
        "3. When a guardrail gate is required, run `prpd.py guardrail ...` first.",
        "4. If the agent prompt asks a clarifying question, answer it using the user-simulation block above.",
        "5. After completing the agent work, verify by running the mechanical checker:",
        f"   python3 {RUN_FIXTURE_PY} {fixture_dir}",
        "6. Report the final pass/fail result and any notable deviations from the expected fixture state.",
    ])

    return "\n".join(parts)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--agent", required=True, help="agent command name, e.g. init-agent, ticket-agent, pr-agent")
    parser.add_argument("--fixture", required=True, type=Path, help="path to fixture directory containing fixture.json")
    parser.add_argument("--work-dir", required=True, type=Path, help="path to create as the isolated work directory")
    parser.add_argument("--previous-work-dir", type=Path, default=None, help="copy repo from this prior stage's work-dir/repo instead of the fixture's target_repo")
    args = parser.parse_args()

    fixture_dir = args.fixture.resolve()
    if not (fixture_dir / "fixture.json").is_file():
        print(f"error: no fixture.json in {fixture_dir}", file=sys.stderr)
        sys.exit(2)

    previous_repo = None
    if args.previous_work_dir:
        previous_repo = Path(args.previous_work_dir).resolve() / "repo"

    dest_repo = setup_work_dir(fixture_dir, args.work_dir, previous_repo)
    replay = build_replay_prompt(args.agent, fixture_dir, args.work_dir.resolve(), dest_repo)
    # Record the starting git ref in the work dir for the report.
    ref = load_json(fixture_dir / "fixture.json").get("initial_ref", "(current)")
    replay = replay.replace(
        "## Work directory",
        f"## Starting state\n\nThis replay begins from git ref `{ref}`.\n\n## Work directory"
    )
    replay_path = args.work_dir.resolve() / "REPLAY.md"
    replay_path.write_text(replay)

    print(f"Prepared work directory: {args.work_dir.resolve()}")
    print(f"Target repo:              {dest_repo}")
    print(f"Replay prompt:             {replay_path}")
    print(f"Next step: execute the replay prompt in a Devin agent (or subagent) against {dest_repo}")


if __name__ == "__main__":
    main()
