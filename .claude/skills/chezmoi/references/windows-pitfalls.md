# Windows-Specific Pitfalls

## 1. Use PowerShell 7 (`pwsh`), not Windows PowerShell 5.1

Chezmoi defaults to `pwsh` for `.ps1` scripts, falling back to `powershell.exe` (5.1) if not found. PowerShell 5.1 defaults to `Restricted` execution policy — scripts silently fail.

Configure explicitly:

```yaml
# .chezmoi.yaml.tmpl
{{- if eq .chezmoi.os "windows" }}
interpreters:
  ps1:
    command: pwsh
    args:
      - "-NoLogo"
      - "-NoProfile"
      - "-NonInteractive"
      - "-ExecutionPolicy"
      - "Bypass"
      - "-File"
{{- end }}
```

In CI, also set policy before `chezmoi apply`:

```yaml
- name: Allow PowerShell scripts
  if: runner.os == 'Windows'
  shell: pwsh
  run: Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope CurrentUser -Force
```

## 2. Double-extension trap

Chezmoi strips recognized interpreter extensions from modify script filenames. If the target also has one of these extensions, double it:

```
modify_Microsoft.PowerShell_profile.ps1      → Microsoft.PowerShell_profile  (WRONG)
modify_Microsoft.PowerShell_profile.ps1.ps1  → Microsoft.PowerShell_profile.ps1  (CORRECT)
```

Recognized extensions: `.sh`, `.ps1`, `.py`, `.pl`, `.rb`, `.nu`

## 3. Guard external tool invocations

On fresh machines, tools aren't installed yet:

```powershell
# PowerShell
if (Get-Command starship -ErrorAction SilentlyContinue) {
    Invoke-Expression (&starship init powershell)
}
```

```bash
# bash
command -v starship &>/dev/null && eval "$(starship init bash)"
```

```fish
# fish
type -q starship && starship init fish | source
```

## 4. PowerShell array range semantics

The `..` range operator counts *through* negative indices instead of producing an empty array:

```powershell
0..3      # @(0, 1, 2, 3)
0..0      # @(0)
0..-1     # @(0, -1) — NOT empty!
```

Use `Select-Object -SkipLast N`:

```powershell
# WRONG
$output = $output[0..($output.Count - 2)]

# CORRECT
$output = @($output | Select-Object -SkipLast 1)
```

## 5. GitHub Actions YAML quoting

Any `run:` value starting with `"` is parsed as YAML double-quoted string where `\` is escape and `|` has special meaning:

```yaml
# WRONG
- run: "$env:USERPROFILE\.local\bin" | Out-File -Append "$env:GITHUB_PATH"

# CORRECT
- run: |
    "$env:USERPROFILE\.local\bin" | Out-File -Append "$env:GITHUB_PATH"
```

## 6. `.chezmoi.yaml.tmpl` must be inside chezmoiroot

If the repo uses `.chezmoiroot` (e.g., `home/`), the config template must be inside that directory:

```
repo-root/
  .chezmoiroot          ← contains "home"
  home/
    .chezmoi.yaml.tmpl   ← MUST be here, not at repo root
```

## 7. Path and config differences

| Concept | Unix | Windows |
|---|---|---|
| Home directory | `$HOME` | `$env:USERPROFILE` |
| PATH separator | `:` | `;` |
| Path separator | `/` | `\` (use `Join-Path`) |
| Profile location | `~/.config/...` | `~/Documents/PowerShell/...` |
| Config directory | `~/.config/` | `~/Documents/` or `~/AppData/` |

## 8. Don't install the running shell

A `run_once_` PowerShell script that tries to `winget install Microsoft.PowerShell` will fail — the MSI can't upgrade a running process. PowerShell is already installed if your script is running.

