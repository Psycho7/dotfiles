import pytest

from hookcase import GIT_GUARD, bash_input, want_allow, want_git_denied

DENIED = [
    ("git -C /tmp/x commit -m Done", "commit"),
    ("cd /tmp/x && git -c user.name=t commit --amend", "commit"),
    ("git push --force origin main", "push"),
    ("git reset --hard HEAD~1", "reset"),
    ("git clean -fd", "clean"),
    ("git checkout .", "checkout"),
    ("git restore src/a.py", "restore"),
    ("git stash", "stash"),
    ("git switch main", "switch"),
    ("git branch -D feature", "branch"),
    ("git rebase -i HEAD~3", "rebase"),
]

ALLOWED = [
    "git log --grep commit",
    "git diff --stat",
    "git status --porcelain",
    "git show HEAD:src/a.py",
    "git branch --show-current",
    "rg -n 'git push' docs/",
]


@pytest.mark.parametrize(("command", "subcommand"), DENIED, ids=[c for c, _ in DENIED])
def test_denies(run_hook, command, subcommand):
    want_git_denied(run_hook(GIT_GUARD, bash_input(command)), subcommand)


@pytest.mark.parametrize("command", ALLOWED, ids=ALLOWED)
def test_allows(run_hook, command):
    want_allow(run_hook(GIT_GUARD, bash_input(command)))
