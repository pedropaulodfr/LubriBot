# Changelog

## [2.3.0-dev] — 25/11/2026 — Fase 5: conversas persistidas e limites de IA

### Adicionado
- Tabela `conversas` (migração `0003`) e registro de rascunhos persistidos:
  cada chat tem no máximo uma conversa ativa com dados e etapa atual.
- **Retomada após restart**: a fachada do bot (`lubribot/bot/facade.py`) anota o
  próximo passo e um handler catch-all retoma o fluxo quando não há passo
  pendente — o usuário não perde o progresso se o processo reiniciar.
- Rascunhos de veículo, manutenção e diagnóstico agora se gravam sozinhos
  (`DraftMixin`), sem alterar a lógica de cada etapa.
- Limites diários de IA configuráveis: `IA_DIAGNOSTICOS_DIA` (3) e
  `IA_DICAS_DIA` (10), com mensagem orientativa ao atingir.

### Alterado
- `apply_migrations.py` verifica a revisão `0003`.
- Validação embarcada cobre a persistência (novo registry lê o mesmo estado).

## [2.2.0-dev] — 25/11/2026 — Fase 4: pacotes, segurança de entrada e higiene do histórico

### Adicionado
- Validação centralizada de entradas (`lubribot/domain/validation.py`): placa
  (antiga e Mercosul), ano, km, custo em formato brasileiro e RENAVAM.
- Medição de tempo de operações caras (`lubribot/utils/timing.py`): chamadas ao
  Gemini e upload no S3 registram `duracao_ms` em log estruturado.
- Confirmação (Sim/Não) antes de remover veículo.

### Alterado
- `handlers/`, `keyboards/` e utilitários migrados para
  `lubribot/bot/handlers/`, `lubribot/bot/keyboards/` e `lubribot/utils/`.
- Histórico Git reescrito: removidos `migration_data.sql` (PII),
  `migration.log` e todos os `.pyc` de **todos** os commits; branches remotas
  atualizadas com force-push. Backup em `Backups/history-backup-20261125.bundle`.

### Segurança
- Histórico sem PII/bytecode: 121 objetos sensíveis removidos; `.git` caiu de
  0,4 MB para 0,2 MB.
- 168 testes passando, Ruff limpo, import da aplicação validado.

## [2.1.0-dev] — 24/11/2026 — Fase 3: experiência do Telegram

### Adicionado
- Menu principal reorganizado: "🔎 Ver Manutenções" no primeiro nível e
  "🗂️ Mais opções" no lugar do botão `"..."` (teclados antigos continuam aceitos).
- Comandos `/menu` (restaura o teclado), `/cancelar` (interrompe o fluxo e limpa
  rascunhos) e `/ajuda`.
- Sanitização de HTML da IA antes do envio (`lubribot/utils/sanitize.py`):
  allowlist de tags, remoção de atributos e bloqueio de `javascript:`.
- Paginação do histórico de manutenções (5 por página, botões Anterior/Próxima).
- `DEBUG_COMMANDS` para habilitar `/teste` só em QA.
- Validação de migrações e notificações em PostgreSQL embarcado
  (`scripts/validate_with_embedded_pg.py`, `tests/integration/`).
- `scripts/apply_migrations.py`: aplica baseline/hardening com verificação de schema.
- `scripts/db_status.py`: diagnóstico somente leitura, sem expor credenciais.

### Corrigido
- Migração `0002` usava `tipoNotificacao` sem aspas; no PostgreSQL o identificador
  virava minúsculo e a migração falhava. Detectado pelo validador embarcado.
- `/start` agora cria usuário e envia boas-vindas numa única transação.
- Mensagens de erro dos fluxos indicam o próximo passo, em vez de erro genérico.

### Alterado
- `DOCUMENTACAO.md` marcado como histórico; README/docs são a fonte atual.
- Fase 3 concluída parcialmente: a migração dos arquivos de handler para
  `lubribot/bot/` e a máquina de estados explícita ficam para o próximo incremento.

