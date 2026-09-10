# rikki report

Markdown with YAML front matter. The front matter is parsed by the gate hooks with `yq --front-matter=extract` and is the sole authority for status; the body is for the reader.

Front matter:

- `status`: `DONE`, `DONE_WITH_CONCERNS`, `NEEDS_CONTEXT`, or `BLOCKED`.
- `base`: the full 40-hex SHA of the HEAD rikki started from; omitted when
  the snapshot shows no HEAD commit (not a repository, or no commits yet).
- `branch`: the branch worked on, when there is one.
- `worktree`: absolute path, only when the work ran in one.
- `files`: list of `{path, lines}`; `lines` is a string such as `"12-40"`
  or `"12-40,88"` pointing at the key edits.
- `tests`: list of `{phase, command, exit, result}`; `phase` is `before`
  for the failing run and `after` for the passing run.

`DONE` and `DONE_WITH_CONCERNS` need non-empty `files`, a `tests` entry
with `phase: after`, and `base` unless there was no HEAD commit, in which
case the gate rejects a report that carries one. `NEEDS_CONTEXT` and
`BLOCKED` need a `Question` section in the body.

Body sections: `Deviations` (where the brief and the code disagreed and
what was done about it), `Concerns` (visibility widenings, restructures,
anything left alone on purpose), and `Question` for the blocked statuses.

````markdown
---
status: DONE
base: 4f2c1a9e8b7d6c5f4e3d2c1b0a9f8e7d6c5b4a39
branch: main
files:
  - path: src/auth/token.py
    lines: "12-40,88"
  - path: tests/auth/test_token.py
    lines: "1-64"
tests:
  - phase: before
    command: "pytest tests/auth/test_token.py"
    exit: 1
    result: "3 failed"
  - phase: after
    command: "pytest tests/auth/test_token.py"
    exit: 0
    result: "3 passed, output clean"
---

## Deviations

- The brief named `src/auth/tokens.py`; the file is `token.py`.

## Concerns

- `validate` was private and is now module-level so the tests can reach it.
````

