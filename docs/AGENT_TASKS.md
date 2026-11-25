# Quadro de tarefas

Status: ✅ concluído · 🚧 em andamento · ⬜ pendente · 🧱 bloqueado

## Fase 2 (concluída)

| ID | Tarefa | Dono | Escopo | Status |
|---|---|---|---|---|
| T-001 | Descartar working tree e criar branch | Tech Lead | git | ✅ |
| T-002 | Remover token exposto do plano de deploy | Segurança | `Implementations/` | ✅ |
| T-003 | Retirar PII e `.pyc` do índice; ampliar `.gitignore` | Segurança | `.gitignore`, git index | ✅ |
| T-004 | Configuração validada (Pydantic Settings) | Python | `lubribot/config/` | ✅ |
| T-005 | Logging estruturado | Python | `lubribot/utils/logging.py` | ✅ |
| T-006 | Engine, pool e unidade de trabalho | Banco | `lubribot/database/` | ✅ |
| T-007 | Modelos unificados (fonte única) | Banco | `lubribot/models/` | ✅ |
| T-008 | Regra de próxima manutenção em Python | Python | `lubribot/domain/` | ✅ |
| T-009 | Repositório de notificações em lote | Banco | `lubribot/repositories/` | ✅ |
| T-010 | Planejador idempotente | Python | `lubribot/notifications/planner.py` | ✅ |
| T-011 | Despachante com retry/backoff | Python | `lubribot/notifications/dispatcher.py` | ✅ |
| T-012 | Sender com classificação de erro | Python | `lubribot/integrations/` | ✅ |
| T-013 | Job + agendador com advisory lock | Banco/Perf | `lubribot/jobs/` | ✅ |
| T-014 | Bootstrap e health check | Python | `lubribot/app.py`, `main.py` | ✅ |
| T-015 | Alembic baseline e hardening | Banco | `migrations/` | ✅ |
| T-016 | Suíte de testes (94) | QA | `tests/` | ✅ |
| T-017 | Corrigir estado global em veículo/serviço/manutenção | Python | `handlers/` | ✅ |
| T-018 | Corrigir diagnóstico (tupla, dono, sessão) | Python | `handlers/ver_diagnostico_handle.py` | ✅ |
| T-019 | Corrigir cache de dicas | Python | `handlers/ver_dicas_handle.py` | ✅ |
| T-020 | Corrigir histórico de manutenções (join/nulos/botões) | Python | `handlers/ver_manutencoes_handle.py` | ✅ |
| T-021 | Corrigir confirmação e autorização em produtos/serviços | Segurança | `handlers/ver_produtos_handle.py`, `ver_servicos_handle.py` | ✅ |
| T-022 | Corrigir serviços quebrados (username/marca/ano) | Python | `services/` | ✅ |
| T-023 | README, arquitetura, decisões, roadmap, changelog, runbook | Docs | `README.md`, `docs/` | ✅ |

## Fase 3 (próxima)

| ID | Tarefa | Dono | Depende de | Complexidade |
|---|---|---|---|---|
| T-101 | Revisão independente dos handlers reescritos | QA | T-017..T-021 | M |
| T-102 | Máquina de estados explícita por chat | UX/Python | T-101 | G |
| T-103 | Novo menu e submenu "Mais opções" | UX | T-102 | M |
| T-104 | Sanitização de HTML da IA | Segurança | — | P |
| T-105 | Validação de entrada com Pydantic | Segurança | — | M |
| T-106 | Medição de p50/p95 por comando | Performance | ambiente com banco | M |
| T-107 | I/O externo em executor (Gemini/S3/VPIC) | Performance | T-106 | G |
| T-108 | Paginação da listagem de manutenções | Performance/UX | T-102 | M |
| T-109 | Testes de integração com Postgres dedicado | QA | infra de teste | M |
| T-110 | Limpeza do histórico Git (decisão do dono) | Segurança | autorização | G |
| T-111 | Rotação do token no BotFather | Dono | — | P |

## Bloqueios

| Bloqueio | Efeito | Dono | Ação |
|---|---|---|---|
| Corpo da procedure `sp_CriarNotificacaoProximaManutencao` desconhecido | impossível comparar regra original com a reconstruída | dono do produto | validar cálculo com casos reais |
| Rotação do token | token antigo potencialmente válido | dono | BotFather → Revoke |
| Reescrita do histórico Git | PII/segredo antigos no histórico | dono | autorizar operação destrutiva |
