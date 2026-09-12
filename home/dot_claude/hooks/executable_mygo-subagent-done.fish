#!/usr/bin/env fish
# SubagentStop hook for rikki and sakichan. Reads the hook JSON on stdin
# (agent_id, agent_type, last_assistant_message, stop_hook_active,
# session_id, optional scratchpad_dir).
#
# rikki: the final message must be "Report: <absolute path>"; the report
# front matter is the sole authority for status. A valid DONE report becomes
# a pending entry and NEEDS_CONTEXT or BLOCKED pends nothing, keeping the
# inflight marker so a rikki resumed with SendMessage still has its cwd,
# branch and starting head to carry into pending. An invalid report is sent
# back once (tracked in retry/, never inferred from stop_hook_active) and
# marked invalid on the second try. Every valid status records agent_id on the
# marker it leaves behind, so a SubagentStart for the same rikki finds it.
# sakichan: the final message must be "Verdict: <absolute path>"; only the
# verdict Complete clears the pending entry. sakichan is never blocked. A
# malformed message is an error entry only while some entry is being
# verified; otherwise it is a stray wake-up and ignored.

source (status dirname)/lib/mygo-gate-state.fish

set -g report_checks '
def ok_str: (type == "string") and (. != "");
def is_sha: (type == "string") and test("^[0-9a-f]{40}$");
[
  (if (.status | IN("DONE", "DONE_WITH_CONCERNS", "NEEDS_CONTEXT", "BLOCKED") | not)
   then "front matter: status must be DONE, DONE_WITH_CONCERNS, NEEDS_CONTEXT or BLOCKED" else empty end),
  (if (.worktree != null) and (.worktree | ok_str | not)
   then "front matter: worktree must be a non-empty string when present" else empty end)
]
+ (if (.status == "DONE") or (.status == "DONE_WITH_CONCERNS") then
[
  (if $head == "none" then
     (if (.base // "") != ""
      then "front matter: the dispatch cwd had no HEAD commit, so base must be omitted" else empty end)
   else
     (if (.base | is_sha | not)
      then "front matter: base must be the full 40-hex SHA of the starting HEAD" else empty end)
   end),
  (if (.branch != null) and (.branch | ok_str | not)
   then "front matter: branch must be a non-empty string when present" else empty end),
  (if ((.files | type) != "array") or ((.files | length) == 0)
   then "front matter: files must be a non-empty list" else empty end),
  (if ((.files | type) == "array")
      and (([.files[] | select((.path | ok_str | not) or (.lines | ok_str | not))] | length) > 0)
   then "front matter: every files entry needs a non-empty path and a lines string" else empty end),
  (if ((.tests | type) != "array") or ((.tests | length) == 0)
   then "front matter: tests must be a non-empty list" else empty end),
  (if ((.tests | type) == "array")
      and (([.tests[] | select((.phase | IN("before", "after") | not) or (.command | ok_str | not)
                               or ((.exit | type) != "number") or (.result | ok_str | not))] | length) > 0)
   then "front matter: every tests entry needs phase before|after, command, exit and result" else empty end),
  (if ((.tests | type) == "array") and (([.tests[] | select(.phase == "after")] | length) == 0)
   then "front matter: tests needs an entry with phase: after" else empty end)
] else [] end)
| .[]
'

# Every argument is one line of the reason; jq joins them, because a fish
# command substitution would split a joined string back into a list.
function block
    jq -n '{decision: "block", reason: ($ARGS.positional | join("\n"))}' --args $argv
    exit 0
end

function error_entry --argument-names id detail
    set -l key "_error-"(key_of $id)
    marker_write $gate_dir/pending/$key "report: (none)" "cwd: " "branch: " "head: " "verdict: error: $detail"
end

# True while a sakichan is expected to report (the dispatch guard marks her
# entry verifying). A sakichan woken again after her verdict, by a background
# command ending hours later, finds none; her stray message must not reopen
# the gate.
function any_verifying
    for marker in (pending_list)
        test (marker_get $marker state) = verifying; and return 0
    end
    return 1
end

# A verdict for a key with no pending entry: an inflight marker means the rikki
# stopped NEEDS_CONTEXT or BLOCKED and the parent verified it anyway, so promote
# the marker and keep its cwd, branch, head and rikki agent_id instead of
# rebuilding the entry empty. Returns 1 when there is nothing to promote.
function pending_from_inflight --argument-names key report
    if test -e $gate_dir/pending/$key
        return 0
    end
    test -e $gate_dir/inflight/$key; or return 1

    inflight_to_pending $key $report ""
end

# Non-empty lines of the final message, so trailing blanks do not fail the
# grammar.
function message_lines --argument-names msg
    printf '%s\n' $msg | string match -r -v '^\s*$'
end

# The absolute path after "<label>: ", or nothing when the line is not
# exactly that shape (a single label, one space, a path with no whitespace
# right after the slash).
function absolute_path_after --argument-names label line
    string match -q -- "$label: /*" $line; or return 1
    set -l path (string replace -- "$label: " '' $line)
    test (string length -- $path) -gt 1; or return 1
    string match -qr -- '^/\s' $path; and return 1
    printf '%s\n' $path
end

function has_question_section --argument-names report
    grep -qE '^#{1,6} *Question' $report
end

# head is the starting HEAD recorded at dispatch: "none" means the cwd had no
# HEAD commit, so the report must not carry a base. Empty means the marker
# is gone and the strict checks apply.
function report_problems --argument-names report head
    if not test -f $report
        printf '%s\n' "the report file does not exist: $report"
        return
    end

    set -l json
    if not set json (yq --front-matter=extract -o=json -I0 '.' $report 2>/dev/null); or test -z "$json"
        printf '%s\n' "the report front matter is missing or not valid YAML"
        return
    end

    set -l problems
    if not set problems (printf '%s' $json | jq -r --arg head "$head" $report_checks 2>/dev/null)
        printf '%s\n' "the report front matter is not a mapping"
        return
    end

    set -l status_value (printf '%s' $json | jq -r '.status // ""')
    if contains -- $status_value NEEDS_CONTEXT BLOCKED
        if not has_question_section $report
            set -a problems "body: NEEDS_CONTEXT and BLOCKED need a Question section"
        end
    end

    if test (count $problems) -gt 0
        printf '%s\n' $problems
    end
end

set -l input (cat)
set -l agent (printf '%s' $input | jq -r '.agent_type // empty' 2>/dev/null)
if test "$agent" != rikki -a "$agent" != sakichan
    exit 0
end

set -l agent_id (printf '%s' $input | jq -r '.agent_id // "unknown"')
set -l msg (printf '%s' $input | jq -r '.last_assistant_message // ""')
set -l scratchpad (printf '%s' $input | jq -r '.scratchpad_dir // empty')
set -l session (printf '%s' $input | jq -r '.session_id // empty')
if not state_dir "$scratchpad" "$session" >/dev/null
    if test "$agent" = rikki
        block "The verification gate state directory cannot be created, so this completion cannot be recorded. Report the failure to the parent."
    end
    exit 0
end

set -l lines (message_lines $msg)

if test "$agent" = sakichan
    set -l verdict_file
    if test (count $lines) -ne 1; or not set verdict_file (absolute_path_after Verdict $lines[1])
        any_verifying; and error_entry $agent_id "sakichan final message was not exactly 'Verdict: <absolute path>'"
        exit 0
    end

    set -l derived (string replace -r '\.verdict\.md$' .md -- $verdict_file)
    set -l json (yq --front-matter=extract -o=json -I0 '.' $verdict_file 2>/dev/null)
    if test $status -ne 0 -o -z "$json"
        set -l key (key_of $derived)
        if pending_from_inflight $key $derived
            pending_annotate $key unreadable $derived
        else
            error_entry $agent_id "the verdict file is missing or unreadable: $verdict_file"
        end
        exit 0
    end

    set -l report (printf '%s' $json | jq -r '.report // ""')
    test -n "$report"; or set report $derived
    set -l verdict (printf '%s' $json | jq -r '.verdict // ""')
    set -l failed (printf '%s' $json | jq -r '.failed // "" | tostring')
    set -l key (key_of $report)

    if test "$verdict" != Complete
        pending_from_inflight $key $report
    end

    switch $verdict
        case Complete
            pending_rm $key
        case Incomplete
            test -n "$failed"; or set failed "?"
            pending_annotate $key "Incomplete ($failed failed)" $report
        case "Cannot verify"
            pending_annotate $key "Cannot verify" $report
        case '*'
            pending_annotate $key unreadable $report
    end
    exit 0
end

# rikki
set -l report
if test (count $lines) -lt 1 -o (count $lines) -gt 2; or not set report (absolute_path_after Report $lines[1])
    set -l key "_agent-"(key_of $agent_id)
    if retry_bump $key
        block "Your final message must be exactly one line, 'Report: <absolute path to the report>'. For NEEDS_CONTEXT or BLOCKED a second line carries the question or blocker. Nothing else. Write the report file if you have not, then finish with that message."
    end
    marker_write $gate_dir/pending/$key "report: (unknown)" "cwd: " "branch: " "head: " "verdict: invalid: final message did not name a report"
    exit 0
end

set -l key (key_of $report)
set -l problems (report_problems $report (recorded_head $key | string collect -a))

if test (count $problems) -gt 0
    if retry_bump $key
        set -l bullets
        for item in $problems
            set -a bullets "- $item"
        end
        block "The verification gate rejected your report $report:" $bullets "Fix the report file and finish again with 'Report: $report'."
    end
    inflight_to_pending $key $report $agent_id
    pending_annotate $key invalid $report
    exit 0
end

set -l status_value (yq --front-matter=extract -r '.status' $report 2>/dev/null)
if contains -- $status_value DONE DONE_WITH_CONCERNS
    inflight_to_pending $key $report $agent_id
else
    marker_set_field $gate_dir/inflight/$key agent_id $agent_id
end
exit 0
