# Roadmap de modernização

Legenda: ✅ concluído · 🚧 em andamento · ⬜ pendente · 🧱 bloqueado por decisão

| Fase | Entrega | Estado | Complexidade |
|---|---|---|---|
| F0 | Congelamento, branch e higiene do repositório | ✅ | P |
| F1 | Testes de caracterização e regras de domínio | ✅ | M |
| F2 | Fundação: config validada, logging, unidade de trabalho | ✅ | M |
| F3 | Persistência: modelos únicos, Alembic, índices, unicidade | ✅ | G |
| F4 | Notificações confiáveis em Python (outbox, retry, lock) | ✅ | G |
| F5 | Migração dos fluxos do Telegram e UX | ⬜ | M |
| F6 | Performance: medições, pool, I/O fora do polling | ⬜ | M |
| F7 | Segurança: autorização por dono em todo callback, validação, sanitização | 🚧 | M |
| F8 | Documentação contínua e runbook | 🚧 | P |

## F0 — Higiene (concluída)

- Working tree não commitado descartado; branch `modernizacao/fase-2`.
- Token removido do plano de deploy (rotação pendente com o dono).
- `migration_data.sql` (PII) e 22 `.pyc` fora do índice do Git.
- `.gitignore` ampliado; `.env.example` criado.

## F1 — Rede de segurança (concluída)

- 94 testes: domínio, planejador, despachante, sender, settings, mapeamento.
- Regra de próxima manutenção documentada e coberta em casos de borda.

## F2 — Fundação (concluída)

- `Settings` validado no boot, com normalização de `AMBIENTE`.
- Logging estruturado (texto ou JSON) e eventos nomeados.
- `Database.unit_of_work()` com commit/rollback/close garantidos.

## F3 — Persistência (concluída)

- Modelos unificados em `lubribot/models/entities.py` (sem `create_all`).
- Migrações `0001` (baseline) e `0002` (índices, outbox, `intervaloDias`,
  alargamento de `status`).
- Correção do dump/SQL de migração para não expor project ref real.

## F4 — Notificações (concluída)

- Regra em Python, idempotente, com retry e trava de instância única.
- Job com etapas em transações separadas e observabilidade por log.

## F5 — Telegram e UX (próxima)

1. Mover handlers para `lubribot/bot/handlers`, com máquina de estados explícita
   (substituir `register_next_step_handler` por estado persistido por chat).
2. Menu principal: substituir o botão `"..."` por "Mais opções"; subir
   "Ver Manutenções" para o primeiro nível.
3. Padronizar cancelar/voltar em todos os fluxos; mensagens de erro orientativas.
4. Confirmação antes de remover veículo; feedback de progresso em I/O longo.
5. Sanitizar HTML retornado pela IA (allowlist de tags).
6. Unificar textos (acentuação, emoji) e remover o comando de debug `/teste`.

## F6 — Performance

1. Medir p50/p95 de cada comando (instrumentação simples por handler).
2. Mover Gemini/S3/VPIC para executor com limite (não bloquear o polling).
3. Revisar `selectin` onde houver carga desnecessária; medir N+1 com `EXPLAIN`.
4. Pool do Supabase (pooler 6543) e parâmetros por ambiente.
5. Paginar listagem de manutenções (hoje envia uma mensagem por item).

## F7 — Segurança

1. Auditoria final de autorização em todos os `callback_data` (imagem, exclusão).
2. Validação de entrada com Pydantic em todos os pontos de escrita.
3. Rate limiting por usuário para IA (hoje só o diagnóstico tem limite).
4. Sanitização de HTML da IA.
5. Revisar permissões do role do banco (mínimo necessário) e SSL obrigatório.
6. Limpeza do histórico Git (decisão do dono — operação destrutiva).

## F8 — Documentação

- Manter README/docs a cada entrega; runbook de operação no servidor do J4 Core.
- Registrar decisões novas como ADR em `docs/DECISIONS.md`.

## Ideias para depois (não autorizadas)

- Notificação baseada em quilometragem (o `km` já é coletado, mas não usado para
  agendamento) — **mudança de regra de negócio**, exige aprovação.
- Lembretes de documentos (IPVA, licenciamento) — funcionalidade nova.
- Painel web administrativo — fora do escopo do bot.
- Migração gradual para banco com pooler/Réplica de leitura se o volume crescer.
