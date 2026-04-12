# Data Hierarchy and Profile-Based Configuration

## Profile system

Define profiles in `.chezmoidata/` with per-profile settings, then select in the config template:

```yaml
# .chezmoidata/defaults.yaml
profiles:
  personal:
    email: "me@home.com"
    install_gui: true
    install_docker: false
  work:
    email: "me@corp.com"
    install_gui: true
    install_docker: true
  server:
    email: "admin@srv.com"
    install_gui: false
    install_docker: true

packages:
  common:
    - git
    - neovim
    - ripgrep
```

## Boolean flags derived from OS and profile

Combine profile selection and derived flags into a single `[data]` block (TOML doesn't allow duplicate section headers):

```toml
# .chezmoi.toml.tmpl — complete example
{{- $profile := "personal" -}}
{{- if eq .chezmoi.hostname "work-laptop" "work-desktop" -}}
{{-   $profile = "work" -}}
{{- else if hasPrefix "srv-" .chezmoi.hostname -}}
{{-   $profile = "server" -}}
{{- else if stdinIsATTY -}}
{{-   $profile = promptChoiceOnce . "profile" "Machine profile"
        (list "personal" "work" "server") -}}
{{- end }}

{{- $p := index .profiles $profile -}}

[data]
    profile        = {{ $profile | quote }}
    is_windows     = {{ eq .chezmoi.os "windows" }}
    is_mac         = {{ eq .chezmoi.os "darwin" }}
    is_linux       = {{ eq .chezmoi.os "linux" }}
    email          = {{ $p.email | quote }}
    install_gui    = {{ $p.install_gui }}
    install_docker = {{ $p.install_docker }}
```

Templates then use these flags directly:

```
# dot_gitconfig.tmpl
[user]
    email = {{ .email }}
{{ if .install_gui -}}
[diff]
    tool = vscode
{{ end -}}
```

## Testing your data

```bash
chezmoi data | jq '.profile, .email, .is_windows'
chezmoi execute-template '{{ .profile }} on {{ .chezmoi.os }}'
```
