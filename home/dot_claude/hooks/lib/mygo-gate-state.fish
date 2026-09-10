# Shared state for the verification gate hooks. State is a directory of
# marker files, one file per fact, so every transition is an atomic mv, rm,
# or touch and no hook ever rewrites a shared document. Concurrency is left
# to the filesystem; there is no lock.
#
#   <state dir>/inflight/<key>   rikki dispatched, not yet completed
#   <state dir>/pending/<key>    report accepted, awaiting a Complete verdict
#   <state dir>/retry/<key>      one invalid completion already sent back
#
# key = the report path with every "/" replaced by "%".
# Marker files hold "field: value" lines: report, cwd, branch, head, agent_id,
# verdict, and, while a sakichan runs or a resumed rikki works, state.

# Resolves the state dir, creates it, and leaves it in the global gate_dir.
# Order: MYGO_VERIFICATION_GATE_DIR (tests), the hook input scratchpad_dir,
# then a per-session dir under the temp dir, so the state is discarded with
# the rest of /tmp instead of accumulating under $HOME.
function state_dir --argument-names scratchpad session
    set -l dir
    if set -q MYGO_VERIFICATION_GATE_DIR; and test -n "$MYGO_VERIFICATION_GATE_DIR"
        set dir $MYGO_VERIFICATION_GATE_DIR
    else if test -n "$scratchpad"
        set dir $scratchpad/verification-gate
    else
        test -n "$session"; or set session unknown-session
        set -l tmp $TMPDIR
        test -n "$tmp"; or set tmp /tmp
        set dir (string trim -r -c / -- $tmp)/claude-(id -u)/verification-gate/$session
    end

    set -g gate_dir $dir
    mkdir -p $dir/inflight $dir/pending $dir/retry 2>/dev/null; or return 1
    printf '%s\n' $dir
end

function key_of --argument-names report
    string replace -a / % -- $report
end

# Writes the remaining arguments as lines of <path>, atomically.
function marker_write --argument-names path
    set -l dir (dirname $path)
    set -l tmp (mktemp $dir/.tmp.XXXXXX 2>/dev/null); or return 1
    if test (count $argv) -gt 1
        printf '%s\n' $argv[2..] >$tmp
    else
        printf '' >$tmp
    end
    mv -f $tmp $path
end

function marker_get --argument-names path field
    test -f "$path"; or return 1
    for line in (cat $path 2>/dev/null)
        set -l m (string match -r '^'$field': ?(.*)$' -- $line)
        if test (count $m) -ge 2
            printf '%s\n' $m[2]
            return 0
        else if test (count $m) -eq 1
            printf '\n'
            return 0
        end
    end
    return 1
end

function inflight_add --argument-names key report cwd branch head
    marker_write $gate_dir/inflight/$key "report: $report" "cwd: $cwd" "branch: $branch" "head: $head"
end

# Creates or refreshes the pending entry for a completed rikki. Sources for
# cwd, branch and head, in order: an existing pending marker (a rikki that
# completes a second time after a resume, whose dispatch facts were recorded
# the first time), the inflight marker, then the report front matter, which
# carries no cwd and so leaves it empty.
# The agent_id recorded on a marker fills in when the caller passes none, so a
# sakichan verdict can promote an inflight entry without claiming it.
function inflight_to_pending --argument-names key report agent_id
    set -l src $gate_dir/inflight/$key
    set -l dst $gate_dir/pending/$key
    set -l cwd ""
    set -l branch ""
    set -l head ""
    if test -f $dst
        set cwd (marker_get $dst cwd)
        set branch (marker_get $dst branch)
        set head (marker_get $dst head)
        set -l recorded (marker_get $dst agent_id)
        test -n "$recorded"; and set agent_id $recorded
    else if test -f $src
        set cwd (marker_get $src cwd)
        set branch (marker_get $src branch)
        set head (marker_get $src head)
        set -l recorded (marker_get $src agent_id)
        test -n "$agent_id"; or set agent_id $recorded
    else if test -f "$report"
        set branch (yq --front-matter=extract -r '.branch // ""' $report 2>/dev/null)
        set head (yq --front-matter=extract -r '.base // ""' $report 2>/dev/null)
    end

    marker_write $dst "report: $report" "cwd: $cwd" "branch: $branch" "head: $head" "agent_id: $agent_id" "verdict: unverified"; or return 1
    rm -f $src
end

function pending_rm --argument-names key
    rm -f $gate_dir/pending/$key
end

function pending_annotate --argument-names key verdict report
    set -l dst $gate_dir/pending/$key
    set -l cwd ""
    set -l branch ""
    set -l head ""
    set -l agent_id ""
    if test -f $dst
        test -n "$report"; or set report (marker_get $dst report)
        set cwd (marker_get $dst cwd)
        set branch (marker_get $dst branch)
        set head (marker_get $dst head)
        set agent_id (marker_get $dst agent_id)
    end

    marker_write $dst "report: $report" "cwd: $cwd" "branch: $branch" "head: $head" "agent_id: $agent_id" "verdict: $verdict"
end

# Rewrites one "field: value" line of a marker, dropping any previous one.
function marker_set_field --argument-names path field value
    test -f $path; or return 1

    set -l lines
    for line in (cat $path 2>/dev/null)
        if string match -qr '^'$field':' -- $line
            continue
        end
        set -a lines $line
    end
    set -a lines "$field: $value"

    marker_write $path $lines
end

# Only the Stop gate reads the state line: an entry in state verifying or
# resumed is listed but does not block. Every other write rewrites the marker
# without the line, so a later verdict blocks again.
function marker_set_state --argument-names path state
    marker_set_field $path state $state
end

# Records that a sakichan is in flight for this entry.
function pending_verifying --argument-names key
    marker_set_state $gate_dir/pending/$key verifying
end

function pending_list
    find $gate_dir/pending -maxdepth 1 -type f 2>/dev/null | sort
end

function inflight_list
    find $gate_dir/inflight -maxdepth 1 -type f 2>/dev/null | sort
end

# Marks one invalid completion for this report. Returns 1 when a mark was
# already there, which means the retry has been spent.
function retry_bump --argument-names key
    set -l mark $gate_dir/retry/$key
    test -e $mark; and return 1
    touch $mark
    return 0
end
