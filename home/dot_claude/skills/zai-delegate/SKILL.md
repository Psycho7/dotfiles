---
name: zai-delegate
description: Delegate task to GLM model from zAI
---

## How to Delegate

First, extract the absolute path of the folders to search, default to the project folder if missing.
Then use the bundled script `${CLAUDE_SKILL_DIR}/scripts/zai-delegate.fish`:

```bash
fish ${CLAUDE_SKILL_DIR}/scripts/zai-delegate.fish "Your search prompt here" "." ["/path/to/other/dir" ...]
```

The first argument is your prompt. All remaining arguments are project directories, each passed as `--add-dir` to GLM. The script:
1. Appends a quality envelope to your prompt that enforces: intent analysis, parallel tool execution, structured output (FILES FOUND / ANSWER / GAPS), and failure conditions
2. Pipes the full prompt into `glm -p` headless with read-only tools (`--allowedTools "Read,Glob,Grep"` — no Bash, Write, or Edit)
3. Returns the output to stdout
4. Surfaces GLM errors to stderr and exits with GLM's exit code

This runs synchronously — the Bash call blocks until GLM finishes, and the output appears in the tool result. Honestly return that output to the caller, do NOT add any of your own text.