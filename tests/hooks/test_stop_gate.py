from hookcase import (
    DONE_HOOK,
    GATE,
    block_reason,
    dispatch_rikki,
    gate_input,
    stop_input,
    want_allow,
    want_block,
    write_report,
)

UNREADABLE = 0o000
RESTORED = 0o755


def pend(run_hook, srcrepo, report, agent_id):
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE", srcrepo.head)
    run_hook(DONE_HOOK, stop_input("rikki", f"Report: {report}", agent_id))


def test_empty_pending_allows(run_hook):
    want_allow(run_hook(GATE, gate_input()))


def test_pending_entry_blocks_with_routes(run_hook, srcrepo, tmp_path):
    report = tmp_path / "g1.md"
    pend(run_hook, srcrepo, report, "agent-16")
    inflight_report = tmp_path / "g2.md"
    dispatch_rikki(run_hook, srcrepo.path, inflight_report)
    result = run_hook(GATE, gate_input())
    want_block(
        result,
        str(report),
        str(srcrepo.path),
        "main",
        "unverified",
        "Routes:",
        "delete the named pending file",
    )
    assert str(inflight_report) in block_reason(result)


def test_stop_hook_active_does_not_yield_the_pending_entry(run_hook, srcrepo, tmp_path):
    report = tmp_path / "g4.md"
    pend(run_hook, srcrepo, report, "agent-21")
    want_block(run_hook(GATE, gate_input(True)), str(report), "Routes:")


def test_mygo_verification_gate_0_allows(run_hook, srcrepo, tmp_path, monkeypatch):
    report = tmp_path / "g3.md"
    pend(run_hook, srcrepo, report, "agent-17")
    monkeypatch.setenv("MYGO_VERIFICATION_GATE", "0")
    result = run_hook(GATE, gate_input())
    monkeypatch.delenv("MYGO_VERIFICATION_GATE")
    want_allow(result)


def test_unreadable_state_dir_blocks(run_hook, state):
    state.chmod(UNREADABLE)
    try:
        result = run_hook(GATE, gate_input())
    finally:
        state.chmod(RESTORED)
    want_block(result, "cannot be")
