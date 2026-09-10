#!/usr/bin/env fish
# PreToolUse hook on Bash for implementer agents: denies git subcommands that
# commit, publish, rewrite history, discard work, or move the branch. Attach
# it in an agent's front matter. Reads the hook JSON on stdin.

set -l denied commit push merge rebase cherry-pick am reset clean stash checkout switch restore

set -l cmd (cat | jq -r '.tool_input.command // empty')

# The subcommand of every `git` in command position (start of the command
# or after ; && || | ( or a backtick), skipping global options such as
# `-C dir` or `-c key=value`.
set -l git_call '(?:^|[;&|(`])\s*git\s+(?:-\S*(?:\s+[^-\s]\S*)?\s+)*(\S+)'
set -l subcommands (string match -arg $git_call -- "$cmd")

function deny --argument-names subcommand
    jq -cn --arg reason "git $subcommand is not allowed for this agent. Leave the working tree and branch as they are; the caller commits, discards, or rewrites." \
        '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: $reason}}'
    exit 0
end

for sub in $subcommands
    if contains -- $sub $denied
        deny $sub
    end
    # `git branch` is read-only unless it deletes.
    if test "$sub" = branch
        set -l words (string split -n ' ' -- (string replace -a \t ' ' -- $cmd))
        if contains -- -d $words; or contains -- -D $words; or contains -- --delete $words
            deny branch
        end
    end
end
