---
name: mygo
description: Dispatch rikki (implementer) and sakichan (verifier) for work that needs a verification gate. Use for tasks with acceptance criteria that span several files, or when the user asks for rikki or sakichan.
---

# Dispatching rikki and sakichan

Not every task needs this. Small changes go inline or through
`/feature-dev`; this skill is for work whose result must be verified
before you accept it.

## Protocol

- Every dispatch carries the envelope from `references/envelopes.md`. The
  dispatch guard refuses prompts without it.
- Report paths are absolute, unique per dispatch, and must not exist yet.
  A plan with several tasks shares one brief file in the scratchpad.
- Run dispatches in the background. At most 3 rikkis in flight, on disjoint
  files. Parallel rikkis in one checkout see each other's edits land and
  sakichan may flag those as drift, so give overlapping work
  `isolation: "worktree"`; that branches from committed HEAD, so commit the
  base first, and integrate the branch yourself afterwards.
- rikki never commits. You commit after the verdict, when the user asked
  for commits.
- Every DONE rikki gets its own sakichan on its report. sakichan checks
  correctness, not quality; `/code-review` is the quality pass before a PR.
- On NEEDS_CONTEXT or a failed verdict, resolve the gap and resume the same
  agent with SendMessage, then re-verify. Resume once; a second
  NEEDS_CONTEXT means the brief is wrong, fix it and re-dispatch.

## The verification gate

A DONE rikki stays pending until a sakichan for the same report returns
`Complete`. Until then the Stop hook blocks your turn with the pending
reports and an annotation each:

| Annotation | Do |
|---|---|
| `unverified` | Dispatch sakichan on that report |
| `Incomplete (<n> criteria failed)` | Read the verdict file (`references/verdict.md`), resume rikki with the gap, re-verify |
| `Cannot verify` | Read the verdict file for what is needed, supply it, re-verify |
| `invalid` | rikki's report failed its format twice; re-dispatch pointing at `references/report.md` |
| `unreadable` | The verdict file is missing or unparsable; re-dispatch sakichan |
| `error` | A hook failed; read the entry's diagnostic and fix the dispatch |

Accepting failed or unverifiable work is the user's call. Ask before
deleting a pending file.
