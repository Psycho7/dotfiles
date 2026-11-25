"""Shared fixtures for the hook and settings tests."""

import json
import os
import subprocess
import time
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from pathlib import Path

import pytest

# Every hook run must finish within this budget.
HOOK_BUDGET_MS = 1000

# Git as the fixtures and hooks see it: no user or system config (signing,
# hooks, templates) and a fixed identity.
GIT_ENV = {
    "GIT_CONFIG_GLOBAL": os.devnull,
    "GIT_CONFIG_NOSYSTEM": "1",
    "GIT_AUTHOR_NAME": "Test",
    "GIT_AUTHOR_EMAIL": "t@example.com",
    "GIT_COMMITTER_NAME": "Test",
    "GIT_COMMITTER_EMAIL": "t@example.com",
}


@dataclass(frozen=True)
class HookResult:
    rc: int
    stdout: str
    elapsed_ms: float

    def json(self) -> dict:
        """Parsed stdout, or an empty dict when stdout is not a JSON object."""
        try:
            parsed = json.loads(self.stdout)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}


@dataclass(frozen=True)
class Repo:
    path: Path
    base1: str
    head: str


RunHook = Callable[[Path, str], HookResult]


@pytest.fixture(scope="session", autouse=True)
def hermetic_git() -> Iterator[None]:
    with pytest.MonkeyPatch.context() as mp:
        for name, value in GIT_ENV.items():
            mp.setenv(name, value)
        yield


@pytest.fixture(autouse=True)
def no_inherited_mygo_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Drops MYGO_* settings from the developer's shell, such as
    MYGO_VERIFICATION_GATE=0, so that only what a test sets reaches the hooks."""
    for name in [n for n in os.environ if n.startswith("MYGO_")]:
        monkeypatch.delenv(name)


def _git(*args: str) -> str:
    result = subprocess.run(["git", *args], check=True, capture_output=True, text=True)
    return result.stdout.strip()


@pytest.fixture(scope="session")
def srcrepo(tmp_path_factory: pytest.TempPathFactory) -> Repo:
    """A scratch git repo with two empty commits, for head and branch checks."""
    path = tmp_path_factory.mktemp("srcrepo") / "repo"
    path.mkdir()
    _git("init", "-q", str(path))
    commit = ("-C", str(path), "-c", "user.email=t@example.com", "-c", "user.name=Test",
              "commit", "-q", "--allow-empty")
    _git(*commit, "-m", "first")
    base1 = _git("-C", str(path), "rev-parse", "HEAD")
    _git(*commit, "-m", "second")
    head = _git("-C", str(path), "rev-parse", "HEAD")
    return Repo(path=path, base1=base1, head=head)


@pytest.fixture
def state(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, no_inherited_mygo_env: None) -> Path:
    """A fresh gate state dir, exported to the hooks."""
    path = tmp_path / "state"
    path.mkdir()
    monkeypatch.setenv("MYGO_VERIFICATION_GATE_DIR", str(path))
    return path


@pytest.fixture
def run_hook(state: Path) -> RunHook:
    """Runs `fish --no-config <script>` on stdin JSON and fails when it
    exceeds the budget.

    stderr is discarded: it is diagnostics, not hook output.
    """

    def run(script: Path, stdin: str) -> HookResult:
        t0 = time.monotonic()
        proc = subprocess.run(
            ["fish", "--no-config", str(script)],
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
        )
        elapsed_ms = (time.monotonic() - t0) * 1000
        assert elapsed_ms <= HOOK_BUDGET_MS, f"{script.name} took {elapsed_ms:.0f}ms"
        return HookResult(rc=proc.returncode, stdout=proc.stdout, elapsed_ms=elapsed_ms)

    return run
