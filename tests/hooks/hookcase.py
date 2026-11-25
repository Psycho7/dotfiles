"""Fixture builders, marker readers and assertions for the gate hook tests."""

import json
import re
from collections.abc import Callable
from pathlib import Path

HOOKS = Path(__file__).resolve().parents[2] / "home" / "dot_claude" / "hooks"
GUARD = HOOKS / "executable_mygo-dispatch-guard.fish"
DONE_HOOK = HOOKS / "executable_mygo-subagent-done.fish"
GATE = HOOKS / "executable_mygo-verification-gate.fish"
RESUMED = HOOKS / "executable_mygo-subagent-resumed.fish"
GIT_GUARD = HOOKS / "executable_git-guard.fish"

SESSION_ID = "test-session"
NOCOMMIT = "a" * 40


def guard_input(agent: str, prompt: str, cwd: Path) -> str:
    return json.dumps({
        "tool_name": "Agent",
        "tool_input": {"subagent_type": agent, "prompt": prompt},
        "cwd": str(cwd),
        "session_id": SESSION_ID,
    })


def stop_input(agent: str, msg: str, agent_id: str) -> str:
    return json.dumps({
        "agent_id": agent_id,
        "agent_type": agent,
        "last_assistant_message": msg,
        "stop_hook_active": False,
        "session_id": SESSION_ID,
    })


def start_input(agent: str, agent_id: str) -> str:
    return json.dumps({"agent_id": agent_id, "agent_type": agent, "session_id": SESSION_ID})


def gate_input(active: bool = False) -> str:
    return json.dumps({"stop_hook_active": active, "session_id": SESSION_ID})


def bash_input(command: str) -> str:
    return json.dumps({"tool_name": "Bash", "tool_input": {"command": command}})


def fenced(*lines: str) -> str:
    return "\n".join(["Task text for the subagent.", "```yaml", *lines, "```", "Trailing prose."])


def rikki_envelope(cwd: Path, report: Path) -> str:
    return fenced(
        "dispatch:",
        f"  cwd: {cwd}",
        "  branch: main",
        f"  report: {report}",
        "  criteria:",
        "    - the hook denies a bad envelope",
        "  verify: uv run pytest",
    )


def sakichan_envelope(cwd: Path, report: Path) -> str:
    return fenced(
        "dispatch:",
        f"  cwd: {cwd}",
        f"  report: {report}",
        "  criteria:",
        "    - the hook denies a bad envelope",
    )


def write_report(path: Path, status: str, base: str, *, after: bool = True) -> None:
    tests = [
        "  - phase: before",
        "    command: uv run pytest",
        "    exit: 1",
        "    result: 1 failed",
    ]
    if after:
        tests += [
            "  - phase: after",
            "    command: uv run pytest",
            "    exit: 0",
            "    result: 27 passed",
        ]
    lines = [
        "---",
        f"status: {status}",
        f"base: {base}",
        "branch: main",
        "files:",
        "  - path: home/dot_claude/hooks/lib/mygo-gate-state.fish",
        '    lines: "1-40"',
        "tests:",
        *tests,
        "---",
        "",
        "## Question",
        "",
        "Which branch should this land on?",
    ]
    path.write_text("\n".join(lines) + "\n")


def write_verdict(path: Path, report: Path, result: str, failed: int) -> None:
    lines = [
        "---",
        f"report: {report}",
        f"verdict: {result}",
        f"failed: {failed}",
        "---",
        "",
        "## Findings",
        "",
        "None.",
    ]
    path.write_text("\n".join(lines) + "\n")


def state_key(report: Path) -> str:
    return str(report).replace("/", "%")


def inflight(state: Path, report: Path) -> Path:
    return state / "inflight" / state_key(report)


def pending(state: Path, report: Path) -> Path:
    return state / "pending" / state_key(report)


def marker_field(path: Path, field: str) -> str:
    """The value of the first `field: value` line, or "" when absent."""
    if not path.is_file():
        return ""
    pattern = re.compile(rf"^{field}: ?(.*)$")
    for line in path.read_text().splitlines():
        m = pattern.match(line)
        if m:
            return m.group(1)
    return ""


def _text(result, *keys: str) -> str:
    """Mirrors `jq -r '.a.b // ""'` on the hook output."""
    value = result.json()
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    if value is None or value is False:
        return ""
    return value if isinstance(value, str) else json.dumps(value)


def want_allow(result) -> None:
    assert result.rc == 0
    assert result.stdout == "", f"stdout should be empty, got: {result.stdout[:200]}"


def want_deny(result, *needles: str) -> None:
    assert result.rc == 0
    assert _text(result, "hookSpecificOutput", "permissionDecision") == "deny"
    reason = _text(result, "hookSpecificOutput", "permissionDecisionReason")
    for needle in ("dispatch:", *needles):
        assert needle in reason, f"deny reason does not mention {needle!r}: {reason}"


def want_git_denied(result, subcommand: str) -> None:
    assert result.rc == 0
    assert _text(result, "hookSpecificOutput", "permissionDecision") == "deny"
    reason = _text(result, "hookSpecificOutput", "permissionDecisionReason")
    assert f"git {subcommand}" in reason, reason


def block_reason(result) -> str:
    return _text(result, "reason")


def want_block(result, *needles: str) -> None:
    assert result.rc == 0
    assert _text(result, "decision") == "block"
    reason = block_reason(result)
    for needle in needles:
        assert needle in reason, f"block reason does not mention {needle!r}: {reason}"


RunHook = Callable[[Path, str], object]


def dispatch_rikki(run_hook: RunHook, repo: Path, report: Path):
    """A rikki dispatched through the guard, leaving an inflight marker."""
    return run_hook(GUARD, guard_input("rikki", rikki_envelope(repo, report), repo))


def verify_rikki(run_hook: RunHook, repo: Path, head: str, report: Path, agent: str):
    """Drives one report to pending, then dispatches a sakichan for it through
    the guard, which is what marks the entry verifying."""
    dispatch_rikki(run_hook, repo, report)
    write_report(report, "DONE", head)
    run_hook(DONE_HOOK, stop_input("rikki", f"Report: {report}", agent))
    return run_hook(GUARD, guard_input("sakichan", sakichan_envelope(repo, report), repo))


def incomplete_rikki(run_hook: RunHook, repo: Path, head: str, report: Path, agent: str):
    """Drives one report to a pending entry with a failed verdict, the state an
    entry is in when the parent resumes its rikki with SendMessage."""
    verify_rikki(run_hook, repo, head, report, agent)
    verdict = Path(f"{report}.verdict.md")
    write_verdict(verdict, report, "Incomplete", 2)
    return run_hook(DONE_HOOK, stop_input("sakichan", f"Verdict: {verdict}", f"{agent}-v"))


def needs_context_rikki(run_hook: RunHook, repo: Path, head: str, report: Path, agent: str):
    dispatch_rikki(run_hook, repo, report)
    write_report(report, "NEEDS_CONTEXT", head)
    return run_hook(DONE_HOOK, stop_input("rikki", f"Report: {report}\nWhich branch?", agent))
