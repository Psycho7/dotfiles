#!/usr/bin/env pwsh
# Replaces the chezmoi-managed block in PowerShell profile, preserving everything else.

$BeginMarker = '# BEGIN chezmoi managed'
$EndMarker = '# END chezmoi managed'

$existing = @($input)

$managed = @(
  $BeginMarker
  ''
  '# Starship prompt'
  'if (Get-Command starship -ErrorAction SilentlyContinue) { Invoke-Expression (&starship init powershell) }'
  ''
  '# Zoxide'
  'if (Get-Command zoxide -ErrorAction SilentlyContinue) { Invoke-Expression (& { (zoxide init powershell | Out-String) }) }'
  ''
  '# Add to PATH'
  '$env:PATH += ";$env:USERPROFILE\.local\bin"'
  ''
  '# PowerShell config'
  'Set-PSReadlineKeyHandler -Key Tab -Function MenuComplete'
  ''
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

# Trim trailing blank lines to avoid accumulation on repeated applies
while ($output.Count -gt 0 -and $output[-1] -eq '') {
  $output = @($output | Select-Object -SkipLast 1)
}

# Add blank separator only if there is user content above the managed block
if ($output.Count -gt 0) {
  $output += ''
}
$output += $managed

$output | ForEach-Object { $_ }
