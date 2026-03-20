# dotfiles

Managed with [chezmoi](https://www.chezmoi.io/).

## Quick Start

### macOS / Linux (Debian/Ubuntu)
```bash
sh -c "$(curl -fsLS get.chezmoi.io)" -- init --apply https://github.com/Psycho7/dotfiles.git
```

### Windows (PowerShell)
```powershell
winget install twpayne.chezmoi
chezmoi init --apply https://github.com/Psycho7/dotfiles.git
```

## What's Included

- Git configuration and aliases
- Fish shell config (macOS/Linux)
- PowerShell profile (Windows)
- Starship prompt
- Claude Code configuration

## Related

- [vimrc](https://github.com/Psycho7/vimrc) - VIM configuration (separate repo)

## Manual Steps After Bootstrap

1. Install a Nerd Font (e.g., Fira Code Nerd Font) and configure terminal to use it
2. Configure SSH keys for GitHub, etc.
3. Add machine-specific Claude permissions if needed
4. Set up VIM using the separate vimrc repo
