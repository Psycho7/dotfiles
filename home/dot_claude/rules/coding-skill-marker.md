---
paths: "**/SKILL.md"
---

When writing or editing a skill, check whether it sets coding style or principles for writing code, such as a language style guide or coding conventions. Such a skill carries this front matter so subagents like rikki may invoke it; workflow, review, and other skills do not:

```yaml
metadata:
  coding-skill: "true"
```

If the marker looks needed or misplaced, ask the user before adding or removing it. A subagent reports it instead.
