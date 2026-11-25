# Changelog

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
