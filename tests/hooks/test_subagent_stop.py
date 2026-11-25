import subprocess

from hookcase import (
    DONE_HOOK,
    GATE,
    dispatch_rikki,
    gate_input,
    inflight,
    marker_field,
    pending,
    state_key,
    stop_input,
    want_allow,
    want_block,
    write_report,
    write_verdict,
)

# Each concurrent hook must exit within this many seconds.
HOOK_TIMEOUT_S = 10


def rikki_stop(run_hook, msg, agent_id):
    return run_hook(DONE_HOOK, stop_input("rikki", msg, agent_id))


def sakichan_stop(run_hook, msg, agent_id):
    return run_hook(DONE_HOOK, stop_input("sakichan", msg, agent_id))


def test_rikki_valid_done_moves_inflight_to_pending(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "d1.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE", srcrepo.head)
    want_allow(rikki_stop(run_hook, f"Report: {report}", "agent-1"))
    assert not inflight(state, report).exists()
    assert pending(state, report).exists()
    assert marker_field(pending(state, report), "verdict") == "unverified"
    assert marker_field(pending(state, report), "head") == srcrepo.head


def test_rikki_done_with_concerns_becomes_pending(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "d2.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE_WITH_CONCERNS", srcrepo.head)
    want_allow(rikki_stop(run_hook, f"Report: {report}", "agent-2"))
    assert pending(state, report).exists()


def test_rikki_needs_context_keeps_inflight_and_pends_nothing(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "d3.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "NEEDS_CONTEXT", srcrepo.head)
    want_allow(rikki_stop(run_hook, f"Report: {report}\nWhich branch?", "agent-3"))
    assert inflight(state, report).exists()
    assert not pending(state, report).exists()


def test_rikki_needs_context_then_done_pends_the_resumed_run(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "d8.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "NEEDS_CONTEXT", srcrepo.head)
    want_allow(rikki_stop(run_hook, f"Report: {report}\nWhich branch?", "agent-20"))
    write_report(report, "DONE", srcrepo.head)
    want_allow(rikki_stop(run_hook, f"Report: {report}", "agent-20"))
    marker = pending(state, report)
    assert marker.exists()
    assert marker_field(marker, "cwd") == str(srcrepo.path)
    assert marker_field(marker, "branch") == "main"
    assert marker_field(marker, "head") == srcrepo.head
    assert not inflight(state, report).exists()


def test_rikki_malformed_final_message_blocks_and_marks_a_retry(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "d4.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE", srcrepo.head)
    result = rikki_stop(run_hook, "All done, the report is in the scratchpad.", "agent-4")
    want_block(result, "Report: <absolute path")
    assert (state / "retry" / "_agent-agent-4").exists()
    assert not pending(state, report).exists()


def test_rikki_missing_report_blocks_and_marks_a_retry(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "d5.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    want_block(rikki_stop(run_hook, f"Report: {report}", "agent-5"), "does not exist")
    assert (state / "retry" / state_key(report)).exists()
    assert not pending(state, report).exists()


def test_rikki_second_invalid_completion_pends_as_invalid(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "d6.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    want_block(rikki_stop(run_hook, f"Report: {report}", "agent-6"), "does not exist")
    want_allow(rikki_stop(run_hook, f"Report: {report}", "agent-6"))
    assert marker_field(pending(state, report), "verdict") == "invalid"
    assert not inflight(state, report).exists()


def test_rikki_report_without_a_phase_after_test_blocks(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "d7.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE", srcrepo.head, after=False)
    want_block(rikki_stop(run_hook, f"Report: {report}", "agent-7"), "phase: after")
    assert (state / "retry" / state_key(report)).exists()


def test_rikki_no_inflight_marker_takes_branch_and_head_from_the_report(
    run_hook, state, srcrepo, tmp_path
):
    report = tmp_path / "d9.md"
    write_report(report, "DONE", srcrepo.head)
    want_allow(rikki_stop(run_hook, f"Report: {report}", "agent-22"))
    marker = pending(state, report)
    assert marker.exists()
    assert marker_field(marker, "branch") == "main"
    assert marker_field(marker, "head") == srcrepo.head
    assert marker_field(marker, "cwd") == ""
    want_block(run_hook(GATE, gate_input()), str(report), "cwd: (unknown)")


def done_then_verdict(run_hook, srcrepo, tmp_path, name, rikki_id, sakichan_id, result, failed):
    report = tmp_path / f"{name}.md"
    verdict = tmp_path / f"{name}.verdict.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE", srcrepo.head)
    rikki_stop(run_hook, f"Report: {report}", rikki_id)
    write_verdict(verdict, report, result, failed)
    return report, sakichan_stop(run_hook, f"Verdict: {verdict}", sakichan_id)


def test_sakichan_complete_removes_the_pending_entry(run_hook, state, srcrepo, tmp_path):
    report, result = done_then_verdict(
        run_hook, srcrepo, tmp_path, "v1", "agent-8", "agent-9", "Complete", 0
    )
    want_allow(result)
    assert not pending(state, report).exists()


def test_sakichan_incomplete_annotates_the_pending_entry(run_hook, state, srcrepo, tmp_path):
    report, result = done_then_verdict(
        run_hook, srcrepo, tmp_path, "v2", "agent-10", "agent-11", "Incomplete", 2
    )
    want_allow(result)
    assert marker_field(pending(state, report), "verdict") == "Incomplete (2 failed)"


def test_sakichan_cannot_verify_annotates_the_pending_entry(run_hook, state, srcrepo, tmp_path):
    report, result = done_then_verdict(
        run_hook, srcrepo, tmp_path, "v3", "agent-12", "agent-13", "Cannot verify", 0
    )
    want_allow(result)
    assert marker_field(pending(state, report), "verdict") == "Cannot verify"


def test_sakichan_missing_verdict_file_marks_the_entry_unreadable(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "v4.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE", srcrepo.head)
    rikki_stop(run_hook, f"Report: {report}", "agent-14")
    want_allow(sakichan_stop(run_hook, f"Verdict: {tmp_path / 'v4.verdict.md'}", "agent-15"))
    assert marker_field(pending(state, report), "verdict") == "unreadable"


def test_concurrent_rikki_completions_keep_both_entries(run_hook, state, srcrepo, tmp_path):
    reports = [tmp_path / "c1.md", tmp_path / "c2.md"]
    for report in reports:
        dispatch_rikki(run_hook, srcrepo.path, report)
        write_report(report, "DONE", srcrepo.head)

    procs = [
        subprocess.Popen(
            ["fish", "--no-config", str(DONE_HOOK)],
            stdin=subprocess.PIPE,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        for _ in reports
    ]
    try:
        for proc, report, agent_id in zip(procs, reports, ["agent-18", "agent-19"]):
            proc.stdin.write(stop_input("rikki", f"Report: {report}", agent_id))
            proc.stdin.close()
        for proc in procs:
            proc.wait(timeout=HOOK_TIMEOUT_S)
    finally:
        for proc in procs:
            if proc.poll() is None:
                proc.kill()
                proc.wait(timeout=HOOK_TIMEOUT_S)

    assert [proc.returncode for proc in procs] == [0, 0]

    for report in reports:
        assert pending(state, report).exists()
        assert not inflight(state, report).exists()
