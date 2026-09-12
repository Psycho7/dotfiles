#!/usr/bin/env fish
# SubagentStart hook: injects a snapshot of the working directory, HEAD, and
# uncommitted changes into the subagent's context so it does not spend tool
# calls gathering them. Reads the hook JSON on stdin; `cwd` follows worktrees.
# Hook output over 10,000 characters is replaced by a file pointer, so long
# lists are truncated.

set -g max_lines 80

function emit
    printf '%s\n' $argv | jq -Rs '{hookSpecificOutput: {hookEventName: "SubagentStart", additionalContext: ("Environment snapshot at start:\n" + .)}}'
end

function capped --argument-names label
    set -l items $argv[2..]
    set -l out "$label"
    set -l n (count $items)
    set -a out $items[1..(math "min($n, $max_lines)")]
    if test $n -gt $max_lines
        set -a out "(+"(math $n - $max_lines)" more)"
    end
    printf '%s\n' $out
end

set -l input (cat)
set -l dir (echo $input | jq -r '.cwd // empty')
if test -n "$dir"; and not cd $dir 2>/dev/null
    emit "cwd: $dir does not exist"
    exit 0
end

set -l lines "cwd: "(pwd)
if git rev-parse --is-inside-work-tree >/dev/null 2>&1
    # Full SHA: the report's base needs all 40 hex digits.
    set -l head (git rev-parse --verify -q HEAD 2>/dev/null)
    test -n "$head"; or set head "none (no commits)"
    set -l branch (git symbolic-ref --short -q HEAD)
    test -n "$branch"; or set branch "detached"
    set -a lines "HEAD: $head ($branch)"
    set -l changes (git status --porcelain)
    if test (count $changes) -gt 0
        set -a lines (capped "Uncommitted changes (git status --porcelain):" $changes)
    else
        set -a lines "Working tree clean"
    end
    set -l subs (git submodule status --recursive 2>/dev/null)
    if test (count $subs) -gt 0
        set -a lines (capped "Submodules (git submodule status; leading - means not initialized):" $subs)
    end
else
    set -a lines "Not a git repository"
end

emit $lines
