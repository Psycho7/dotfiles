# Global Guideline
User-wide guideline for all repositories. Project-level CLAUDE.md and user prompts take precedence over this global guideline when conflicts arise.

## Response Style
- **Direct mode.** Lead with the answer. No filler openers, no hype words, no soft closers, no emojis, no restating the question, no narrating your deliberation. Stop when the content ends.
- **No filler transitions.** Logical connectors are fine ("because", "so", "however", "if"). Ban padding transitions: "Additionally", "Moreover", "Furthermore", "That said", "With that in mind", "To that end".

## CRITICAL - Principles
### 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If uncertain, you MUST use tool AskUserQuestion for clarification.
- If you think anything beyond what was asked is absolutely needed, propose it and ask for approval.

### 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was requested.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- Do not add/upgrade NuGet/vcpkg/npm/Cargo/etc. packages or new feeds without approval

### 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- MUST follow project conventions and existing frameworks.
- If you notice unrelated dead code, mention it - don't delete it.

Every changed line should trace directly to the user's request.

### 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> "Write tests for invalid inputs, then make them pass"
- "Fix the bug" -> "Write a test that reproduces it, then make it pass"
- "Refactor X" -> "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

### 5. Write First, Simplify Later

**Correctness before conciseness. Optimize in batch, not inline.**

During implementation:
- Prioritize working code. Duplication and verbosity are acceptable in-progress.
- Do not self-optimize mid-iteration while requirements are shifting or bugs are being fixed.
- Do not re-invent the wheel. Use existing functions, utilities, and tools already available in the codebase or project dependencies before writing new ones.

Run simplification only at natural completion boundaries:
- A module, feature, or full plan is functionally complete and stable.
- All relevant tests pass.

Skip simplification entirely for throwaway, exploratory, or prototype code.

## Code Comments
Applies to all in-source text that is not code: line/block comments, docstrings, TODO/FIXME/NOTE markers, license/file headers.
- Use ASCII characters only unless explicitly asked otherwise (no em-dashes, smart quotes, Unicode arrows, non-ASCII symbols).
- Do not mention or refer to external documentation, design docs, ADRs, tickets, wikis, or other Markdown files.

## Documentation
- The user is an experienced developer; skip obvious basics in explanations and docs.
- Default to Markdown format when writing documents unless another format is specified.
- In Markdown documents, use Mermaid for workflows, diagrams, sequence diagrams, etc. Only use ASCII art for trivial structures (e.g., folder trees).

## Planning
- Plans must NOT contain implementation code. A plan that has near-complete code defeats its purpose.
- Plans should contain: tasks, acceptance criteria, key decisions, and dependencies.
- Code snippets are acceptable ONLY when they explain a concept more concisely than prose.

## Testing
- Follow the build/test instructions provided by project-level CLAUDE.md.
- If available, run relevant tests before claiming a task is complete.

## Git
- Do not commit unless explicitly asked.
- Avoid committing untracked/generated/binary artifacts. Keep commits scoped and descriptive.
- Use ASCII characters only in commit messages unless explicitly asked otherwise.
- Do not mention or refer to external documentation, design docs, ADRs, tickets, wikis, or other Markdown files in commit messages.
- Commit message style: imperative mood. Single line for small changes (e.g., `Fix null check in parser`). For large commits, a brief summary line followed by bullet details:

```
Refactor auth middleware

- Extract token validation into dedicated module
- Update route handlers to use new middleware
- Remove deprecated session helpers
```

## Exploration
- Trust subagent exploration summaries; do not re-explore.
- For complex exploration, split the task into smaller pieces and spawn up to 3 subagents in parallel.
- Only re-read files you will edit or where the summary is ambiguous.

## Tools
- Use `jq` for JSON processing
- Prefer built-in tools over Bash:
  - Glob/Read (not `fd`, `find`, `cat`, `head`)
  - Grep (not `rg`, `grep`)
  - Edit/Write (not `sed`, `awk`, `>`)
