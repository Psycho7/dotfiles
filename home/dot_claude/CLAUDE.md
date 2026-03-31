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

## Agent dispatch
- In Plan mode, write plans directly after gathering info — do not dispatch a Plan subagent.

## Tools
- Use `fd` or `rg --files` instead of `tree`.
- Prefer `rg` over `grep`, `fd` over `find`.
- Use `jq` for JSON processing