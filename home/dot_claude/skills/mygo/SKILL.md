---
name: mygo
description: Dispatch rikki (implementer) and sakichan (verifier) for work that needs a verification gate. Use for tasks with acceptance criteria that span several files, or when the user asks for rikki or sakichan.
---

# Dispatching rikki and sakichan

This skill is for high-stakes or complex works.
For trivial works, suggest `feature-dev` or inline.

## Protocol

- Every dispatch carries the envelope from `references/envelopes.md`. The
  dispatch guard refuses prompts without it.
- A criterion names observable behaviour and the command or diff that
  proves it. What cannot be proven that way is context for the brief, not
  a criterion.
- Criteria carry every project-mandated gate the change can affect
  (formatter, audit, visual protocol, from CLAUDE.md or your memory), each
  with its command; subagents see neither your memory nor this
  conversation. `verify` is the task's targeted test command.
- An Explore does the groundwork and returns a map of at most ~40 lines:
  files and symbols, facts with `path:line`, open questions. Never read
  source for a brief. A brief names files, symbols and rulings, no line
  numbers.
- A dispatch is one coherent change of any size.
- A removal brief: what goes, and the search that proves it gone.
- Report paths are absolute, unique per dispatch, and must not exist yet.
  A plan with several tasks shares one brief file in the scratchpad.
- Run every independent task in the background at once. Use worktrees to
  avoid collision: commit the base first, integrate the branch yourself
  after.
- rikki never commits. You commit after the verdict, when the user asked
  for commits.
- Every DONE rikki gets its own sakichan on its report. sakichan checks
  the criteria, not quality; `/code-review` is the quality pass before a PR.
- A sakichan prompt is the envelope alone, no prose; she reads the report
  and the brief herself.
- Read reports by front matter (`yq --front-matter=extract`), further
  sections only when needed. Never read a verdict to learn its outcome:
  the Stop gate lists every report not yet Complete. Open a verdict file
  only for an `Incomplete` or `Cannot verify` entry.
- On NEEDS_CONTEXT or a failed verdict, resolve the gap and resume the same
  agent with SendMessage, then re-verify. Resume once; a second
  NEEDS_CONTEXT means the brief is wrong, fix it and re-dispatch.
- A Complete report is final: no resuming that rikki, no editing the files
  it lists. Follow-up is a new dispatch with a new report path, or the
  final message calls the edit unverified. A rikki's files are off limits
  while it holds the task.
- Do not re-check Complete work: no `git diff`, test runs, or screenshots
  for it. The closing gates are the only re-run. To commit, stage the
  paths in each report's `files`.

## Closing

Once every task is Complete, run the full test command and the mandatory
gates once; a failure is a new task through rikki and sakichan. Keep their
output out of your context: run them quietly, or filtered to the exit code
and failures.

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
| `error` | A hook failed; read the entry's diagnostic, fix the dispatch, delete the entry |

Accepting failed or unverifiable work is the user's call. Ask before
deleting a pending file that names a report; an `error` entry names none
and is yours to delete.
