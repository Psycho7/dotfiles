#!/usr/bin/env fish
# PreToolUse hook on Skill for subagents: allows only skills whose SKILL.md
# front matter sets metadata.coding-skill to "true". Claude Code has no
# per-subagent skill allowlist, so this provides one. Attach it in an
# agent's front matter. Reads the hook JSON on stdin.

set -l marker coding-skill

# An allowlist fails closed: exit 2 blocks the call when a required tool is
# missing or the input cannot be read.
for tool in jq yq
    if not command -q $tool
        echo "coding-skill-guard: $tool not found" >&2
        exit 2
    end
end

set -l input (cat | string collect)
set -l skill (printf '%s' $input | jq -r '.tool_input.skill // empty' | string trim -l -c /)
set -l cwd (printf '%s' $input | jq -r '.cwd // empty')
or begin
    echo "coding-skill-guard: unreadable hook input" >&2
    exit 2
end

function deny --argument-names skill marker
    jq -cn --arg reason "Skill $skill is not allowed for this agent. Only coding skills may be invoked: user or project skills whose SKILL.md front matter sets metadata.$marker: \"true\"." \
        '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $reason}}'
    exit 0
end

# A plain skill name only: no plugin prefix, path, or traversal.
if not string match -qr '^[A-Za-z0-9][A-Za-z0-9_.-]*$' -- "$skill"
    deny "$skill" $marker
end

# User skills shadow project skills of the same name, so the first SKILL.md
# found decides. Project skills load from the working directory and every
# parent up to the repo root.
set -l roots $HOME/.claude/skills
set -l top (git -C "$cwd" rev-parse --show-toplevel 2>/dev/null)
set -l dir
test -n "$cwd"; and set dir (path resolve $cwd)
while test -n "$dir"
    set -a roots $dir/.claude/skills
    if test -z "$top"; or test "$dir" = "$top"; or test "$dir" = /
        break
    end
    set dir (path dirname $dir)
end

for root in $roots
    set -l file $root/$skill/SKILL.md
    test -f $file; or continue

    set -l value (yq --front-matter=extract ".metadata[\"$marker\"] // \"\"" $file 2>/dev/null)
    test "$value" = true; and exit 0
    break
end

deny "$skill" $marker
