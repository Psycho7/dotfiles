"""Tests for the Claude settings merge (home/dot_claude/modify_private_settings.json).

The merge reads the existing settings.json on stdin and writes the merged
document on stdout, so every case is a pipe. Assertions are jq filters run
with `jq -e`.
"""

import json
import subprocess
from pathlib import Path

import pytest

MERGE = Path(__file__).resolve().parents[2] / "home" / "dot_claude" / "modify_private_settings.json"

# An existing settings.json with a hook the user added (must survive) and a
# stale copy of one of ours (must be replaced, not duplicated).
EXISTING = {
    "userSetting": "keep me",
    "hooks": {
        "PreToolUse": [
            {"matcher": "Bash", "hooks": [{"type": "command", "command": '"$HOME/bin/user-hook.sh"', "timeout": 5}]},
        ],
        "SubagentStart": [
            {"matcher": "rikki|sakichan", "hooks": [{"type": "command", "command": '"$HOME/.claude/hooks/mygo-subagent-context.fish"', "timeout": 60}]},
            {"matcher": "tomorin", "hooks": [{"type": "command", "command": '"$HOME/bin/user-subagent.sh"', "timeout": 5}]},
        ],
    },
}

# A settings.json written by the previous version of the merge, where the
# user has also edited our entries in place: the two stale "if"-filtered
# mygo-dispatch-guard handlers (one carrying a custom field), an extra handler
# inside our matcher "Agent" entry, unknown fields on the entry, a stale
# timeout, and a Stop handler with no command key at all.
CUSTOMIZED = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Agent",
                "note": "hand-edited",
                "hooks": [
                    {"type": "command", "if": "Agent(rikki)", "command": '"$HOME/.claude/hooks/mygo-dispatch-guard.fish"', "timeout": 60, "customField": "keep me"},
                    {"type": "command", "if": "Agent(sakichan)", "command": '"$HOME/.claude/hooks/mygo-dispatch-guard.fish"', "timeout": 60},
                    {"type": "command", "command": '"$HOME/bin/my-agent-audit.sh"'},
                ],
            },
        ],
        "Stop": [
            {"hooks": [{"type": "prompt", "prompt": "no command key here"}]},
        ],
    },
}

# Handlers under the pre-rename names: the ones in .claude/hooks/ are ours
# and must go; a user script that shares a retired basename elsewhere, a
# user handler beside them and a command-less handler must stay.
RETIRED = {
    "hooks": {
        "PreToolUse": [
            {
                "matcher": "Agent",
                "hooks": [
                    {"type": "command", "command": '"$HOME/.claude/hooks/dispatch-guard.fish"', "timeout": 60},
                    {"type": "command", "command": '"$HOME/bin/my-agent-audit.sh"'},
                ],
            },
        ],
        "SubagentStop": [
            {
                "hooks": [
                    {"type": "command", "command": '"$HOME/.claude/hooks/subagent-done.fish"', "timeout": 60},
                    {"type": "command", "command": '"$HOME/bin/subagent-done.fish"', "timeout": 5},
                ],
            },
        ],
        "Stop": [
            {
                "hooks": [
                    {"type": "command", "command": '"$HOME/.claude/hooks/verification-gate.fish"', "timeout": 60},
                    {"type": "prompt", "prompt": "no command key here"},
                ],
            },
        ],
    },
}


def merge(settings: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["bash", str(MERGE)], input=settings, capture_output=True, text=True)


@pytest.fixture(scope="module")
def empty_out() -> str:
    return merge("{}\n").stdout


@pytest.fixture(scope="module")
def merged() -> str:
    return merge(json.dumps(EXISTING)).stdout


@pytest.fixture(scope="module")
def customized() -> subprocess.CompletedProcess[str]:
    return merge(json.dumps(CUSTOMIZED))


@pytest.fixture(scope="module")
def customized_out(customized: subprocess.CompletedProcess[str]) -> str:
    return customized.stdout


@pytest.fixture(scope="module")
def retired_out() -> str:
    return merge(json.dumps(RETIRED)).stdout


