# dotfiles

Managed with [chezmoi](https://www.chezmoi.io/).

## Quick Start

### macOS / Linux (Debian/Ubuntu)
```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply https://github.com/Psycho7/dotfiles.git
```

### Windows (PowerShell)
```powershell
winget install Microsoft.PowerShell
winget install twpayne.chezmoi
chezmoi init --apply https://github.com/Psycho7/dotfiles.git
```

> PowerShell 7 must be installed first — the install script runs as `.ps1` and requires `pwsh`.

## What's Included

- Git configuration and aliases
- Fish shell config (macOS/Linux)
- PowerShell profile (Windows)
- Starship prompt
- Claude Code configuration (optional, macOS/Linux only)

## Configuration Options

During `chezmoi init`, you'll be prompted:

| Prompt | Default | Description |
|---|---|---|
| Email address | `user@example.com` | Git identity |
| Full name | `User` | Git identity |
| Use Claude Code | `true` | Deploy Claude Code config, skills, ccstatusline (macOS/Linux only; always off on Windows) |

To change after initial setup, re-run `chezmoi init`.

## Keeping Up to Date

```bash
chezmoi update    # Pull from remote and apply
chezmoi diff      # Preview pending changes
chezmoi apply     # Apply without pulling
```

## Manual Steps After Bootstrap

1. Install a Nerd Font (e.g., Fira Code Nerd Font) and configure terminal to use it
2. Configure SSH keys for GitHub, etc.
3. Add machine-specific Claude permissions if needed
4. Set up VIM using the separate vimrc repo

## Related

- [vimrc](https://github.com/Psycho7/vimrc) - VIM configuration (separate repo)

## Attribution

Claude Code setup inspired by:

- [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT License)
- [centminmod/my-claude-code-setup](https://github.com/centminmod/my-claude-code-setup) ([MIT License](https://github.com/centminmod/my-claude-code-setup/blob/master/LICENSE))