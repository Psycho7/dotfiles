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

## Git
- No destructive git commands (reset --hard/clean/force-push) without explicit request; no history rewrites unless told. Avoid adding untracked/generated/binary artifacts; keep commits scoped/descriptive when asked.

## Coding practices
- Maintain thread/exception safety; ask if expectations are unclear.
- Do not add/upgrade NuGet/vcpkg/Conan/etc. packages or new feeds without approval.

## Agent Workflow
- Use the proxy-explore skill for all codebase exploration, including plan mode Phase 1 — it delegates to a faster model and preserves main context. The Explore subagent type is only a fallback when proxy-explore is unavailable.
- Trust /proxy-explore for exploration summary and structure, do not re-explore.
- For complex exploration, split the task into smaller pieces and spawn up to 3 subagents in parallel.
- Only re-read files you will edit or where the summary is ambiguous.

## Tools
- Use `jq` for JSON processing
- Prefer built-in tools over Bash:
  - Glob/Read (not `fd`, `find`, `cat`, `head`)
  - Grep (not `rg`, `grep`)
  - Edit/Write (not `sed`, `awk`, `>`)
