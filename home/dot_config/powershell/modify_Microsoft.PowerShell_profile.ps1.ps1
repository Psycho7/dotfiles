#!/usr/bin/env pwsh
# Replaces the chezmoi-managed block in PowerShell profile, preserving everything else.

$BeginMarker = '# BEGIN chezmoi managed'
$EndMarker = '# END chezmoi managed'

$existing = @($input)

$managed = @(
  $BeginMarker
  '# Starship prompt'
  'Invoke-Expression (&starship init powershell)'
  ''
  '# Zoxide'
  'Invoke-Expression (& { (zoxide init powershell | Out-String) })'
  ''
  '# Add to PATH'
  '$env:PATH += ";$env:USERPROFILE\.local\bin"'
  $EndMarker
)

# Strip existing managed block if present
$output = @()
$inBlock = $false
foreach ($line in $existing) {
  if ($line -eq $BeginMarker) {
    $inBlock = $true
  } elseif ($line -eq $EndMarker) {
    $inBlock = $false
  } elseif (-not $inBlock) {
    $output += $line
  }
}

# Append managed block
$output += ''
$output += $managed

$output | ForEach-Object { $_ }
