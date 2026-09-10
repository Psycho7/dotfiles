#!/usr/bin/env fish
# PreToolUse Agent hook: refuses a rikki or sakichan dispatch whose envelope
# is missing, malformed, points at a report path that is already taken, or
# names a report that is not finished.
# Reads the hook JSON on stdin (tool_name, tool_input.subagent_type,
# tool_input.prompt, cwd, session_id, optional scratchpad_dir).
# Allow prints nothing and, for sakichan, marks the pending entry verifying;
# deny prints a permission decision whose reason names the failed check and
# shows a skeleton envelope with that field marked.
# Fails closed: any internal error denies too.

source (status dirname)/lib/gate-state.fish

set -g agent ""

function skeleton --argument-names type field note
    set -l lines "dispatch:" "  cwd: /abs/path/to/repo"
    if test "$type" = rikki
        set -a lines "  branch: main"
    end
    set -a lines "  report: /abs/path/to/report.md" "  criteria:" "    - first acceptance criterion"
    if test "$type" = rikki
        set -a lines "  verify: command to run" "  commit: false"
    end
    set -a lines "  brief: /abs/path/to/brief.md   # optional"

    for line in $lines
        if test -n "$field"; and string match -q -- "  $field:*" $line
            printf '%s   # <-- %s\n' $line $note
        else
            printf '%s\n' $line
        end
    end
end

# jq joins the reason, because a fish command substitution would split it
# back into one argument per line.
function deny --argument-names check field note
    set -l lines "Dispatch refused: $check" "" "Expected envelope:" '```yaml' (skeleton $agent $field $note) '```'
    jq -n '{hookSpecificOutput: {hookEventName: "PreToolUse", permissionDecision: "deny", permissionDecisionReason: ($ARGS.positional | join("\n"))}}' --args $lines
    exit 0
end

function field_type --argument-names json name
    printf '%s' $json | jq -r --arg k $name '.[$k] | type' 2>/dev/null
end

function field_value --argument-names json name
    printf '%s' $json | jq -r --arg k $name '.[$k] // "" | tostring' 2>/dev/null
end

function require_string --argument-names json name absolute
    set -l type (field_type $json $name)
    if test "$type" = null
        deny "envelope has no `$name`." $name "missing"
    end
    if test "$type" != string
        deny "envelope field `$name` must be a string, got $type." $name "must be a string"
    end

    set -l value (field_value $json $name)
    if test -z "$value"
        deny "envelope field `$name` is empty." $name "must not be empty"
    end
    if test "$absolute" = yes; and not string match -q '/*' -- $value
        deny "envelope field `$name` must be an absolute path, got `$value`." $name "must be an absolute path"
    end
end

function require_criteria --argument-names json
    set -l type (field_type $json criteria)
    if test "$type" = null
        deny "envelope has no `criteria`." criteria "missing"
    end
    if test "$type" != array
        deny "envelope field `criteria` must be a list of strings, got $type." criteria "must be a list of strings"
    end

    if test (printf '%s' $json | jq -r '.criteria | length') -eq 0
        deny "envelope field `criteria` is empty." criteria "needs at least one criterion"
    end

    set -l bad (printf '%s' $json | jq -r '[.criteria[] | select((type != "string") or (. == ""))] | length' 2>/dev/null)
    if test "$bad" != 0
        deny "envelope field `criteria` has an entry that is not a non-empty string." criteria "each entry is a non-empty string"
    end
end

# Prints the body of the first fenced yaml block in the prompt.
function yaml_block
    awk '
        /^[[:space:]]*```[[:space:]]*(yaml|yml)[[:space:]]*$/ { if (!started) { started = 1; next } }
        started && /^[[:space:]]*```/ { exit }
        started { print }
    '
end

set -l input (cat)
if test -z "$input"
    set agent rikki
    deny "the hook received no input." "" ""
end

if not printf '%s' $input | jq -e . >/dev/null 2>&1
    set agent rikki
    deny "the hook input is not valid JSON." "" ""
end

set agent (printf '%s' $input | jq -r '.tool_input.subagent_type // empty')
if test "$agent" != rikki -a "$agent" != sakichan
    exit 0
end

if not type -q yq
    deny "`yq` is not installed, so the envelope cannot be parsed." "" ""
end

