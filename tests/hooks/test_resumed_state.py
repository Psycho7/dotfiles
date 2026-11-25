from hookcase import (
    DONE_HOOK,
    GATE,
    RESUMED,
    dispatch_rikki,
    gate_input,
    incomplete_rikki,
    marker_field,
    pending,
    start_input,
    stop_input,
    want_allow,
    want_block,
    write_report,
)


def test_rikki_stop_the_pending_entry_records_the_agent_id(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "x1.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    write_report(report, "DONE", srcrepo.head)
    want_allow(run_hook(DONE_HOOK, stop_input("rikki", f"Report: {report}", "agent-36")))
    assert marker_field(pending(state, report), "agent_id") == "agent-36"


def test_subagent_start_a_matching_agent_id_marks_the_pending_entry_resumed(
    run_hook, state, srcrepo, tmp_path
):
    report = tmp_path / "x2.md"
    incomplete_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-37")
    want_allow(run_hook(RESUMED, start_input("rikki", "agent-37")))
    marker = pending(state, report)
    assert marker_field(marker, "state") == "resumed"
    assert marker_field(marker, "verdict") == "Incomplete (2 failed)"
    assert marker_field(marker, "cwd") == str(srcrepo.path)


def test_subagent_start_an_unknown_agent_id_changes_nothing(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "x3.md"
    incomplete_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-38")
    want_allow(run_hook(RESUMED, start_input("rikki", "agent-fresh")))
    assert marker_field(pending(state, report), "state") == ""


def test_stop_gate_a_resumed_entry_alone_does_not_block(run_hook, srcrepo, tmp_path):
    report = tmp_path / "x5.md"
    incomplete_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-40")
    run_hook(RESUMED, start_input("rikki", "agent-40"))
    want_allow(run_hook(GATE, gate_input()))


def test_stop_gate_a_resumed_entry_beside_an_unverified_one_is_listed_only(
    run_hook, srcrepo, tmp_path
):
    report = tmp_path / "x6.md"
    incomplete_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-41")
    run_hook(RESUMED, start_input("rikki", "agent-41"))
    blocked = tmp_path / "x7.md"
    dispatch_rikki(run_hook, srcrepo.path, blocked)
    write_report(blocked, "DONE", srcrepo.head)
    run_hook(DONE_HOOK, stop_input("rikki", f"Report: {blocked}", "agent-42"))
    want_block(
        run_hook(GATE, gate_input()),
        "1 report(s) still need",
        str(blocked),
        "unverified",
        str(report),
        "resumed",
        "not blocking",
    )


def test_rikki_stop_a_second_done_keeps_the_recorded_dispatch_facts(
    run_hook, state, srcrepo, tmp_path
):
    report = tmp_path / "x8.md"
    incomplete_rikki(run_hook, srcrepo.path, srcrepo.head, report, "agent-43")
    run_hook(RESUMED, start_input("rikki", "agent-43"))
    write_report(report, "DONE", srcrepo.head)
    want_allow(run_hook(DONE_HOOK, stop_input("rikki", f"Report: {report}", "agent-43")))
    marker = pending(state, report)
    assert marker_field(marker, "cwd") == str(srcrepo.path)
    assert marker_field(marker, "branch") == "main"
    assert marker_field(marker, "head") == srcrepo.head
    assert marker_field(marker, "agent_id") == "agent-43"
    assert marker_field(marker, "verdict") == "unverified"
    assert marker_field(marker, "state") == ""
    want_block(run_hook(GATE, gate_input()), str(report), str(srcrepo.path), "unverified")
