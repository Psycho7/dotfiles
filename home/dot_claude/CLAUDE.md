# Global Guideline
User-wide guideline for all repositories. Project-level CLAUDE.md and user prompts take precedence over this global guideline when conflicts arise.

## Response Style
- Provide concise, focused response; no mannered prose.
- Skip non-essential context; keep disclaimers and caveats brief.
- When asked to explain something, give a high-level summary unless requested otherwise.
- The user is an experienced developer; skip obvious basics in explanations and docs.

## Humanize Before Delivering
Before delivering human-facing prose (docs, writeups, PR bodies, commit messages, comments), humanize it with the `humanizer` skill or `tomorin`.

## Principles
- Push back when a simpler approach exists or the request looks wrong.
- Touch only what the request needs, in code, docs, and config alike. Mention anything beyond it, and do it only once the user agrees.
- Do not add/upgrade NuGet/vcpkg/npm/Cargo/etc. packages or new feeds without approval.
- Before asserting how a tool, API, or product behaves, verify against current docs or source and cite it; otherwise say "unverified".
- Verify before claiming a task done: tests for code, a diff or dry run for config, a preview for docs where one exists.
- Guides or scripts with copy-paste commands get an adversarial audit pass (paths, prerequisites, ordering) before delivery.

## Interaction and Tooling Discipline
- Find all affected sites before asking a scoping question. Ask once with the real scope.
- After asking, stop and wait; never pre-commit to a guessed option. If the question times out, take the most conservative reading, carry it as a stated assumption, and lead the final report with it.
- Verify paths, files, and scope with a real read/grep before launching a workflow or fan-out. Never size work off unverified bash output, invented filenames, or stale summaries.
- Do not run commands that change the machine or profile (`chezmoi apply`, installs, service restarts, config applies) unless explicitly asked. Editing source is not a request to apply it.

## Coding Principles
Before writing or editing code in any language, invoke and follow the `coding-principles` skill. Language-specific skills (e.g. `csharp-style`) build on it.

## Documentation
- Keep generated docs (CLAUDE.md, handoffs, etc.) concise and proportional to the request; reference existing content instead of duplicating it, and do not inline large structured content into prose.
- Default to Markdown format when writing documents unless another format is specified.
- In Markdown documents, use Mermaid for workflows, diagrams, sequence diagrams, etc. Only use ASCII art for trivial structures (e.g., folder trees).

## Planning
- Plans hold tasks, acceptance criteria, key decisions, and dependencies, not implementation code; a snippet only where it explains a concept more concisely than prose.

## Git
- Do not commit unless explicitly asked.
- Keep commits scoped; stage explicit paths (never `git add -A` or `git add .`) and leave out untracked, generated, and binary artifacts.
- Before committing, confirm the repo root (`git rev-parse --show-toplevel`) and the branch, and run `git status`; list pre-existing uncommitted changes instead of sweeping them in.
- Never discard changes (`git checkout --`, `git restore`, `git stash`) without showing the diff that would be lost.
- Never merge PRs (`gh pr merge`, `git merge`). Open the PR, confirm CI, hand over the URL. Integrating a subagent worktree branch locally is the one exception.
- Commit messages are ASCII only unless explicitly asked otherwise, and never mention external documentation, design docs, ADRs, tickets, wikis, or other Markdown files.
- Commit message style: imperative mood. Subject line capitalized, no trailing period, 50 characters target and 72 hard limit. Single line for small changes (e.g., `Fix null check in parser`). For large commits, a brief summary line followed by bullet details that explain what and why, not how; wrap at 72.

## Subagents
- Work with acceptance criteria across several files goes through `mygo`; smaller features through `/feature-dev`.
- Mechanical, token-heavy work with no design judgment (renames, reference sweeps, bulk fixture edits) goes to a subagent with exact instructions and a verification command, not inline.
- Split complex exploration into one subagent per independent area, with no overlap; scale the count to the work, and keep each brief tight so every agent's context stays small.
- Trust subagent exploration summaries; re-read only files you will edit or where the summary is ambiguous.
- Ad-hoc subagents run Opus; review and audit subagents run at high effort.

## Tools
- `jq` for JSON processing
- `yq` for YAML and Markdown front matter
- File finding: use `fd` (not `find`)
- Content search: use `rg` (not `grep`)
