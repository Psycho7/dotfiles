# CLAUDE.md (Global)
User-wide defaults for all repositories.

## Defaults
- Reflect on tool output before next steps and verify solutions before finishing.
- Do only what is asked. Never proactively edit or create files. No scaffolding, renames/moves/deletes, or new files (especially docs/README) unless explicitly requested or absolutely required.
- Honor project conventions and existing frameworks; do not upgrade or add dependencies without approval. Prefer existing utilities over reimplementing patterns.
- Keep changes minimal, localized, and in existing style. Summarize planned edits when scope is ambiguous; ask one clarifying question at a time when unsure.
- If any instruction conflicts, pause and ask before proceeding.

## Documentation style
- Keep docs concise. The user is an experienced developer; skip obvious environment/language basics.

## Git & workflow
- No destructive git commands (reset --hard/clean/force-push) without explicit request; no history rewrites unless told. Avoid adding untracked/generated/binary artifacts; keep commits scoped/descriptive when asked.
- Ask if unsure about staging/branching strategy.

## Coding practices
- Maintain thread/exception safety; ask if expectations are unclear.
- Do not add/upgrade NuGet/vcpkg/Conan/etc. packages or new feeds without approval.

## Agent Workflow
- In Plan mode, write plans directly after gathering info — do not dispatch a Plan subagent.
- Trust agent summaries for file contents and structure; only re-read files you will edit or where the summary is ambiguous.

## Tools
- Use `jq` for JSON processing
- Prefer built-in tools over Bash:
  - Glob/Read (not `fd`, `find`, `cat`, `head`)
  - Grep (not `rg`, `grep`)
  - Edit/Write (not `sed`, `awk`, `>`)