## [2.0.0-dev] — 24/11/2026 — Fase 2: fundação, notificações e persistência

### Adicionado
- Pacote `lubribot/` em camadas: `config`, `database`, `models`, `domain`,
  `repositories`, `notifications`, `integrations`, `jobs`, `bot`.
- Configuração validada com Pydantic Settings; `.env.example` documentado.
- Logging estruturado (texto ou JSON) com eventos nomeados.
- `Database.unit_of_work()` com commit/rollback/close garantidos e pool
  configurável (`pool_pre_ping`, tamanho, reciclagem).
- Regra de próxima manutenção em Python puro (`domain/maintenance.py`), com
  intervalo padrão configurável (`INTERVALO_MANUTENCAO_DIAS`, 180).
- Outbox de notificações: chave de idempotência, tentativas, backoff exponencial,
  status `Falha` auditável.
- Agendador periódico com `pg_try_advisory_lock` (instância única) e
  desligamento gracioso por sinal.
- Alembic: `0001` baseline do schema legado e `0002` hardening idempotente.
- 94 testes automatizados (domínio, planejador, despachante, sender, config,
  mapeamento).

### Alterado
- `main.py` reduzido a entrypoint; bootstrap em `lubribot/app.py`.
- `repository/models.py` virou shim que reexporta `lubribot.models` (sem
  `create_all`, sem engine duplicado).
- `services/notificacoes_service.py` mantém a API antiga delegando à nova
  implementação (compatibilidade temporária).
- Relacionamentos ORM passaram de `lazy="subquery"` para `lazy="selectin"`.
- `requirements.txt` enxuto: 10 dependências reais (antes 73, com Flask, OpenCV,
  NumPy, PyAutoGUI e gcloud sem uso).
- `DOCUMENTACAO.md` marcado como referência histórica; `README.md` + `docs/`
  passam a ser a fonte atual.

### Corrigido
- **Estado global entre usuários:** `Veiculo`, `Servico`, `Manutencao` e listas de
  produtos eram objetos de módulo; o segundo uso fazia `UPDATE` no registro do
  usuário anterior. Agora cada conversa tem rascunho próprio (por `chat_id`).
- **Notificação:** `Servico.intervaloDias` inexistente e `INTERVALO_NOTIFICACAO`
  indefinida derrubavam a rotina (working tree). Regra migrada e coberta por testes.
- **Diagnóstico:** vírgula em `diagnostico.veiculo_id = veiculo.id,` gravava tupla e
  falhava no commit — o limite diário de 3 nunca era atingido.
- **Cache de dicas:** condição invertida fazia a dica nunca expirar.
- **Histórico de manutenções:** inner join escondia manutenções sem serviço;
  `custo`/`data` nulos quebravam a mensagem; botão de recibo só aparecia com foto.
- **Exclusões:** confirmação registrava handler novo a cada clique (capturando
  qualquer "Sim"/"Não" do bot); exclusão de produto/serviço/veículo não conferia dono.
- **Serviços quebrados:** `add_usuario(username=...)` e
  `add_veiculo(marca=..., ano=...)` usavam colunas inexistentes.
- **Scheduler:** laço antigo morria na primeira exceção e dormia 24h fixas.
- **Status de notificação:** `varchar(8)` não comportava "Cancelada" (9 chars).

### Segurança
- Token de produção removido de documento local (rotação recomendada no BotFather).
- `migration_data.sql` (contém PII) e 22 arquivos `.pyc` retirados do versionamento.
- `.gitignore` ampliado (`.env`, dumps, bytecode, caches, artefatos locais).
- Project ref do Supabase removido do exemplo em `migration/main.py`.
- Autorização por dono adicionada em veículo, produto, serviço e diagnóstico.
- Validação de entrada em placa, anos, km e custo.

### Pendente
- Migração dos fluxos/UX (F5) e performance (F6).
- Limpeza do histórico Git (decisão do dono; operação destrutiva).
- Rotação do token do Telegram no BotFather.
- Revisão independente por QA dos handlers reescritos.
