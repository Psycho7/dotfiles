---
name: mygo
description: Use when dispatching the rikki implementer or the sakichan verifier, or when orchestrating implementation subagents across a multi-task plan. Covers the dispatch envelope, brief and report paths, parallelism and worktree rules, resume handling, and the verification gate's Stop block.
---

# Dispatching rikki and sakichan

## Protocol

- Every dispatch prompt carries exactly one fenced `yaml` block with a
  top-level `dispatch` key. Prose around it is context; the block is the
  contract, and the dispatch guard parses only that block.
- Multi-dispatch plans share one brief file in the scratchpad. Each dispatch
  gets the brief path, its own task and criteria, and its own report path.
  sakichan gets the same paths, never a restated report.
- A report path is absolute, unique per task, and must not exist when rikki
  is dispatched. Reusing one is refused by the guard.
- Name every dispatch and run it in the background.
- At most 3 rikkis in flight, disjoint files, one commit each. Use
  `isolation: "worktree"` only when files must overlap; it branches from
  committed HEAD, so commit the base first, send sakichan to the worktree
  path from the report, and integrate the branch yourself.
- Parallel rikkis in one checkout see each other's edits land mid-task, and
  sakichan may flag those as unreported drift. Expect a resume in that case,
  or give each parallel rikki a worktree.
- Verify each rikki as it finishes with a sakichan on its report. Run the
  full verification command once per plan.
- On NEEDS_CONTEXT or failed criteria, resolve the gap and resume the same
  agent with SendMessage. Routine gaps are your call; ask the user only when
  readings differ materially. Resume once; a second NEEDS_CONTEXT means fix
  the brief and re-dispatch. An isolated rikki that returns with no changes
  is re-dispatched, since its worktree is gone.
- sakichan checks correctness, not quality. `/code-review` is the quality
  pass and runs before opening a PR.
- Opus by default, never Sonnet; drop the reasoning effort instead of the
  model. Haiku only for trivial work where speed matters.

## rikki envelope

```yaml
dispatch:
  cwd: /Users/me/project
  branch: main
  report: /tmp/scratch/reports/t1-parser.md
  brief: /tmp/scratch/brief.md
  criteria:
    - "parse() rejects a trailing comma with ParseError"
    - "tests/test_parser.py covers both the valid and the invalid case"
  verify: "bash -c 'cd /Users/me/project && pytest tests/test_parser.py'"
  commit: false
```

`brief` is optional. `report` must not exist yet. rikki writes the report
there and answers with one line, `Report: <absolute path>`.

## sakichan envelope

```yaml
dispatch:
  cwd: /Users/me/project
  report: /tmp/scratch/reports/t1-parser.md
  brief: /tmp/scratch/brief.md
  criteria:
    - "parse() rejects a trailing comma with ParseError"
    - "tests/test_parser.py covers both the valid and the invalid case"
```

No base commit: the report's front matter carries it, and the guard checks
it against the HEAD recorded when rikki was dispatched. sakichan writes
`<report>` with `.md` replaced by `.verdict.md` and answers with one line,
`Verdict: <absolute path>`.

## The verification gate

A rikki that finishes DONE stays pending until a sakichan for the same
report returns verdict `Complete`. Until then the Stop hook blocks the turn
with a reason like:

```
Verification gate: 3 pending report(s).

- /tmp/scratch/reports/t1-parser.md  cwd=/Users/me/project branch=main
  annotation: unverified
- /tmp/scratch/reports/t2-lexer.md  cwd=/Users/me/project branch=main
  annotation: Incomplete (2 criteria failed)
- /tmp/scratch/reports/t3-cli.md  cwd=/Users/me/project branch=main
  annotation: invalid

Routes: dispatch sakichan for an unverified entry; resume rikki then
re-verify a failed one; delete the named pending file to accept as-is.
```

What each annotation asks of you:

| Annotation | Do |
|---|---|
| `unverified` | Dispatch sakichan on that report |
| `Incomplete (<n> criteria failed)` | Read the verdict file, resume rikki with the gap, re-verify |
| `Cannot verify` | Read the verdict file for what is needed, supply it, then re-verify |
| `invalid` | rikki's report failed its schema twice; re-dispatch with the format spelled out |
| `unreadable` | The verdict file is missing or unparsable; re-dispatch sakichan |
| `error` | A hook failed; read the entry's diagnostic and fix the dispatch |

Accepting failed or unverifiable work is the user's call, not yours. Ask
before deleting a pending file, and never set `CLAUDE_VERIFICATION_GATE=0`
on your own.
