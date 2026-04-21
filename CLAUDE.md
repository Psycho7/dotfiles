# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Dotfiles managed with [chezmoi](https://www.chezmoi.io/). The chezmoi source root is `home/` (per `.chezmoiroot`), which maps to `$HOME` on the target machine.

Use the `chezmoi` skill when creating or modifying chezmoi-managed files — it covers file type selection, template syntax, modify scripts, cross-platform handling, and `.chezmoiignore` configuration.

## Key Commands

```bash
# Apply changes to the local machine
chezmoi apply

# Preview what would change
chezmoi diff

# Re-run a run_once script (after modifying it)
chezmoi state delete-bucket --bucket=scriptState && chezmoi apply
```

## Architecture

### Platform Use Cases

Each supported OS has a distinct intended use case. The current `.chezmoiignore` rules, install scripts, and prompt defaults all encode these assumptions — respect them when adding or modifying anything platform-specific.

- **macOS** — primary dev + daily-driver desktop. Full surface: fish + functions, Nerd Font, Claude Code, Tailscale helpers, GUI-adjacent tooling. Desktop-dev additions are in scope.
- **Windows** — daily use, gaming, *partial* dev. Keep the surface minimal: PowerShell profile + a short winget CLI toolchain. Do not add fish, Nerd Fonts, or Claude Code. Prefer winget over manual installers.
- **Linux (Debian/Ubuntu)** — **always headless** (WSL or a VM without a desktop environment). CLI + fish + Claude Code only. Do not add Nerd Fonts, GUI apps, desktop-only helpers, or user-level GUI systemd services. Tailscale fish helpers remain macOS-only because the macOS box is the Tailscale node in this setup.

When in doubt, ask before expanding a platform's surface beyond what is listed above.

### Chezmoi File Naming Conventions

| Prefix/suffix | Meaning |
|---|---|
| `dot_` | Maps to `.` in target (e.g., `dot_gitconfig` → `~/.gitconfig`) |
| `.tmpl` | Go template; variables like `{{ .chezmoi.os }}`, `{{ .email }}` |
| `modify_` | Script that reads existing file on stdin, outputs merged result to stdout |
| `run_once_` | Script that runs once on first `chezmoi apply` (tracked by content hash) |
| `executable_` | File is installed with executable permission |

### Modify Scripts Pattern

Files prefixed `modify_` implement a "managed block" merge: they preserve user customizations outside a `# BEGIN chezmoi managed` / `# END chezmoi managed` block while injecting chezmoi-owned content. This is the preferred pattern for config files users also edit manually (fish config, git ignore, PowerShell profile, Claude settings).

The Claude `modify_settings.json` uses `jq` to additively merge baseline permissions — it never removes permissions the user has added locally.

### Platform Handling

- `home/.chezmoiignore` excludes platform-specific files (PowerShell on non-Windows; fish/git-ignore/Claude on Windows; Tailscale fish functions on non-macOS; fish `conf.d` everywhere)
- Templates use `{{ if eq .chezmoi.os "darwin" }}` guards
- `run_once_00_install_packages.sh.tmpl` handles macOS (Homebrew) and Linux (apt + manual installers); `.ps1.tmpl` handles Windows (winget)
- The Linux branch intentionally installs no fonts or GUI packages — the Linux target is headless (WSL/VM), so there is no `desktop-vs-headless` split to maintain

### CI / GitHub Actions

- PowerShell `run:` values that start with `"` must use block scalar (`|`) — bare double-quoted YAML strings break on backslashes and `|` pipe characters.

### What's Managed

- **Git**: `dot_gitconfig.tmpl` (identity + includes), `dot_config/git/aliases.gitconfig`, `dot_config/git/modify_ignore`
- **Fish shell**: `dot_config/fish/modify_config.fish.tmpl` + functions in `dot_config/fish/functions/`
- **PowerShell**: `Documents/PowerShell/modify_Microsoft.PowerShell_profile.ps1.ps1`
- **Starship prompt**: `dot_config/starship.toml`
- **Claude Code**: `dot_claude/CLAUDE.md`, `dot_claude/modify_settings.json`, `dot_claude/skills/`

### What's Excluded

Work configs, conda, SSH keys, and linuxbrew are intentionally not managed.
