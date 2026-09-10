# sakichan verdict

Markdown with YAML front matter. The front matter is parsed by the gate hooks with `yq --front-matter=extract` and is the sole authority for status; the body is for the reader.

Written to the report path with `.md` replaced by `.verdict.md`.

Front matter:

- `report`: the absolute path of the report verified.
- `verdict`: `Complete`, `Incomplete`, or `Cannot verify`.
- `failed`: the number of criteria that did not pass; `0` for `Complete`.

Body: a `Criteria` table (criterion or claim, verdict PASS/FAIL/CANNOT
VERIFY, evidence as file:line or a command with the relevant output lines),
then `Findings` (unreported drift and test-quality problems only, each with
severity Critical/Important/Minor, file:line, what is wrong, why it
matters; one line saying none if there are none).

````markdown
---
report: /tmp/scratch/reports/t1.md
verdict: Incomplete
failed: 1
---

## Criteria

| Criterion or claim | Verdict | Evidence |
|---|---|---|
| `validate` rejects an expired token | PASS | src/auth/token.py:31; `pytest tests/auth/test_token.py` -> 3 passed |
| Report claims 3 tests added | FAIL | tests/auth/test_token.py has 2 tests; the third is `@pytest.mark.skip` |

## Findings

- Important tests/auth/test_token.py:48 the expiry test is skipped, so the
  criterion it covers is not exercised.
- Minor src/auth/token.py:12 `validate` was private and is now
  module-level; the report's Concerns do not mention the widening.
````
