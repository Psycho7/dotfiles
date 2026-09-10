# Dispatch envelopes

Every dispatch prompt carries exactly one fenced `yaml` block with a
top-level `dispatch` key. The prose around it is the task and its context;
the block is the contract, and the dispatch guard parses only the block.

## rikki

```yaml
dispatch:
  cwd: /Users/me/project
  branch: main
  report: /tmp/scratch/reports/t1-parser.md
  brief: /tmp/scratch/brief.md
  criteria:
    - "parse() rejects a trailing comma with ParseError"
    - "tests/test_parser.py covers both the valid and the invalid case"
  verify: "bash -c 'cd /Users/me/project && pytest tests/test_parser.py'"
```

- `report` is absolute, unique per dispatch, and must not exist yet.
- `brief` is optional: a shared file when the task belongs to a plan.
- `verify` is optional; without it rikki runs the project's documented
  test command.

rikki writes the report to `report` (format in `report.md`) and
answers with one line, `Report: <absolute path>`.

## sakichan

```yaml
dispatch:
  cwd: /Users/me/project
  report: /tmp/scratch/reports/t1-parser.md
  brief: /tmp/scratch/brief.md
  criteria:
    - "parse() rejects a trailing comma with ParseError"
    - "tests/test_parser.py covers both the valid and the invalid case"
```

No base commit: the report's front matter carries it, and the guard checks
it against the HEAD recorded when rikki was dispatched. sakichan writes the
verdict next to the report (`.md` replaced by `.verdict.md`) and answers
with one line, `Verdict: <absolute path>`.
