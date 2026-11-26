"""Gera um pacote de release do LubriBot para deploy (Windows).

Uso::

    powershell -NoProfile -File scripts/build_release.ps1

Saída: ``dist/lubribot-release-AAAAmmdd-HHMM.tar.gz`` sem segredos, sem `.git`,
sem venv e sem dumps. O pacote inclui `deploy/` e `docs/`.
"""

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$dist = Join-Path $raiz 'dist'
$nome = "lubribot-release-{0:yyyyMMdd-HHmm}" -f (Get-Date)

if (-not (Test-Path $dist)) { New-Item -ItemType Directory -Path $dist | Out-Null }
$staging = Join-Path $dist "staging-$nome"
if (Test-Path $staging) { Remove-Item -Recurse -Force $staging }

Write-Host "[i] preparando staging"
New-Item -ItemType Directory -Path $staging | Out-Null

$excluir = @(
    '.git', '.venv', 'venv', '__pycache__', '.pytest_cache', '.ruff_cache',
    '.mypy_cache', 'Backups', 'dist', '.agent-panel', 'agent-panel.html',
    '.opencode', 'downloads', '.env'
)

Get-ChildItem -Path $raiz -Force | Where-Object { $excluir -notcontains $_.Name } | ForEach-Object {
    Copy-Item -Path $_.FullName -Destination $staging -Recurse -Force
}

# Remove bytecode que tenha vazado dentro das pastas copiadas.
Get-ChildItem -Path $staging -Recurse -Directory -Filter '__pycache__' -ErrorAction SilentlyContinue |
    Remove-Item -Recurse -Force

$saida = Join-Path $dist "$nome.tar.gz"
if (Test-Path $saida) { Remove-Item $saida -Force }
Write-Host "[i] compactando"
tar -czf $saida -C $staging .
Remove-Item -Recurse -Force $staging

$sha = (Get-FileHash -Path $saida -Algorithm SHA256).Hash.ToLower()
$shaFile = "$saida.sha256"
"$sha  $nome.tar.gz" | Set-Content -Path $shaFile -Encoding ASCII

$tamanhoMb = [Math]::Round((Get-Item $saida).Length / 1MB, 2)
Write-Host "[OK] $saida ($tamanhoMb MB)"
Write-Host "[OK] SHA256: $sha"
Write-Host "[i] envie com: scp `"$saida`" usuario@servidor:/tmp/"
