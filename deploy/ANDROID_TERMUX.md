# LubriBot no Android (J4 Core) via Termux + ADB

Este é o caminho usado para rodar o bot no **Samsung Galaxy J4 Core (SM-J410G)**,
Android 8.1, ARM 32 bits, usando o Termux já instalado no aparelho.

## Por que um perfil "lite"

O aparelho não tem wheels compatíveis para parte da stack:

| Pacote | Problema | Solução no aparelho |
|---|---|---|
| `psycopg2-binary` | sem wheel armv7 | driver puro **pg8000** (`lubribot/database/engine.py` adapta a URL) |
| `grpcio` (`google-generativeai`) | sem wheel armv7 | **Gemini via REST** (`lubribot/integrations/gemini.py`) |
| `pydantic-core` | sem wheel armv7 | **config lite** sem Pydantic (`lubribot/config/settings_lite.py`) |

O código escolhe automaticamente o caminho disponível; servidor/desktop segue
usando Pydantic, SDK oficial e psycopg2.

## Pré-requisitos

- Termux instalado no aparelho (já está).
- Depuração USB ativada e `adb devices` mostrando o aparelho.
- `adb` no PATH ou em `D:\Arquivos de Programas\Android\Sdk\platform-tools\adb.exe`.
- Termux com as dependências:

```bash
# dentro do Termux (ou via adb, como fizemos)
python -m pip install -r requirements-device.txt
```

## Instalar/atualizar

Na máquina com o repositório:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File scripts/deploy_device.ps1 -Install
```

O script:
1. gera o pacote de release sem segredos;
2. envia para `/sdcard` e extrai em `~/lubribot` no Termux;
3. cria/atualiza o `.env` (600) a partir do `.env` local;
4. mantém notificações desativadas no primeiro boot.

## Operar

```powershell
... -Start     # inicia o bot em background
... -Stop      # encerra o processo python
... -Status    # processo + últimas linhas do log + /ping
... -Logs      # últimas 40 linhas de bot.log
... -UpdateEnv # reintala o .env a partir do local
```

Health check local: `adb forward tcp:10000 tcp:10000` e
`curl http://127.0.0.1:10000/ping`.

## TLS do banco

O pooler do Supabase usa CA própria. No aparelho o TLS roda **sem validação de
CA** (equivalente a `sslmode=require`): tráfego cifrado, sem pinning. Para
validação completa, baixe o `prod-ca-2021.crt` do Supabase, envie ao aparelho e
defina no `.env`:

```
DB_SSL_CA=/data/data/com.termux/files/home/lubribot/prod-ca-2021.crt
```

## Autostart e limitações

- **Termux:Boot não está instalado** — após reiniciar o aparelho o bot **não**
  sobe sozinho. Inicie com `... -Start` (adb) ou abrindo o Termux e rodando
  `~/lubribot/start.sh`.
- O aparelho tem ~858 MB de RAM; o sistema pode matar o processo sob pressão.
  Já foi adicionado à whitelist de bateria (`cmd deviceidle whitelist +com.termux`).
- Manter o aparelho carregando e com Wi-Fi estável.
- `run-as` funciona porque o Termux é debuggable; qualquer pessoa com ADB e o
  aparelho autorizado consegue acessar os dados do app. Não deixe a depuração USB
  ligada em ambiente não confiável.
