from hookcase import (
    GUARD,
    NOCOMMIT,
    dispatch_rikki,
    fenced,
    guard_input,
    inflight,
    marker_field,
    pending,
    sakichan_envelope,
    want_allow,
    want_deny,
    write_report,
)


def run_guard(run_hook, agent, prompt, repo):
    return run_hook(GUARD, guard_input(agent, prompt, repo))


def test_rikki_valid_envelope_allows_and_records_inflight(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "r1.md"
    want_allow(dispatch_rikki(run_hook, srcrepo.path, report))
    marker = inflight(state, report)
    assert marker.exists()
    assert marker_field(marker, "head") == srcrepo.head
    assert marker_field(marker, "cwd") == str(srcrepo.path)
    assert marker_field(marker, "branch") == "main"


def test_rikki_no_envelope_denies(run_hook, srcrepo):
    result = run_guard(run_hook, "rikki", "Just prose, no envelope at all.", srcrepo.path)
    want_deny(result, "fenced")


def test_rikki_malformed_yaml_denies(run_hook, srcrepo):
    prompt = fenced("dispatch:", "  cwd: [unclosed", "   bad: : :")
    want_deny(run_guard(run_hook, "rikki", prompt, srcrepo.path), "valid YAML")


def test_rikki_missing_field_denies_naming_it(run_hook, srcrepo):
    prompt = fenced(
        "dispatch:",
        f"  cwd: {srcrepo.path}",
        "  branch: main",
        "  criteria:",
        "    - something",
    )
    want_deny(run_guard(run_hook, "rikki", prompt, srcrepo.path), "report", "missing")


def test_rikki_branch_is_optional(run_hook, srcrepo, tmp_path):
    prompt = fenced(
        "dispatch:",
        f"  cwd: {srcrepo.path}",
        f"  report: {tmp_path / 'r2.md'}",
        "  criteria:",
        "    - something",
    )
    want_allow(run_guard(run_hook, "rikki", prompt, srcrepo.path))


def test_rikki_existing_report_path_denies(run_hook, srcrepo, tmp_path):
    report = tmp_path / "r3.md"
    report.write_text("existing\n")
    want_deny(dispatch_rikki(run_hook, srcrepo.path, report), "report", "already exists")


def test_rikki_inflight_report_path_denies(run_hook, srcrepo, tmp_path):
    report = tmp_path / "r4.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    want_deny(dispatch_rikki(run_hook, srcrepo.path, report), "report", "in flight")


def test_rikki_pending_report_path_denies(run_hook, state, srcrepo, tmp_path):
    report = tmp_path / "r5.md"
    dispatch_rikki(run_hook, srcrepo.path, report)
    inflight(state, report).rename(pending(state, report))
    want_deny(dispatch_rikki(run_hook, srcrepo.path, report), "report", "pending verification")


def test_sakichan_missing_report_denies(run_hook, srcrepo, tmp_path):
    prompt = sakichan_envelope(srcrepo.path, tmp_path / "s2.md")
    want_deny(run_guard(run_hook, "sakichan", prompt, srcrepo.path), "report", "does not exist")


def test_sakichan_base_that_is_not_a_commit_denies(run_hook, srcrepo, tmp_path):
    report = tmp_path / "s3.md"
    write_report(report, "DONE", NOCOMMIT)
    prompt = sakichan_envelope(srcrepo.path, report)
    want_deny(run_guard(run_hook, "sakichan", prompt, srcrepo.path), "not a commit")
