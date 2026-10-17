---
name: coding-principles
description: Use when writing, editing, refactoring, or reviewing code in any language, before the first line is written, and whenever deciding how much to change or how to structure, name, comment, or expose it.
metadata:
  coding-skill: "true"
---

# Coding Principles

Language-agnostic rules for code the user maintains by hand. Language-specific
skills build on these and win on conflict.

## Simplicity

- Write the minimum code that solves the problem. Nothing speculative.
- No features, flexibility, or configurability beyond what was requested.
- No abstractions for single-use code.
- No error handling for impossible scenarios.

## Surgical changes

- Every changed line traces to the request. Clean up only your own mess.
- Do not "improve" adjacent code, comments, or formatting, and do not
  refactor what is not broken.
- Mention unrelated dead code; do not delete it.

## Tests

- Fix a bug by first writing a test that reproduces it.

## Write first, simplify later

- Prioritize working code. Duplication and verbosity are fine while in
  progress.
- Do not optimize mid-iteration while requirements shift or bugs are being
  fixed.
- Reuse functions, utilities, and tools already in the codebase or its
  dependencies before writing new ones.
- Simplify only at a natural boundary: a module, feature, or plan is
  complete and stable, and its tests pass. Skip simplification for
  throwaway, exploratory, or prototype code.

## Structure

- Single responsibility; avoid coincidental cohesion.
- Prefer duplication over the wrong abstraction.
- Name things after what they do, matching their siblings.
- Return or continue early. Keep nesting shallow.
- Name meaningful or recurring values as constants or enums. A value that
  comes from a spec (HTTP 200, a port, a magic byte, a timeout from an RFC)
  always gets a name. A self-explanatory one-off value stays inline.
- Separate logical blocks with a blank line so the reader can breathe.
- Brace every block, including a one-line `if`, in languages that allow
  omitting braces.

## Visibility and layering

- Start with the narrowest visibility that works.
- Widening within the same assembly or module (private to internal, file or
  package scope, `InternalsVisibleTo` for tests) is routine when the task
  needs it. Do it and mention it.
- Widening to public on a library or package surface, unsealing a type, or
  exposing a private field or setter is a design change. Prefer adding a
  narrow method over exposing the existing member. In an interactive
  session, ask first. In a subagent, do the minimal version and call it out
  in the report.
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
| Need to call `private` from the same assembly | Make it internal, mention it |
| Need to expose it outside the package | Ask, or in a subagent do the minimum and report it |
| Controller needs data | Go through the service layer, not the repository |
| Explaining a block | One short line: what, then why |
