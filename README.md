# LubriBot

Bot de Telegram para gestão de manutenção de veículos: cadastro de veículos,
histórico de manutenções com fotos e recibo, catálogo de serviços/produtos,
dicas e diagnósticos gerados por IA e notificações de próxima manutenção.

> **Estado:** fase 2 da modernização concluída (fundação, notificações,
> migrações e testes). A migração da experiência do Telegram é a próxima fase —
> ver [docs/ROADMAP.md](docs/ROADMAP.md).

## Stack

| Componente | Tecnologia |
|---|---|
| Linguagem | Python 3.12+ |
| Bot | pyTelegramBotAPI (long polling) |
| Persistência | PostgreSQL (Supabase) + SQLAlchemy 2.0 + Alembic |
| Configuração | Pydantic Settings (validada no boot) |
| IA | Google Gemini (`gemini-2.5-flash`) |
| Imagens | AWS S3 |
| Consulta veicular | NHTSA VPIC |

## Estrutura

```
lubribot/            # aplicação modernizada (camadas)
├── config/          # settings validados (env)
├── database/        # engine, unidade de trabalho, advisory lock
├── models/          # mapeamento SQLAlchemy (fonte única)
├── domain/          # regras puras: manutenção, retry, validação
├── repositories/    # consultas e persistência
├── notifications/   # planejador + despachante (outbox)
├── integrations/    # Telegram (envio classificado)
├── jobs/            # job + agendador periódico
├── bot/             # registry, handlers, teclados, navegação
│   ├── handlers/    # um arquivo por fluxo
│   └── keyboards/   # teclados Reply/Inline
└── app.py           # bootstrap

services/ prompts/   # lógica legada mantida durante a migração incremental
migrations/          # Alembic (0001 baseline, 0002 hardening)
tests/               # pytest: unidade + integração com Postgres
scripts/             # operação: status do banco, aplicar migrações, validação
docs/                # arquitetura, decisões, roadmap, runbook
migration/           # ETL legado (Postgres -> Supabase), mantido como ferramenta
```

## Instalação

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# Linux/macOS
source .venv/bin/activate

pip install -r requirements-dev.txt   # inclui runtime + testes/lint
cp .env.example .env                  # preencha as credenciais
```

## Configuração

Todas as variáveis estão documentadas em [.env.example](.env.example).
Credenciais **nunca** ficam no código: são lidas do ambiente (ou de `.env` local,
que está no `.gitignore`).

O boot falha de forma explícita se faltar token, string de conexão ou se a
configuração estiver inválida — não existe mais "subir com o padrão errado".

## Banco de dados

O schema é versionado com Alembic. **Banco já existente** (produção/QA):

```bash
alembic stamp 0001      # marca o schema legado como baseline
alembic upgrade head    # aplica índices, colunas do outbox e ajustes
```

Banco novo:

```bash
alembic upgrade head
```

Detalhes em [docs/RUNBOOK.md](docs/RUNBOOK.md).

## Execução

```bash
python main.py
```

O processo sobe:
- long polling do Telegram;
- job de notificações em thread própria (a cada `INTERVALO_NOTIFICACAO` minutos);
- health check `GET /ping` na porta `PORT`.

Comandos no chat: `/menu` (restaura o teclado), `/cancelar` (interrompe o fluxo),
`/ajuda`. `/teste` só existe com `DEBUG_COMMANDS=true`.

## Testes

```bash
pytest                                        # unidade, sem banco/rede
python scripts/validate_with_embedded_pg.py   # Postgres embarcado: migrações + notificações
ruff check .
mypy lubribot
```

## Migrações

```bash
python scripts/db_status.py STRING_CONNECTION       # diagnóstico read-only
python scripts/apply_migrations.py STRING_CONNECTION  # baseline/hardening + verificação
```

## Notificações

A regra saiu do banco (procedure não versionada) para Python testável:

```
proxima_data = ultima_manutencao.data + max(intervaloDias dos serviços)
```

- `intervaloDias` é opcional por serviço; sem ele, vale `INTERVALO_MANUTENCAO_DIAS` (180).
- Aviso entra na janela `[hoje, hoje + diasNotificacao]`.
- Idempotência por chave `ProximaManutencao:<manutencao_id>` (índice único).
- Falha de envio → retry com backoff; depois de N tentativas vira `Falha` (auditável).
- Duas instâncias não duplicam envio (advisory lock + chave única).

## Segurança

- Rotacione o token do bot: ele esteve exposto em um arquivo local de plano de
  deploy (removido nesta fase). Ver [docs/DECISIONS.md](docs/DECISIONS.md).
- O dump `migration_data.sql` saiu do versionamento (continha dados pessoais).
- Bytecode `.pyc` saiu do versionamento.
- Pendente: limpeza do histórico Git (exige reescrita — decisão sua).

## Documentação

- [Arquitetura](docs/ARCHITECTURE.md)
- [Decisões técnicas](docs/DECISIONS.md)
- [Roadmap](docs/ROADMAP.md)
- [Changelog](docs/CHANGELOG.md)
- [Runbook (instalação, migração, operação)](docs/RUNBOOK.md)
- [Deploy no servidor (systemd ou Docker)](deploy/README.md)
- [Deploy no Android/J4 Core via Termux (em uso)](deploy/ANDROID_TERMUX.md)
- [Equipe de agentes](docs/AGENT_TEAM.md) · [Quadro de tarefas](docs/AGENT_TASKS.md)
- `DOCUMENTACAO.md` é o documento histórico da versão anterior (parcialmente desatualizado).
