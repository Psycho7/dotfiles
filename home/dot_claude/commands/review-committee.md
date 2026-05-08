---
description: Convene a Codex + Opus + Sonnet review committee on $ARGUMENTS and merge their findings into one categorized list
argument-hint: <target — file paths, branch/SHA, or free-form description>
---

# Review Committee

Convene three reviewers in parallel on the target, then merge their findings into one actionable list. One round only — do not auto-loop.

Reviewers are read-only and operate on the current working directory. Uncommitted changes are visible to them; if the user's target implies "current work", reviewers will include WIP via `git status` / `git diff`. If the user names a specific SHA, branch, or PR, reviewers inspect via git commands rather than checking it out.

Target: $ARGUMENTS

## Procedure

### 1. Dispatch three reviewers in parallel

Send three Task/Agent calls in a single message so they run concurrently. All three operate on the current working directory — reviewers are read-only, so there is no isolation concern.

For each call:
- Take the reviewer prompt template at the bottom of this file, substitute `{TARGET}` with the user's target, and pass the result as the `prompt` parameter.
- Set the other parameters per reviewer:
  - **Codex**: `subagent_type: codex:codex-rescue` (provided by the codex plugin). No `model` override — the agent handles routing.
  - **Opus**: `subagent_type: general-purpose`, `model: opus`.
  - **Sonnet**: `subagent_type: general-purpose`, `model: sonnet`.

### 2. Merge findings into one report

Tag each item with reviewer initials: `C` = Codex, `O` = Opus, `S` = Sonnet.

Output structure:

```
## Review Committee Report

### MUST FIX
- [C+O+S] <issue> -- <file:line>
- [C+O]   <issue> -- <file:line>
- [O]     <issue> -- <file:line>

### SHOULD FIX
(same shape)

### NICE TO HAVE
(same shape)

### Disagreements
- C: <claim>; O: <opposite claim>. <one-line context>

### Cleared
- <area> [<initials of reviewers who examined and cleared it, e.g. C+O+S, or O+S>]
```

Within each category, sort by reviewer count descending so consensus issues come first.

For Cleared, only include areas where two or more reviewers explicitly cleared the same scope; drop solo clears to keep the section signal-rich.

Distinguish three cases when reviewers don't all agree on an issue:

- **Silent omission**: a reviewer didn't mention it. Tag with only the flaggers, e.g. `[C+O] <issue>` if Sonnet didn't raise it. This is the common case — reviewers don't share scope.
- **Partial disagreement**: one reviewer *explicitly* cleared an area another flagged. Keep the item under its severity tier with a parenthetical note, e.g. `[C+O] <issue> -- <file:line> (S cleared)`.
- **Direct contradiction**: reviewers make opposing claims about the same specific code (one says broken, another says correct). Move to the Disagreements section with both sides quoted; the user decides.

### 3. Stop

Hand the report to the user and stop. The point of this command is to surface findings for the user to triage — auto-fixing or re-running collapses that decision back onto the model and burns a round on issues the user may not care about. If the user wants another pass, they will invoke the command again.

## Reviewer prompt template

Send this to each reviewer (Codex, Opus, Sonnet). Substitute `{TARGET}`.

---

You are one of three independent reviewers on a committee. The other two reviewers operate independently. Do not assume they will catch what you miss; do not defer to them.

Target: {TARGET}

Scope rules:
- You are read-only. Do not edit, write, or run anything that mutates state.
- Operate on the current working directory.
- If the target references a specific commit, branch, or PR, use git commands (`git show`, `git diff`, `git log`) to inspect it — do not assume it is checked out.
- If there are uncommitted changes (`git status` is non-empty) and the target is "current work" or unqualified, include them in the review. Use `git diff` and `git diff --staged` to see them.
- If the target explicitly says "the committed state" or names a SHA, ignore uncommitted changes.

Severity rubric:
- MUST FIX: correctness, security, data loss, or contract violation. Code is wrong, will break, or violates an invariant.
- SHOULD FIX: significant quality issue. Misleading naming, missing edge case, brittle design, or performance cliff under realistic load.
- NICE TO HAVE: polish, minor refactor, comment quality. Genuinely optional.

Ground every finding in a `file:line` reference. Quote the offending code only when the line number alone is insufficient to understand the finding (e.g., a multi-line construct, or a non-obvious smell that needs surrounding context). A finding without a specific anchor is too vague — sharpen it or drop it.

Skip style nits already covered by formatters or linters. Skip NICE items unless the target is explicitly a polish pass.

If the target is a non-code artifact (plan, design doc, question), anchor findings to section headings, bullet indices, or short quoted phrases instead of `file:line`. Same severity rubric, judged on argument quality, factual accuracy, and missing considerations.

Output format:

```
### MUST FIX
- <file:line> -- <one-sentence claim>
  <2-4 line explanation if needed>

### SHOULD FIX
(same shape)

### NICE TO HAVE
(same shape)

### Cleared
- <short noun-phrase label for an area you examined and found sound, e.g. "error-handling paths in Foo.cs", "argument parsing">

```

Clears must name a concrete scope another reviewer could match against — a function, file region, or specific concern. `Cleared: the code` is too broad to merge and will be dropped.

Be direct. No padding, no hedging, no preamble or trailing summary. If the target is sound, say so plainly.
