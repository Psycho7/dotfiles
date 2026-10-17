#!/usr/bin/env fish
# PreToolUse hook on Agent for subagents: allows only the agent types passed
# as arguments. Claude Code ignores `Agent(type, ...)` lists in a subagent's
# `tools:`, so this enforces them. Attach it in an agent's front matter.
# Reads the hook JSON on stdin.

set -l allowed $argv

# An allowlist fails closed: exit 2 blocks the call when the input cannot
# be read.
if not command -q jq
    echo "agent-type-guard: jq not found" >&2
    exit 2
end

# An omitted type spawns the default general-purpose agent.
set -l agent (cat | jq -r '.tool_input.subagent_type // "general-purpose"')
or begin
    echo "agent-type-guard: unreadable hook input" >&2
    exit 2
end

# A type split over several lines is never a valid name.
if test (count $agent) -ne 1; or not contains -- $agent $allowed
    jq -cn --arg reason "Agent type $agent is not allowed for this agent. Allowed: "(string join ', ' $allowed)"." \
        '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $reason}}'
end