set -l prompt (printf '%s' $input | jq -r '.tool_input.prompt // empty')
set -l block (printf '%s\n' $prompt | yaml_block)
if test (count $block) -eq 0
    deny "the prompt has no fenced `yaml` dispatch envelope." "" ""
end

set -l envelope (printf '%s\n' $block | yq -o=json -I0 '.' 2>/dev/null)
if test $status -ne 0 -o -z "$envelope"
    deny "the fenced `yaml` block is not valid YAML." "" ""
end

set -l dispatch (printf '%s' $envelope | jq -c '.dispatch // empty' 2>/dev/null)
if test -z "$dispatch"
    deny "the envelope has no top-level `dispatch` key." "" ""
end
if test (printf '%s' $dispatch | jq -r 'type') != "object"
    deny "the `dispatch` key must be a mapping." "" ""
end

require_string $dispatch cwd yes
require_string $dispatch report yes
require_criteria $dispatch
if test (field_type $dispatch brief) != null
    require_string $dispatch brief yes
end

set -l cwd (field_value $dispatch cwd)
set -l report (field_value $dispatch report)
if not test -d $cwd
    deny "`cwd` is not an existing directory: $cwd" cwd "must be an existing directory"
end

set -l scratchpad (printf '%s' $input | jq -r '.scratchpad_dir // empty')
set -l session (printf '%s' $input | jq -r '.session_id // empty')
if not state_dir "$scratchpad" "$session" >/dev/null
    deny "the gate state directory cannot be created." "" ""
end
set -l key (key_of $report)

if test "$agent" = rikki
    require_string $dispatch branch no
    require_string $dispatch verify no
    set -l commit_type (field_type $dispatch commit)
    if test "$commit_type" = null
        deny "envelope has no `commit`." commit "missing"
    end
    if test "$commit_type" != boolean
        deny "envelope field `commit` must be true or false, got $commit_type." commit "must be true or false"
    end

    if test -e $report
        deny "the report path already exists: $report" report "pick a path that does not exist yet"
    end
    if test -e $gate_dir/inflight/$key
        deny "another rikki is already in flight for this report path: $report" report "pick a fresh report path"
    end
    if test -e $gate_dir/pending/$key
        deny "this report path is already pending verification: $report" report "pick a fresh report path"
    end

    set -l head (git -C $cwd rev-parse HEAD 2>/dev/null)
    set -l branch (field_value $dispatch branch)
    if not inflight_add $key $report $cwd $branch "$head"
        deny "the gate state directory is not writable." "" ""
    end
    exit 0
end

# sakichan
if not test -f $report
    deny "the report to verify does not exist: $report" report "must be an existing rikki report"
end

# Only a finished report can be verified; a rikki that stopped for input has
# to be resumed first, and its report carries no base to compare.
set -l report_status (yq --front-matter=extract -r '.status // ""' $report 2>/dev/null)
if contains -- "$report_status" NEEDS_CONTEXT BLOCKED
    deny "report status is $report_status; resume rikki first" report "must be a DONE or DONE_WITH_CONCERNS report"
end

set -l base (yq --front-matter=extract -r '.base // ""' $report 2>/dev/null)
if test $status -ne 0
    deny "the report front matter is not valid YAML: $report" report "rikki must rewrite the report"
end
if not string match -qr '^[0-9a-f]{40}$' -- "$base"
    deny "the report front matter has no 40-hex `base`: $report" report "rikki must record the starting HEAD"
end
if not git -C $cwd rev-parse --verify --quiet "$base^{commit}" >/dev/null 2>&1
    deny "the report `base` $base is not a commit in $cwd" cwd "must be the repo holding the reported base commit"
end

set -l recorded ""
for marker in $gate_dir/pending/$key $gate_dir/inflight/$key
    if test -f $marker
        set recorded (marker_get $marker head)
        break
    end
end
if test -n "$recorded" -a "$recorded" != "$base"
    deny "the report `base` $base differs from the HEAD recorded at dispatch, $recorded." report "must be the report of the rikki that started at $recorded"
end

# Allowed, so a verifier is about to run: the entry stops blocking Stop until
# this sakichan reports a verdict. A deny never reaches here, so a refused
# dispatch leaves the entry untouched.
pending_verifying $key
exit 0
