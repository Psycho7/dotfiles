#!/usr/bin/fish
# zai-delegate - Run a search prompt through GLM headlessly
# Usage: zai-delegate <prompt> <project_dir> [project_dir ...]

if test (count $argv) -lt 2
    echo "Usage: zai-delegate <prompt> <project_dir> [project_dir ...]" >&2
    exit 1
end

set prompt $argv[1]
set dirs $argv[2..-1]

# Resolve to absolute paths and build --add-dir flags
set add_dir_args
for dir in $dirs
    set -a add_dir_args --add-dir (realpath $dir)
end

set script_dir (realpath (status dirname))

printf '%s' $prompt | glm -p --model Haiku $add_dir_args \
    --allowedTools "Read,Glob,Grep,Bash" \
    --permission-mode default \
    --append-system-prompt-file $script_dir/../prompts/explore.md

set glm_status $status
if test $glm_status -ne 0
    echo "zai-delegate: GLM exited with code $glm_status" >&2
    date +%s > ~/.claude/.zai-delegate-failed
else
    rm -f ~/.claude/.zai-delegate-failed
end
exit $glm_status