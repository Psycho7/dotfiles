---
name: chezmoi
description: >-
  Managing dotfiles with chezmoi — choosing the right file type (plain copy, template, modify script),
  handling cross-platform differences (macOS/Linux/Windows), writing managed-block modify scripts,
  configuring .chezmoiignore, and creating run scripts. Use this skill whenever working in a chezmoi-managed
  dotfiles repo: adding or editing managed files, creating new modify scripts, setting up platform-specific
  config, troubleshooting chezmoi apply/diff, or bootstrapping a new machine. Also use when the user asks
  about chezmoi conventions, template syntax, or how to structure their dotfiles for multiple platforms.
---

# Chezmoi Dotfiles Management

## 1. Choosing the Right Approach

Before creating or modifying a file, walk this decision tree:

```
Is the file identical on all platforms?
  YES → Plain copy (no .tmpl, no modify_)
  NO → Does chezmoi own the entire file?
    YES → Go template (.tmpl)
    NO → modify_ script (file is shared with programs/users)
      Is it structured data (JSON/YAML/TOML)?
        YES, simple key merge → modify_ with jq/yq deep merge
        YES, fine-grained control → modify_ with chezmoi:modify-template + setValueAtPath
        NO (line-based text) → modify_ with managed-block markers
```

### Quick reference

| Scenario | Source file pattern |
|---|---|
| Identical everywhere | `dot_editorconfig` |
| OS/machine-conditional sections | `dot_zshrc.tmpl` |
| Excluded on some OSes | `.chezmoiignore` entry |
| Partial JSON (add/override keys) | `modify_settings.json` (bash+jq) |
| Partial JSON/YAML/TOML (fine-grained) | `modify_` with `chezmoi:modify-template` |
| Partial text (shared with user) | `modify_` with managed-block markers |
| Package installation | `.chezmoiscripts/run_once_before_*.sh.tmpl` |
| Post-apply reload | `.chezmoiscripts/run_onchange_after_*` |

---

## 2. Data Hierarchy

Chezmoi merges template data from three layers (later overrides earlier):

1. **`.chezmoidata/`** — static defaults shared across all machines (cannot be templates)
2. **`.chezmoidata.$FORMAT`** — single-file variant
3. **Config `[data]`** — machine-specific, from `.chezmoi.toml.tmpl` at `chezmoi init`

Verify with: `chezmoi data | jq .`

For detailed examples of profile-based configuration, read `references/data-and-profiles.md` in this skill's directory.

---

## 3. Go Templates

Use `.tmpl` suffix when the file needs OS or machine-specific sections:

```
{{- if eq .chezmoi.os "darwin" }}
...macOS content...
{{- else if eq .chezmoi.os "linux" }}
...Linux content...
{{- else if eq .chezmoi.os "windows" }}
...Windows content...
{{- end }}
```

Place reusable snippets in `.chezmoitemplates/` and include with `{{ template "name.tmpl" . }}`. Always pass `.` explicitly.

---

## 4. Modify Scripts

### 4a. Managed-block pattern (text files)

The preferred pattern for config files that users also edit manually:

1. Read current file from stdin
2. Strip existing managed block (between `BEGIN` / `END` markers)
3. Rebuild managed block with chezmoi-controlled content
4. Output: preserved user content + new managed block

Rules:
- **Idempotency**: Modify scripts run on every `chezmoi apply`. Trim trailing blank lines before appending the managed block to prevent accumulation across repeated applies.
- **Interpreter**: Use bash even when targeting fish/zsh — chezmoi runs modify scripts before the target shell may be installed.
- **Templates**: Add `.tmpl` suffix for OS-conditional content inside the managed block.

### 4b. JSON deep merge (jq)

```bash
#!/bin/bash
MANAGED='{ "key": "value" }'
jq -s '.[0] * .[1]' - <(echo "$MANAGED")
```

### 4c. In-process modify-template

No external interpreter needed — works on all platforms:

```
{{- /* chezmoi:modify-template */ -}}
{{- $c := .chezmoi.stdin | fromToml -}}
{{- $c = $c | setValueAtPath "key" "value" -}}
{{- $c | toToml -}}
```

Parsers: `fromJson`/`toJson`/`toPrettyJson`, `fromYaml`/`toYaml`, `fromToml`/`toToml`.

For detailed examples of all modify patterns, read `references/modify-scripts.md` in this skill's directory.

---

## 5. .chezmoiignore

A Go template. Patterns match **target paths** (after `dot_`/`.tmpl`/`run_once_` stripping), not source filenames:

```
# CORRECT — target paths
{{- if ne .chezmoi.os "windows" }}
Documents/PowerShell
{{- end }}

# WRONG — source-style names silently never match:
# dot_config/fish          ← should be .config/fish
# run_once_00_install.ps1  ← should be 00_install.ps1
```

---

## 6. Run Scripts

| Prefix | Behavior |
|---|---|
| `run_before_` / `run_after_` | Before/after file deployment |
| `run_once_` | Only when content hash changes |
| `run_onchange_` | When referenced content changes |

Combine: `run_once_before_10-install-packages.sh.tmpl`

Use separate `.sh.tmpl` and `.ps1.tmpl` for cross-platform installs. For `run_onchange_`, embed a hash: `# hash: {{ include "dot_zshrc.tmpl" | sha256sum }}`.

Hooks (`hooks.*.pre/post` in config) run even on `--dry-run` — avoid destructive actions in hooks.

---

## 7. Windows Pitfalls

Read `references/windows-pitfalls.md` in this skill's directory for the full list. The critical ones:

1. **Configure `pwsh`** with `-ExecutionPolicy Bypass` in the `ps1` interpreter
2. **Double-extension trap**: target `.ps1` files need `modify_name.ps1.ps1`
3. **Guard tool invocations**: `if (Get-Command starship -ErrorAction SilentlyContinue) { ... }`
4. **Array ranges**: `0..-1` is `@(0, -1)` not empty — use `Select-Object -SkipLast`
5. **GitHub Actions**: Always `run: |` for PowerShell
6. **`.chezmoi.yaml.tmpl` with `.chezmoiroot`**: config template must be inside the chezmoiroot directory

---

## 8. Troubleshooting

```bash
chezmoi diff                    # Preview changes
chezmoi doctor                  # Diagnose issues
chezmoi data | jq .             # Show template data
chezmoi cat ~/.gitconfig        # Test-render a file
chezmoi managed --include=all   # List managed files
```

---

## 9. Recommended Layout

```
source-root/
├── .chezmoi.toml.tmpl
├── .chezmoiignore
├── .chezmoidata/defaults.yaml
├── .chezmoitemplates/*.tmpl
├── .chezmoiscripts/run_once_before_*.sh.tmpl
├── dot_gitconfig.tmpl              # dot_ → . in target
├── dot_editorconfig
├── modify_dot_config/app/settings.json
└── private_dot_ssh/config          # private_ → 0600 permissions
```

If using `.chezmoiroot`, the source state lives under that subdirectory.

## Reference Files

Load these on demand for detailed examples and edge cases:

- `references/data-and-profiles.md` — Profile-based config, data hierarchy examples, boolean flags
- `references/modify-scripts.md` — All modify patterns with full examples (managed blocks, jq, modify-template, Python/TS)
- `references/windows-pitfalls.md` — Comprehensive Windows failure modes with solutions