CHECKS = [
    ("empty input: PreToolUse has one unfiltered mygo-dispatch-guard handler", "empty_out",
     '''[.hooks.PreToolUse[] | select(.matcher == "Agent") | .hooks[]] | length == 1
     and (.[0].command | test("mygo-dispatch-guard.fish"))
     and (.[0] | has("if") | not)
     and (.[0].timeout == 10)'''),
    ("empty input: SubagentStart entry present once", "empty_out",
     '[.hooks.SubagentStart[] | select(.hooks[].command | test("mygo-subagent-context.fish"))] | length == 1'),
    ("empty input: SubagentStart has our two entries, one handler each", "empty_out",
     '''(.hooks.SubagentStart | length) == 2
     and (.hooks.SubagentStart | map(.matcher) == ["rikki|sakichan", "rikki"])
     and (.hooks.SubagentStart | all(.hooks | length == 1))'''),
    ("empty input: SubagentStart matcher rikki runs mygo-subagent-resumed", "empty_out",
     '''[.hooks.SubagentStart[] | select(.matcher == "rikki") | .hooks[]]
     | length == 1
     and (.[0].command | test("mygo-subagent-resumed.fish"))
     and (.[0].timeout == 10)'''),
    ("empty input: SubagentStop entry present once", "empty_out",
     '[.hooks.SubagentStop[] | select(.hooks[].command | test("mygo-subagent-done.fish"))] | length == 1'),
    ("empty input: Stop entry present once with no matcher", "empty_out",
     '''[.hooks.Stop[] | select(.hooks[].command | test("mygo-verification-gate.fish"))]
     | length == 1 and (.[0] | has("matcher") | not)'''),
    ("empty input: every managed handler has timeout 10", "empty_out",
     r'''[.hooks | to_entries[] | .value[] | .hooks[] | select(.command | test("\\.claude/hooks/"))
      | .timeout] | length == 5 and all(. == 10)'''),
    ("merge keeps unknown top-level fields", "merged", '.userSetting == "keep me"'),
    ("merge keeps the unrelated PreToolUse hook", "merged",
     '''[.hooks.PreToolUse[] | select(.matcher == "Bash")
      | .hooks[] | select(.command | test("user-hook.sh")) | select(.timeout == 5)] | length == 1'''),
    ("merge appends our PreToolUse entry alongside it", "merged", '(.hooks.PreToolUse | length) == 2'),
    ("merge replaces the stale SubagentStart entry", "merged",
     '''[.hooks.SubagentStart[] | select(.matcher == "rikki|sakichan")]
     | length == 1 and (.[0].hooks | length) == 1 and (.[0].hooks[0].timeout == 10)'''),
    ("merge keeps the user SubagentStart entry and appends ours", "merged",
     '''(.hooks.SubagentStart | length) == 3
     and ([.hooks.SubagentStart[] | select(.matcher == "tomorin")
           | .hooks[] | select(.command | test("user-subagent.sh")) | select(.timeout == 5)] | length == 1)
     and ([.hooks.SubagentStart[] | select(.matcher == "rikki")
           | .hooks[] | select(.command | test("mygo-subagent-resumed.fish"))] | length == 1)'''),
    ("merge adds SubagentStop and Stop to an existing hooks object", "merged",
     '(.hooks.SubagentStop | length) == 1 and (.hooks.Stop | length) == 1'),
    ("merge leaves exactly one entry per managed hook script", "merged",
     r'''[.hooks | to_entries[] | .value[] | .hooks[] | .command
      | select(test("\\.claude/hooks/")) | split("/") | last | sub("\"$"; "")]
     | (length == 5)
     and (map(select(. == "mygo-dispatch-guard.fish")) | length) == 1
     and (map(select(. == "mygo-subagent-context.fish")) | length) == 1
     and (map(select(. == "mygo-subagent-resumed.fish")) | length) == 1
     and (map(select(. == "mygo-subagent-done.fish")) | length) == 1
     and (map(select(. == "mygo-verification-gate.fish")) | length) == 1'''),
    ("merge keeps a user handler inside our entry", "customized_out",
     '''[.hooks.PreToolUse[] | select(.matcher == "Agent") | .hooks[]
      | select(.command? // "" | test("my-agent-audit.sh"))] | length == 1'''),
    ("merge keeps unknown fields on our entry", "customized_out",
     '[.hooks.PreToolUse[] | select(.matcher == "Agent") | select(.note == "hand-edited")] | length == 1'),
    ("merge collapses the stale if-filtered mygo-dispatch-guard handlers into one", "customized_out",
     '''[.hooks.PreToolUse[] | select(.matcher == "Agent") | .hooks[]
      | select(.command? // "" | test("mygo-dispatch-guard.fish"))] | length == 1'''),
    ("merge drops the stale if filter from our handler", "customized_out",
     '''[.hooks.PreToolUse[] | select(.matcher == "Agent") | .hooks[]
      | select(.command? // "" | test("mygo-dispatch-guard.fish"))
      | select(has("if") | not)] | length == 1'''),
    ("merge keeps unknown fields on our handler", "customized_out",
     '''[.hooks.PreToolUse[] | select(.matcher == "Agent") | .hooks[]
      | select(.command? // "" | test("mygo-dispatch-guard.fish"))
      | select(.customField == "keep me")] | length == 1'''),
    ("merge updates the stale timeout on our handler", "customized_out",
     '''[.hooks.PreToolUse[] | select(.matcher == "Agent") | .hooks[]
      | select(.command? // "" | test("mygo-dispatch-guard.fish"))
      | select(.timeout == 10)] | length == 1'''),
    ("merge keeps the command-less Stop handler", "customized_out",
     '[.hooks.Stop[] | .hooks[] | select(.prompt? == "no command key here")] | length == 1'),
    # The command-less Stop entry is not one of ours, so ours is appended beside it.
    ("merge appends our Stop entry beside the unrelated one", "customized_out",
     '''(.hooks.Stop | length) == 2 and
     ([.hooks.Stop[] | .hooks[] | select(.command? // "" | test("mygo-verification-gate.fish"))] | length == 1)'''),
    ("merge drops retired handlers under .claude/hooks, keeps user and command-less ones", "retired_out",
     r'''([.hooks[][] | .hooks[] | .command? | strings
       | select(test("\\.claude/hooks/(dispatch-guard|subagent-done|verification-gate)\\.fish"))]
      | length == 0)
     and ([.hooks.PreToolUse[] | .hooks[] | select(.command? // "" | test("my-agent-audit.sh"))] | length == 1)
     and ([.hooks.Stop[] | .hooks[] | select(.prompt? == "no command key here")] | length == 1)'''),
    ("merge keeps a user handler that shares a retired basename", "retired_out",
     '''[.hooks.SubagentStop[] | .hooks[] | select(.command? == "\\"$HOME/bin/subagent-done.fish\\"")
      | select(.timeout == 5)] | length == 1'''),
]


@pytest.mark.parametrize(("output", "jq_filter"), [c[1:] for c in CHECKS], ids=[c[0] for c in CHECKS])
def test_check(request: pytest.FixtureRequest, output: str, jq_filter: str) -> None:
    document = request.getfixturevalue(output)
    result = subprocess.run(["jq", "-e", jq_filter], input=document, capture_output=True, text=True)
    assert result.returncode == 0, f"jq -e failed ({result.returncode}): {result.stderr}\n{document}"


def test_merge_survives_a_handler_with_no_command_key(customized: subprocess.CompletedProcess[str]) -> None:
    assert customized.returncode == 0, customized.stderr


@pytest.mark.parametrize(
    "output",
    ["customized_out", "merged", "empty_out", "retired_out"],
    ids=[
        "merge is idempotent on a hand-edited settings file",
        "merge is idempotent on its own output",
        "merge is idempotent on empty input output",
        "merge is idempotent on retired handler output",
    ],
)
def test_idempotent(request: pytest.FixtureRequest, output: str) -> None:
    first = request.getfixturevalue(output)
    assert merge(first).stdout == first
