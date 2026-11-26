# Deploy do LubriBot no servidor (J4 Core)

O bot é um processo único (long polling + job de notificações + health check em
`GET /ping`). Há dois caminhos; escolha conforme o servidor.

## Opção A — Linux com systemd (recomendado para VPS)

Pré-requisitos: Python 3.11+, `python3-venv`, `rsync`, systemd, acesso root.

```bash
# na sua máquina: gere o pacote
powershell -NoProfile -File scripts/build_release.ps1

# envie para o servidor
scp dist/lubribot-release-*.tar.gz usuario@servidor:/tmp/

# no servidor
sudo mkdir -p /opt/lubribot-src && sudo tar -xzf /tmp/lubribot-release-*.tar.gz -C /opt/lubribot-src
cd /opt/lubribot-src
sudo ./deploy/install.sh --migrate          # instala sem iniciar
sudo nano /etc/lubribot/lubribot.env        # preencha as credenciais
sudo systemctl start lubribot
sudo systemctl status lubribot
curl -s http://127.0.0.1:10000/ping
```

O instalador:
- cria usuário de serviço `lubribot`;
- instala em `/opt/lubribot` com venv próprio;
- cria `/etc/lubribot/lubribot.env` (permissão 600) a partir do `.env.example`;
- opcionalmente aplica `alembic upgrade head` (`--migrate`);
- instala e habilita o systemd, com `Restart=on-failure` e `SIGTERM` gracioso.

Flags: `--start` (instala e inicia), `--migrate` (migra o banco).

## Opção B — Container (Docker/Podman)

```bash
cp .env.example .env   # preencha
docker compose -f deploy/docker-compose.yml up -d --build
docker compose -f deploy/docker-compose.yml logs -f
```

A imagem roda como usuário não-root, expõe `/ping` só em `127.0.0.1` e tem
healthcheck. Migrações: rode uma vez antes de subir:

```bash
docker compose -f deploy/docker-compose.yml run --rm lubribot \
  .venv/bin/alembic upgrade head   # ou use a imagem com alembic no PATH
```

## Primeiro boot seguro

O job de notificações roda imediatamente ao iniciar. Para subir sem enviar nada:

```bash
# no /etc/lubribot/lubribot.env ou no .env
NOTIFICACOES_HABILITADAS=false
```

Depois de conferir os logs, troque para `true` e reinicie.

## Verificação

```bash
systemctl status lubribot                  # ou docker compose ps
journalctl -u lubribot -f                  # logs em tempo real
curl -s http://127.0.0.1:10000/ping        # {"status": "ok", ...}
```

Logs úteis: `bot_iniciado`, `scheduler_iniciado`, `scheduler_ciclo_concluido`,
`notificacao_criada`, `notificacao_enviada`.

## Atualização

```bash
# Opção A: novo release
sudo ./deploy/install.sh --migrate && sudo systemctl restart lubribot
# Opção B
git pull && docker compose -f deploy/docker-compose.yml up -d --build
```

## Segurança

- `.env` **nunca** vai para o Git; no servidor fica em `/etc/lubribot/lubribot.env`
  com permissão 600 e dono `root:lubribot`.
- Exponha a porta do health check apenas em rede interna/reverse proxy.
- O bot usa role privilegiada no Postgres; não abra o banco para a internet além
  do necessário (Supabase já restringe por rede/SSL).
- Rotacione token do Telegram e senha do banco se houver suspeita de exposição.
