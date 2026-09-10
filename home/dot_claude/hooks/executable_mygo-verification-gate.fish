#!/usr/bin/env fish
# Stop hook: keeps the turn open while a rikki report is still waiting for a
# sakichan verdict of Complete. Reads the hook JSON on stdin (stop_hook_active,
# session_id, optional scratchpad_dir).
#
# stop_hook_active is deliberately not consulted; the documented 8-block cap
# is the backstop. inflight entries and pending entries in state verifying or
# resumed are listed for information only and never block, because a completing
# rikki or sakichan re-invokes the parent and the next Stop is gated.
# MYGO_VERIFICATION_GATE=0 disables the block for the session.

source (status dirname)/lib/mygo-gate-state.fish

set -g routes "Routes: dispatch sakichan for an unverified entry; resume rikki with SendMessage and re-verify a failed one; or, if the user decides to accept the work as-is, delete the named pending file."

# Every argument is one line of the reason; jq joins them, because a fish
# command substitution would split a joined string back into a list.
function block
    jq -n '{decision: "block", reason: ($ARGS.positional | join("\n"))}' --args $argv
    exit 0
end

# The state line wins over the verdict, so an entry whose sakichan is running
# reads "verifying" and one whose rikki was resumed reads "resumed". A field
# the guard could not record prints "(unknown)" rather than a blank.
function describe --argument-names marker
    set -l report (marker_get $marker report)
    set -l cwd (marker_get $marker cwd)
    set -l branch (marker_get $marker branch)
    set -l state (marker_get $marker state)
    test -n "$report"; or set report (basename $marker)
    test -n "$state"; or set state (marker_get $marker verdict)
    test -n "$state"; or set state unverified
    test -n "$cwd"; or set cwd "(unknown)"
    test -n "$branch"; or set branch "(unknown)"
    printf '%s\n' "- $report" "  cwd: $cwd  branch: $branch" "  state: $state  pending file: $marker"
end

if test "$MYGO_VERIFICATION_GATE" = 0
    exit 0
end

set -l input (cat)
set -l scratchpad (printf '%s' $input | jq -r '.scratchpad_dir // empty' 2>/dev/null)
set -l session (printf '%s' $input | jq -r '.session_id // empty' 2>/dev/null)

set -l dir (state_dir "$scratchpad" "$session")
if test $status -ne 0
    block "The verification gate state directory $gate_dir cannot be created or read, so pending verifications cannot be checked. Fix the directory or set MYGO_VERIFICATION_GATE=0 for this session, then stop again."
end
if not test -r $dir/pending -a -x $dir/pending
    block "The verification gate state directory $dir/pending cannot be read, so pending verifications cannot be checked. Fix the directory or set MYGO_VERIFICATION_GATE=0 for this session, then stop again."
end

set -l blocking
set -l running
for marker in (pending_list)
    set -l state (marker_get $marker state)
    if contains -- "$state" verifying resumed
        set -a running $marker
    else
        set -a blocking $marker
    end
end

if test (count $blocking) -eq 0
    exit 0
end

set -l lines "Verification gate: "(count $blocking)" report(s) still need a sakichan verdict of Complete."
for marker in $blocking
    set -a lines (describe $marker)
end

if test (count $running) -gt 0
    set -a lines "" "Being verified or resumed right now (informational, not blocking):"
    for marker in $running
        set -a lines (describe $marker)
    end
end

set -l inflight (inflight_list)
if test (count $inflight) -gt 0
    set -a lines "" "Still in flight (informational, not blocking):"
    for marker in $inflight
        set -l report (marker_get $marker report)
        set -a lines "- $report"
    end
end

set -a lines "" $routes
block $lines
