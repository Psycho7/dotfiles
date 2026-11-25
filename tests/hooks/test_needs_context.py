"""The parent dispatches sakichan for a rikki report whose status is
NEEDS_CONTEXT, then resumes the rikki: the guard refuses the dispatch, and a
verdict that slips past it still lands on the dispatch facts."""

from hookcase import (
    DONE_HOOK,
    GATE,
    GUARD,
    RESUMED,
    block_reason,
    dispatch_rikki,
    gate_input,
    guard_input,
    inflight,
    marker_field,
    needs_context_rikki,
    pending,
    sakichan_envelope,
    start_input,
    stop_input,
    want_allow,
    want_block,
    want_deny,
    write_report,
    write_verdict,
)


def guard_sakichan(run_hook, srcrepo, report):
    return run_hook(GUARD, guard_input("sakichan", sakichan_envelope(srcrepo.path, report), srcrepo.path))


def test_guard_sakichan_a_needs_context_report_denies(run_hook, srcrepo, tmp_path):
    report = tmp_path / "y1.md"
    needs_context_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-44")
    want_deny(guard_sakichan(run_hook, srcrepo, report), "NEEDS_CONTEXT", "resume rikki first")


def test_guard_sakichan_a_blocked_report_denies(run_hook, srcrepo, tmp_path):
    report = tmp_path / "y2.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "BLOCKED", srcrepo.head)
    want_deny(guard_sakichan(run_hook, srcrepo, report), "BLOCKED", "resume rikki first")


def test_guard_sakichan_a_done_with_concerns_report_allows(run_hook, srcrepo, tmp_path):
    report = tmp_path / "y3.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE_WITH_CONCERNS", srcrepo.head)
    run_hook(DONE_HOOK, stop_input("rikki", f"Report: {report}", "agent-45"))
    want_allow(guard_sakichan(run_hook, srcrepo, report))


def test_rikki_stop_needs_context_records_the_agent_id_on_the_inflight_marker(
    run_hook, state, srcrepo, tmp_path
):
    report = tmp_path / "y4.md"
    want_allow(needs_context_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-46"))
    marker = inflight(state, report)
    assert marker_field(marker, "agent_id") == "agent-46"
    assert marker_field(marker, "cwd") == str(srcrepo.path)
    assert not pending(state, report).exists()
    want_allow(run_hook(RESUMED, start_input("rikki", "agent-46")))


def test_sakichan_stop_incomplete_with_no_pending_promotes_the_inflight_marker(
    run_hook, state, srcrepo, tmp_path
):
    report = tmp_path / "y5.md"
    needs_context_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-47")
    verdict = tmp_path / "y5.verdict.md"
    write_verdict(verdict, report, "Incomplete", 1)
    want_allow(run_hook(DONE_HOOK, stop_input("sakichan", f"Verdict: {verdict}", "agent-48")))
    marker = pending(state, report)
    assert marker_field(marker, "cwd") == str(srcrepo.path)
    assert marker_field(marker, "branch") == "main"
    assert marker_field(marker, "head") == srcrepo.head
    assert marker_field(marker, "agent_id") == "agent-47"
    assert marker_field(marker, "verdict") == "Incomplete (1 failed)"
    assert not inflight(state, report).exists()
    result = run_hook(GATE, gate_input())
    want_block(result, str(report), str(srcrepo.path), "Incomplete (1 failed)")
    assert "Still in flight" not in block_reason(result)
