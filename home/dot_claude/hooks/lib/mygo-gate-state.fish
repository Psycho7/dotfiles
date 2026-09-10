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
# head is the commit rikki started from, or "none" when the dispatch cwd had
# no HEAD commit (not a repository, or no commits yet).

# Resolves the state dir, creates it, and leaves it in the global gate_dir.
# Order: MYGO_VERIFICATION_GATE_DIR (tests), the hook input scratchpad_dir,
# then a per-session dir under the temp dir, so the state is reaped with the
# temp dir instead of accumulating under $HOME. The per-uid root is created
# 0700 and must be owned by us: on Linux the temp dir is the shared, sticky
# /tmp, where any local user could otherwise pre-create that name and delete
# a pending marker, which would fail the gate open.
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
        set -l root (string trim -r -c / -- $tmp)/claude-(id -u)
        mkdir -m 700 -p $root 2>/dev/null
        test -d $root -a -O $root; or return 1
        set dir $root/verification-gate/$session
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

# Prints the value of the first "<field>: <value>" line; a bare "<field>:"
# line prints an empty line. marker_write always puts one space after the
# colon, so stripping leading spaces is enough.
function marker_get --argument-names path field
    test -f "$path"; or return 1
    for line in (cat $path 2>/dev/null)
        string match -q -- "$field:*" $line; or continue
        set -l value (string sub -s (math (string length -- $field) + 2) -- $line)
        printf '%s\n' (string trim -l -c ' ' -- $value | string collect)
        return 0
    end
    return 1
end

# The starting HEAD recorded for a report key: a commit SHA, or "none" when
# the dispatch cwd had no HEAD commit. The pending marker wins over the
# inflight one after a resume. Prints nothing when no marker is left.
function recorded_head --argument-names key
    for marker in $gate_dir/pending/$key $gate_dir/inflight/$key
        if test -f $marker
            marker_get $marker head
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
        if string match -q -- "$field:*" $line
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
