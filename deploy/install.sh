#!/usr/bin/env bash
# Instalador do LubriBot em servidor Linux (systemd).
#
# Uso (como root, a partir da pasta do release):
#   sudo ./deploy/install.sh                 # instala e NAO inicia
#   sudo ./deploy/install.sh --start         # instala e inicia o bot
#   sudo ./deploy/install.sh --migrate       # roda alembic upgrade head antes
#
# Requisitos: python3.12+ (ou python3.11+), git (opcional), systemd.
set -euo pipefail

APP_DIR="/opt/lubribot"
ENV_DIR="/etc/lubribot"
ENV_FILE="${ENV_DIR}/lubribot.env"
SERVICE="lubribot"
USUARIO="lubribot"
ORIGEM="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

INICIAR=0
MIGRAR=0
for arg in "$@"; do
  case "$arg" in
    --start) INICIAR=1 ;;
    --migrate) MIGRAR=1 ;;
    -h|--help) sed -n '2,10p' "$0"; exit 0 ;;
    *) echo "argumento desconhecido: $arg"; exit 2 ;;
  esac
done

if [[ $EUID -ne 0 ]]; then
  echo "[!] rode como root (sudo)"
  exit 1
fi

PYTHON="$(command -v python3.12 || command -v python3.11 || command -v python3 || true)"
if [[ -z "$PYTHON" ]]; then
  echo "[!] Python 3.11+ nao encontrado. Instale python3, python3-venv e python3-dev."
  exit 1
fi
echo "[i] Python: $("$PYTHON" --version)"

echo "[i] criando usuario de servico ($USUARIO)"
id -u "$USUARIO" >/dev/null 2>&1 || useradd --system --home "$APP_DIR" --shell /usr/sbin/nologin "$USUARIO"

echo "[i] sincronizando aplicacao para $APP_DIR"
mkdir -p "$APP_DIR"
if command -v rsync >/dev/null 2>&1; then
  rsync -a --delete \
    --exclude '.git' --exclude '.venv' --exclude '.env' --exclude 'Backups' \
    --exclude '__pycache__' --exclude '.pytest_cache' --exclude '.ruff_cache' \
    --exclude '.agent-panel' --exclude 'agent-panel.html' --exclude 'dist' \
    "$ORIGEM"/ "$APP_DIR"/
else
  cp -a "$ORIGEM"/. "$APP_DIR"/
  rm -rf "$APP_DIR/.git" "$APP_DIR/.venv" "$APP_DIR/Backups" "$APP_DIR/.agent-panel"
fi

echo "[i] criando ambiente virtual"
"$PYTHON" -m venv "$APP_DIR/.venv"
"$APP_DIR/.venv/bin/python" -m pip install --quiet --upgrade pip
"$APP_DIR/.venv/bin/python" -m pip install --quiet -r "$APP_DIR/requirements.txt"

echo "[i] preparando arquivo de ambiente"
mkdir -p "$ENV_DIR"
if [[ ! -f "$ENV_FILE" ]]; then
  install -m 600 "$APP_DIR/.env.example" "$ENV_FILE"
  echo "[!] EDITE $ENV_FILE com as credenciais reais antes de iniciar."
  PREENCHER=1
else
  chmod 600 "$ENV_FILE"
  PREENCHER=0
fi

if [[ $MIGRAR -eq 1 ]]; then
  echo "[i] aplicando migracoes"
  ( cd "$APP_DIR" && set -a && . "$ENV_FILE" && set +a && .venv/bin/alembic upgrade head )
fi

echo "[i] instalando servico systemd"
install -m 644 "$APP_DIR/deploy/lubribot.service" "/etc/systemd/system/${SERVICE}.service"
systemctl daemon-reload
systemctl enable "$SERVICE" >/dev/null

chown -R "$USUARIO":"$USUARIO" "$APP_DIR"
chown root:"$USUARIO" "$ENV_FILE"

if [[ $INICIAR -eq 1 ]]; then
  if [[ $PREENCHER -eq 1 ]]; then
    echo "[!] ambiente ainda e o exemplo; preencha $ENV_FILE antes de iniciar."
    exit 3
  fi
  echo "[i] iniciando servico"
  systemctl restart "$SERVICE"
  sleep 3
  systemctl --no-pager --lines=20 status "$SERVICE" || true
  echo "[i] health check: curl -s http://127.0.0.1:10000/ping"
else
  echo "[OK] instalado. Edite $ENV_FILE e rode: systemctl start $SERVICE"
fi
