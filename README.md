# dotfiles

Personal dotfiles managed with [chezmoi](https://www.chezmoi.io/), supporting macOS, Linux (Debian/Ubuntu), and Windows.

See [dev-environment](https://github.com/Psycho7/dev-environment) for rendered dotfiles on a real macOS instance.

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

## What Gets Installed

### macOS (via Homebrew)

| Package | Description |
|---|---|
| [fish](https://fishshell.com/) | Shell |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | Fast grep |
| [fd](https://github.com/sharkdp/fd) | Fast find |
| [jq](https://jqlang.github.io/jq/) | JSON processor |
| [starship](https://starship.rs/) | Cross-shell prompt |
| [zoxide](https://github.com/ajeetdsouza/zoxide) | Smarter `cd` |
| [Fira Code Nerd Font](https://www.nerdfonts.com/) | Terminal font (cask) |

### Linux (Debian/Ubuntu)

| Package | Description |
|---|---|
| [fish](https://fishshell.com/) | Shell (via apt) |
| [ripgrep](https://github.com/BurntSushi/ripgrep) | Fast grep (via apt) |
| [fd](https://github.com/sharkdp/fd) | Fast find (via apt as `fd-find`) |
| [jq](https://jqlang.github.io/jq/) | JSON processor (via apt) |
| [starship](https://starship.rs/) | Cross-shell prompt (via install script) |
| [zoxide](https://github.com/ajeetdsouza/zoxide) | Smarter `cd` (via install script) |

> Other Linux distros are not supported by the bootstrap script.

### Windows (winget)

| Package | winget ID |
|---|---|
| [ripgrep](https://github.com/BurntSushi/ripgrep) | `BurntSushi.ripgrep.MSVC` |
| [fd](https://github.com/sharkdp/fd) | `sharkdp.fd` |
| [jq](https://jqlang.github.io/jq/) | `jqlang.jq` |
| [starship](https://starship.rs/) | `Starship.Starship` |
| [zoxide](https://github.com/ajeetdsouza/zoxide) | `ajeetdsouza.zoxide` |

> Fish shell and Nerd Fonts are not installed on Windows. PowerShell is used instead.


## Configuration Options

During `chezmoi init`, you'll be prompted:

| Prompt | Default | Description |
|---|---|---|
| Email address | `user@example.com` | Git identity |
| Full name | `User` | Git identity |
| Use Claude Code | `true` | Deploy Claude Code config, skills, ccstatusline (macOS/Linux only; always `false` on Windows) |

To change after initial setup, re-run `chezmoi init`.

## Keeping Up to Date

```bash
chezmoi update    # Pull from remote and apply
chezmoi diff      # Preview pending changes
chezmoi apply     # Apply without pulling
```

## Related

- [vimrc](https://github.com/Psycho7/vimrc) - VIM configuration (separate repo)

## Attribution

Claude Code setup inspired by:

- [forrestchang/andrej-karpathy-skills](https://github.com/forrestchang/andrej-karpathy-skills) (MIT License)
- [centminmod/my-claude-code-setup](https://github.com/centminmod/my-claude-code-setup) ([MIT License](https://github.com/centminmod/my-claude-code-setup/blob/master/LICENSE))
