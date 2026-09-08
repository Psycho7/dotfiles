---
name: coding-guidelines
description: Use when writing, refactoring, or reviewing code in any language, before the first line is written, and whenever deciding how to structure, name, comment, or expose it.
---

# Coding Guidelines

Language-agnostic rules for code the user maintains by hand. Language-specific
skills (`csharp-style`, etc.) build on these and win on conflict. The
behavioral principles (simplicity, surgical changes, test-first) live in the
global CLAUDE.md and are not repeated here.

## Structure

- Return or `continue` early. Keep nesting shallow; no arrow-shaped functions.
- Name meaningful or recurring values as constants or enums. A value that
  comes from a spec (HTTP 200, a port, a magic byte, a timeout from an RFC)
  always gets a name. A self-explanatory one-off value stays inline.
- Separate logical blocks with a blank line so the reader can breathe.
- Brace every block, including a one-line `if`, in languages that allow
  omitting braces.

## Visibility and layering

- Everything is private by default. Widening visibility (private to
  internal or public, exporting a symbol, opening a sealed type) is a design
  change: propose it and wait for approval instead of doing it silently.
- Keep low-level mechanics (raw I/O, sockets, parsing, hardware access)
  behind a dedicated layer that exposes domain-level operations.
- A layer talks only to the layer directly beneath it. Never bypass an
  intermediate layer, for example a UI component or controller calling
  storage or a raw network client directly.

## Comments

- A comment says what a block does and why, only where the code cannot show
  it: an algorithm choice, a spec-derived constant, a domain rule, a
  constraint the reader would otherwise trip over. Keep it short. Prefer a
  concrete example to prose; use an ASCII diagram for a system with several
  moving parts.
- Do not comment code you did not write or change in this task.
- No comments that restate the code, and no decorative banners.
- ASCII characters only in comments, docstrings, and file headers unless
  explicitly asked otherwise (no em-dashes, smart quotes, Unicode arrows).
- Do not reference external documentation, design docs, tickets, wikis, or
  other Markdown files from in-source text.

## Quick reference

| Situation | Do |
|---|---|
| Nested `if` three deep | Invert the condition and return early |
| Literal `200`, `8080`, `0x7F` | Named constant, even if used once |
| Need to call `private` from another type | Stop and ask before widening |
| Controller needs data | Go through the service layer, not the repository |
| Explaining a block | One short line: what, then why |
