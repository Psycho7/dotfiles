from hookcase import (
    DONE_HOOK,
    GATE,
    GUARD,
    dispatch_rikki,
    gate_input,
    guard_input,
    marker_field,
    pending,
    sakichan_envelope,
    stop_input,
    verify_rikki,
    want_allow,
    want_block,
    want_deny,
    write_report,
    write_verdict,
)


def sakichan_verdict(run_hook, tmp_path, name, report, result, failed, agent_id):
    verdict = tmp_path / f"{name}.verdict.md"
    write_verdict(verdict, report, result, failed)
    return run_hook(DONE_HOOK, stop_input("sakichan", f"Verdict: {verdict}", agent_id))


def test_guard_sakichan_allow_marks_the_pending_entry_verifying(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "w1.md"
    want_allow(verify_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-23"))
    marker = pending(state, report)
    assert marker_field(marker, "state") == "verifying"
    assert marker_field(marker, "verdict") == "unverified"
    assert marker_field(marker, "head") == srcrepo.head


def test_guard_sakichan_deny_leaves_the_pending_entry_unchanged(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "w2.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE", srcrepo.base1)
    run_hook(DONE_HOOK, stop_input("rikki", f"Report: {report}", "agent-24"))
    result = run_hook(GUARD, guard_input("sakichan", sakichan_envelope(srcrepo.path, report), srcrepo.path))
    want_deny(result, "differs from the HEAD recorded at dispatch")
    marker = pending(state, report)
    assert marker_field(marker, "state") == ""
    assert marker_field(marker, "verdict") == "unverified"


def test_stop_gate_a_verifying_entry_alone_does_not_block(run_hook, srcrepo, tmp_path):
    verify_rikki(run_hook, srcrepo.path, srcrepo.head, tmp_path / "w3.md", "agent-25")
    want_allow(run_hook(GATE, gate_input()))


def test_stop_gate_a_verifying_entry_beside_an_unverified_one_is_listed_only(
    run_hook, srcrepo, tmp_path
):
    report = tmp_path / "w4.md"
    verify_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-26")
    blocked = tmp_path / "w5.md"
    dispatch_rikki(run_hook, srcrepo.path, blocked)
    write_report(blocked, "DONE", srcrepo.head)
    run_hook(DONE_HOOK, stop_input("rikki", f"Report: {blocked}", "agent-27"))
    want_block(
        run_hook(GATE, gate_input()),
        "1 report(s) still need",
        str(blocked),
        "unverified",
        str(report),
        "verifying",
        "not blocking",
    )


def test_sakichan_complete_removes_a_verifying_entry(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "w6.md"
    verify_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-28")
    want_allow(sakichan_verdict(run_hook, tmp_path, "w6", report, "Complete", 0, "agent-29"))
    assert not pending(state, report).exists()
    want_allow(run_hook(GATE, gate_input()))


def test_sakichan_incomplete_clears_verifying_and_blocks_again(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "w7.md"
    verify_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-30")
    want_allow(sakichan_verdict(run_hook, tmp_path, "w7", report, "Incomplete", 2, "agent-31"))
    assert marker_field(pending(state, report), "state") == ""
    want_block(run_hook(GATE, gate_input()), str(report), "Incomplete (2 failed)")


def test_sakichan_cannot_verify_clears_verifying_and_blocks_again(run_hook, srcrepo, tmp_path):
    report = tmp_path / "w8.md"
    verify_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-32")
    want_allow(sakichan_verdict(run_hook, tmp_path, "w8", report, "Cannot verify", 0, "agent-33"))
    want_block(run_hook(GATE, gate_input()), str(report), "Cannot verify")


def test_sakichan_missing_verdict_file_clears_verifying_and_blocks_again(run_hook, srcrepo, tmp_path):
    report = tmp_path / "w9.md"
    verify_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-34")
    missing = tmp_path / "w9.verdict.md"
    want_allow(run_hook(DONE_HOOK, stop_input("sakichan", f"Verdict: {missing}", "agent-35")))
    want_block(run_hook(GATE, gate_input()), str(report), "unreadable")
