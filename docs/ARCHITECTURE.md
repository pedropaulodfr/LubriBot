# Arquitetura do LubriBot

## Visão de camadas

```
┌────────────────────────────────────────────────────────────┐
│ Telegram (pyTelegramBotAPI, long polling)                  │
│ lubribot/bot/registry.py  → handlers/ (legado)             │
└───────────────────────────┬────────────────────────────────┘
                            │ (dados já validados pela conversa)
┌───────────────────────────▼────────────────────────────────┐
│ Aplicação          lubribot/app.py                          │
│  - configuração validada    - logging estruturado           │
│  - health check /ping       - shutdown gracioso             │
└───────────────┬─────────────────────────────┬──────────────┘
                │                             │
┌───────────────▼────────────┐   ┌────────────▼───────────────┐
│ Job periódico              │   │ Handlers (F5 migra p/      │
│ lubribot/jobs/             │   │ lubribot/bot/handlers)     │
│  scheduler + advisory lock │   │  - conversa e teclados     │
└───────────────┬────────────┘   └────────────┬───────────────┘
                │                             │
┌───────────────▼─────────────────────────────▼───────────────┐
│ Notificações                     Serviços/repositórios       │
│ planner → outbox(notificacoes)   repositories/ + services/  │
│ dispatcher → TelegramSender      (SQLAlchemy)               │
└───────────────────────────────┬─────────────────────────────┘
                                │
                     ┌──────────▼──────────┐
                     │ PostgreSQL (Supabase)│
                     └─────────────────────┘
```

## Princípios

1. **Regra de negócio fora do banco.** O cálculo da próxima manutenção é Python
   puro (`lubribot/domain/maintenance.py`), testável sem infraestrutura. A
   procedure antiga não está versionada e foi substituída.
2. **Domínio não conhece infraestrutura.** `domain/` não importa SQLAlchemy,
   Telegram nem rede.
3. **Notificações como outbox.** A tabela `notificacoes` é a fila persistida:
   cada linha tem chave de idempotência, tentativas e agendamento de retry. Um
   restart não perde nem duplica aviso.
4. **Uma unidade de trabalho por operação.** `Database.unit_of_work()` faz
   commit, rollback e `close` — acabou a sessão global de módulo.
5. **Falha explícita.** Configuração inválida derruba o boot; erro de envio é
   logado com a chave da notificação; nada de `except:` silencioso.

## Fluxo de notificações

```
scheduler (a cada INTERVALO_NOTIFICACAO)
  └─ advisory lock (pg_try_advisory_lock)
       ├─ FASE 1: planejar
       │    SELECT veículos ativos + última manutenção finalizada
       │    SELECT intervalos de serviço (em lote, 2 queries no total)
       │    proxima_data = ultima_data + max(intervaloDias | padrão)
       │    está na janela [hoje, hoje + diasNotificacao]?
       │    INSERT notificacoes (chave única → idempotente)
       └─ FASE 2: despachar
            SELECT pendentes prontas (proximaTentativaEm IS NULL OR <= agora)
            valida opt-out do usuário → Cancela
            TelegramSender.enviar
              sucesso   → status=Enviada, enviadaEm
              temporário→ tentativas+1, backoff, proximaTentativaEm
              permanente→ status=Falha (sem retry)
```

Estados: `Pendente`, `Enviada`, `Cancelada`, `Falha`.
`notificacoes.status` foi alargada para `varchar(20)` porque `Cancelada` (9
caracteres) não cabia em `varchar(8)`.

## Persistência

- Engine única com `pool_pre_ping`, pool dimensionado e reciclagem.
- Sessões `expire_on_commit=False` para compatibilidade com handlers que
  devolvem objetos.
- `lazy="selectin"` nos relacionamentos: carrega em lote e evita N+1.
- Schema é responsabilidade do Alembic (`migrations/`). Nenhum `create_all`.
- `repository/models.py` virou shim que reexporta `lubribot.models` — os
  handlers legados continuam funcionando durante a migração incremental.

## Compatibilidade e migração incremental

| Camada | Estado |
|---|---|
| Config, logging, banco, modelos, domínio | Nova (`lubribot/`) |
| Notificações | Nova (`lubribot/notifications` + job) |
| Handlers, keyboards | Legados, com correções pontuais de integridade |
| `services/` | Parcialmente legado; serviços quebrados foram corrigidos |

A fase F5 move handlers para `lubribot/bot/handlers` e remove a pasta
`services/` duplicada.

## Testes

| Tipo | Onde | Precisa de banco? |
|---|---|---|
| Domínio (regra de manutenção, retry) | `tests/test_domain_*` | não |
| Planejador/despachante (dublês) | `tests/test_notification_*` | não |
| Configuração | `tests/test_settings.py` | não |
| Mapeamento/metadata | `tests/test_models.py` | não |
| Integração Postgres | `tests/integration/` (fase futura) | sim, banco dedicado |
