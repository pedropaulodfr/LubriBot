# Roadmap de modernização

Legenda: ✅ concluído · 🚧 em andamento · ⬜ pendente · 🧱 bloqueado por decisão

| Fase | Entrega | Estado | Complexidade |
|---|---|---|---|
| F0 | Congelamento, branch e higiene do repositório | ✅ | P |
| F1 | Testes de caracterização e regras de domínio | ✅ | M |
| F2 | Fundação: config validada, logging, unidade de trabalho | ✅ | M |
| F3 | Persistência: modelos únicos, Alembic, índices, unicidade | ✅ | G |
| F4 | Notificações confiáveis em Python (outbox, retry, lock) | ✅ | G |
| F5 | Migração dos fluxos do Telegram e UX | 🚧 | M |
| F6 | Performance: medições, pool, I/O fora do polling | 🚧 | M |
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

## F5 — Telegram e UX (em andamento)

Concluído neste incremento:

1. ✅ Menu principal reorganizado; "Ver Manutenções" no primeiro nível; `"..."` →
   "🗂️ Mais opções" (com retrocompatibilidade).
2. ✅ `/menu`, `/cancelar` e `/ajuda`; cancelamento limpa rascunhos por chat.
3. ✅ Sanitização de HTML da IA (allowlist) em dicas e diagnósticos.
4. ✅ Paginação do histórico (5 por página).
5. ✅ `/teste` restrito a `DEBUG_COMMANDS=true`.
6. ✅ Migração física: `handlers/` e `keyboards/` movidos para `lubribot/bot/`.
7. ✅ Confirmação antes de remover veículo.

Pendente (próximo incremento):

1. ✅ Máquina de estados persistida por chat (tabela `conversas`, migração
   `0003`, retomada automática após restart).
2. ⬜ Feedback de progresso mais claro em I/O longo (foto, IA).
3. ⬜ Revisão de textos (acentuação/emoji) nos fluxos ainda não tocados.

## F6 — Performance

1. ⬜ Medir p50/p95 de cada comando com os logs de `duracao_ms` já emitidos
   (Gemini e S3 instrumentados; falta coletar amostras em produção).
2. ⬜ Mover Gemini/S3/VPIC para executor com limite (não bloquear o polling).
3. ⬜ Revisar `selectin` onde houver carga desnecessária; medir N+1 com `EXPLAIN`.
4. ✅ Pool do Supabase (pooler 6543) e parâmetros por ambiente configuráveis.
5. ✅ Paginação da listagem de manutenções (5 por página).

## F7 — Segurança

1. ✅ Autorização por dono em veículo/produto/serviço/diagnóstico.
2. ✅ Validação de entrada centralizada (placa, ano, km, custo, RENAVAM).
3. ✅ Rate limiting por usuário para IA (limites diários configuráveis para
   diagnósticos e dicas).
4. ✅ Sanitização de HTML da IA (allowlist de tags).
5. ⬜ Revisar permissões do role do banco (mínimo necessário) e SSL obrigatório.
6. ✅ Limpeza do histórico Git (executada em 25/11/2026; backup em `Backups/`).

## F8 — Documentação

- Manter README/docs a cada entrega; runbook de operação no servidor do J4 Core.
- Registrar decisões novas como ADR em `docs/DECISIONS.md`.

## Ideias para depois (não autorizadas)

- Notificação baseada em quilometragem (o `km` já é coletado, mas não usado para
  agendamento) — **mudança de regra de negócio**, exige aprovação.
- Lembretes de documentos (IPVA, licenciamento) — funcionalidade nova.
- Painel web administrativo — fora do escopo do bot.
- Migração gradual para banco com pooler/Réplica de leitura se o volume crescer.
