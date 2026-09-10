#!/usr/bin/env fish
# SubagentStart hook for rikki. Reads the hook JSON on stdin (agent_id,
# agent_type, session_id, optional scratchpad_dir).
#
# A SendMessage resume starts the same agent_id again, so the pending entry
# that rikki left behind is marked resumed: the Stop gate lists it without
# blocking, which lets the parent yield while the rikki works. The next
# SubagentStop rewrites the entry as unverified and the gate blocks again.
# A fresh dispatch has no pending entry for its agent_id and nothing happens,
# and so does a resume that matches an inflight marker instead, left by a rikki
# that stopped NEEDS_CONTEXT or BLOCKED: an inflight entry never blocks Stop.

source (status dirname)/lib/mygo-gate-state.fish

set -l input (cat)
set -l agent (printf '%s' $input | jq -r '.agent_type // empty' 2>/dev/null)
test "$agent" = rikki; or exit 0

set -l agent_id (printf '%s' $input | jq -r '.agent_id // empty' 2>/dev/null)
test -n "$agent_id"; or exit 0

set -l scratchpad (printf '%s' $input | jq -r '.scratchpad_dir // empty')
set -l session (printf '%s' $input | jq -r '.session_id // empty')
state_dir "$scratchpad" "$session" >/dev/null; or exit 0

for marker in (pending_list)
    set -l recorded (marker_get $marker agent_id)
    if test "$recorded" = "$agent_id"
        marker_set_state $marker resumed
        break
    end
end
exit 0
