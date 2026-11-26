# Deploy/operacao do LubriBot no J4 Core (Android + Termux) via adb.
#
# Uso:
#   powershell -NoProfile -ExecutionPolicy Bypass -File scripts/deploy_device.ps1 -Install
#   ... -Start | -Stop | -Status | -Logs | -UpdateEnv
param(
    [switch]$Install,
    [switch]$Start,
    [switch]$Stop,
    [switch]$Status,
    [switch]$Logs,
    [switch]$UpdateEnv
)

$ErrorActionPreference = 'Stop'
$raiz = Split-Path -Parent $PSScriptRoot
$prefixo = '/data/data/com.termux/files/usr'
$homeApp = '/data/data/com.termux/files/home'
$destino = "$homeApp/lubribot"

function Get-Adb {
    $cmd = Get-Command adb -ErrorAction SilentlyContinue
    if ($cmd) { return $cmd.Source }
    foreach ($c in @(
        'D:\Arquivos de Programas\Android\Sdk\platform-tools\adb.exe',
        "$env:LOCALAPPDATA\Android\Sdk\platform-tools\adb.exe",
        'C:\platform-tools\adb.exe'
    )) { if (Test-Path $c) { return $c } }
    throw 'adb nao encontrado'
}

$adb = Get-Adb

function Invoke-OnDevice([string]$codigo) {
    $codigo | & $adb shell "run-as com.termux $prefixo/bin/python3 -"
}

function Install-App {
    Write-Host '[i] gerando release'
    powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $raiz 'scripts/build_release.ps1') | Out-Null
    $pkg = Get-ChildItem (Join-Path $raiz 'dist/*.tar.gz') | Sort-Object LastWriteTime | Select-Object -Last 1
    Write-Host "[i] enviando $($pkg.Name)"
    & $adb push $pkg.FullName /sdcard/lubribot-release.tar.gz | Out-Null

    if ($UpdateEnv -or $Install) {
        if (Test-Path (Join-Path $raiz '.env')) {
            & $adb push (Join-Path $raiz '.env') /sdcard/lubribot.env | Out-Null
        }
    }

    Invoke-OnDevice @'
import glob, os, tarfile
dest = "/data/data/com.termux/files/home/lubribot"
os.makedirs(dest, exist_ok=True)
pkg = sorted(glob.glob("/sdcard/lubribot-release*.tar.gz"))[-1]
with tarfile.open(pkg) as t:
    t.extractall(dest)
print("extraido:", len(os.listdir(dest)), "itens")
env_src = "/sdcard/lubribot.env"
if os.path.exists(env_src):
    texto = open(env_src, encoding="utf-8").read()
    if "NOTIFICACOES_HABILITADAS" not in texto:
        texto = texto.rstrip() + "\nNOTIFICACOES_HABILITADAS=false\n"
    env_dst = dest + "/.env"
    open(env_dst, "w", encoding="utf-8").write(texto)
    os.chmod(env_dst, 0o600)
    os.remove(env_src)
    print("env atualizado (600)")
else:
    print("env mantido" if os.path.exists(dest + "/.env") else "AVISO: .env ausente")
'@
    Write-Host '[OK] instalado em ~/lubribot'
}

function Start-Bot {
    Invoke-OnDevice @'
import os, subprocess, time
home = "/data/data/com.termux/files/home"
prefix = "/data/data/com.termux/files/usr"
dest = home + "/lubribot"
if not os.path.exists(dest + "/.env"):
    print("ERRO: .env ausente")
    raise SystemExit(3)
env = os.environ.copy()
env.update(HOME=home, PREFIX=prefix, PATH=prefix + "/bin:/system/bin",
           LD_LIBRARY_PATH=prefix + "/lib", TMPDIR=prefix + "/tmp")
log = open(dest + "/bot.log", "ab", buffering=0)
null = open(os.devnull, "rb")
proc = subprocess.Popen([prefix + "/bin/python", "main.py"], cwd=dest, env=env,
                        stdin=null, stdout=log, stderr=log,
                        start_new_session=True, close_fds=True)
time.sleep(8)
print("pid:", proc.pid, "| vivo:", os.path.exists("/proc/%d" % proc.pid))
'@
}

function Stop-Bot {
    # Mata somente processos cujo cmdline contem main.py (o ps do Android nao
    # mostra argumentos, entao lemos /proc/<pid>/cmdline dentro do app).
    Invoke-OnDevice @'
import os, signal
mortos = 0
for pid in os.listdir("/proc"):
    if not pid.isdigit():
        continue
    try:
        cmd = open("/proc/%s/cmdline" % pid, "rb").read().replace(b"\x00", b" ").decode(errors="replace")
    except Exception:
        continue
    if "main.py" in cmd:
        try:
            os.kill(int(pid), signal.SIGKILL)
            mortos += 1
        except Exception:
            pass
print("processos encerrados:", mortos)
'@
}

function Show-Status {
    Write-Host '=== processos python ==='
    & $adb shell "ps -A | grep -i python | head -5"
    Write-Host '=== log (ultimas 12) ==='
    & $adb shell "run-as com.termux tail -12 $destino/bot.log"
    Write-Host '=== health check ==='
    & $adb forward tcp:10000 tcp:10000 | Out-Null
    try {
        $r = Invoke-WebRequest -Uri 'http://127.0.0.1:10000/ping' -TimeoutSec 8 -UseBasicParsing
        Write-Host "PING OK: $($r.StatusCode) $($r.Content)"
    } catch {
        Write-Host "PING FALHOU: $($_.Exception.Message)"
    }
}

function Show-Logs {
    & $adb shell "run-as com.termux tail -40 $destino/bot.log"
}

if ($Install -or $UpdateEnv) { Install-App }
if ($Stop) { Stop-Bot }
if ($Start) { Start-Bot }
if ($Status) { Show-Status }
if ($Logs) { Show-Logs }
if (-not ($Install -or $Start -or $Stop -or $Status -or $Logs -or $UpdateEnv)) {
    Write-Host 'uso: -Install | -UpdateEnv | -Start | -Stop | -Status | -Logs'
}
