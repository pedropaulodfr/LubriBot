# Decisões técnicas (ADRs)

Formato curto: contexto → decisão → consequência. Datas em 24/11/2026.

---

## ADR-001 — Manter pyTelegramBotAPI; não migrar de framework nesta fase

**Contexto:** o código usa `pyTelegramBotAPI` (síncrono, long polling) em todos os
17 handlers. Migrar para aiogram 3/PTB assíncrono exigiria reescrever 100% da
interface e dos fluxos.
**Decisão:** manter o framework e modernizar por dentro; isolar o envio em
`lubribot/integrations/telegram_sender.py` para permitir troca futura.
**Consequência:** handlers continuam síncronos; I/O externo pesado (Gemini/S3)
ainda bloqueia o polling até a fase F5/F6 (fila de execução).

## ADR-002 — Migrar a regra de notificação do banco para Python

**Contexto:** o commit em produção chama
`CALL sp_CriarNotificacaoProximaManutencao()`, mas o corpo da procedure **não
está no repositório** nem em `migration_data.sql`. O sistema dependia de um
objeto de banco impossível de recriar a partir do código.
**Decisão:** reimplementar a regra em `lubribot/domain/maintenance.py`, com
testes, e aposentar a dependência da procedure.
**Consequência:** a regra passa a ser versionada e testável; exige validar com o
dono do produto se o cálculo reconhecido (maior intervalo entre os serviços da
última manutenção) é o mesmo da procedure original.

## ADR-003 — Semântica de `intervaloDias`

**Contexto:** `Servico.intervaloDias` era citado no código e na documentação, mas
não existia no modelo nem no dump. O dono do projeto não recorda a finalidade.
**Decisão:** criar a coluna como **opcional** (`integer NULL`), com o significado
"intervalo recomendado de troca/revisão, em dias". Quando ausente, vale
`INTERVALO_MANUTENCAO_DIAS` (padrão 180). O cálculo usa o **maior** intervalo
entre os serviços realizados, preservando o comportamento documentado.
**Consequência:** nenhum dado existente muda; o comportamento atual (180 dias
para serviços sem intervalo) é explícito e configurável. Se o produto quiser
outro padrão, basta alterar a variável de ambiente.
**Atualização (25/11/2026):** ao conectar no banco real, confirmou-se que a coluna
`servicos.intervaloDias` **já existia no PostgreSQL** (apenas não estava mapeada
no ORM). A migração `0002` é idempotente e não a recriou; os valores existentes
passaram a ser lidos pela regra em Python.

## ADR-004 — Notificações como outbox persistido

**Contexto:** o modelo antigo gravava `status` e enviava; falha de envio causava
ou perda (commit antes do envio) ou duplicata (rollback depois do envio).
**Decisão:** usar a própria tabela `notificacoes` como outbox, com:
`chave` única (`ProximaManutencao:<manutencao_id>`), `tentativas`,
`proximaTentativaEm`, `enviadaEm`, `ultimoErro`; estados `Pendente/Enviada/
Cancelada/Falha`; retry com backoff exponencial; `pg_try_advisory_lock` para
instância única.
**Consequência:** restart não perde nem duplica; falha permanente fica auditável.

## ADR-005 — Alembic como fonte do schema; remover `create_all`

**Contexto:** `Base.metadata.create_all(engine)` rodava na importação do módulo e
não havia histórico de migrações.
**Decisão:** baseline `0001` (schema legado) + `0002` (hardening, idempotente com
`IF NOT EXISTS`). Banco existente: `alembic stamp 0001` + `upgrade head`.
**Consequência:** schema versionado e revisável; `create_all` removido do fluxo.

## ADR-006 — Configuração validada com normalização de ambiente

**Contexto:** `os.getenv('AMBIENTE') == "PRODUÇÃO"` com string acentuada: se a
variável viesse como `PRODUCAO`, o bot subiria em QA **em produção**.
**Decisão:** Pydantic Settings com validador que remove acentos, espaços e caixa;
falha no boot quando falta token ou string de conexão.
**Consequência:** erro de configuração aparece no start, não em produção silenciosa.

## ADR-007 — `lazy="selectin"` em vez de `"subquery"`

**Contexto:** todos os relacionamentos usavam `lazy='subquery'`, gerando carga
ampla e N+1 em listagens.
**Decisão:** `selectin` (lote) mantendo objetos legíveis após o commit.
**Consequência:** menos queries em listagens; ainda há pontos a medir na fase F6.

## ADR-008 — Manter PostgreSQL/Supabase via SQLAlchemy; não adotar `supabase-py`

**Contexto:** o app acessa o banco com SQLAlchemy + psycopg2 e role privilegiada.
RLS não se aplica (não há acesso anônimo).
**Decisão:** manter SQLAlchemy; em produção usar o **pooler** do Supabase e SSL.
`supabase-py` só faria sentido para Auth/Storage, que não são usados.
**Consequência:** nenhuma reescrita de dados; ganho de pool e reconexão.
**Atualização (25/11/2026):** o pooler correto do projeto é
`aws-1-us-east-1.pooler.supabase.com` na porta **5432 (modo sessão)** — a porta
6543 (transação) também conecta, mas liberaria o advisory lock ao fim de cada
transação, quebrando a trava de instância única do job. O host "direto"
(`db.*.supabase.co`) é IPv6 e apresentou timeout nesta rede; por isso o app usa o
pooler IPv4.

## ADR-009 — Descartar o working tree não commitado

**Contexto:** havia alterações locais em `main.py`, `repository/models.py`,
`migration/models.py` e `services/notificacoes_service.py`. A versão local
quebrava a notificação (`Servico.intervaloDias` inexistente,
`INTERVALO_NOTIFICACAO` não definida) e não representava produção.
**Decisão:** descartar (autorizado pelo dono) e reconstruir a funcionalidade na
arquitetura nova.
**Consequência:** base limpa a partir do `HEAD`; histórico preservado no Git.

## ADR-010 — Segredo removido e rotação recomendada

**Contexto:** o token de produção do bot estava em texto claro em
`Implementations/ImplementationPlan_DeployRailway_08062026.md` (arquivo não
rastreado) e havia `migration_data.sql` com PII versionado, além de 22 `.pyc`
versionados (incluindo bytecode de um `config.py` inexistente).
**Decisão:** remover o valor do arquivo, tirar dump e bytecode do índice, ampliar
o `.gitignore`. Rotação do token é ação do dono no BotFather.
**Consequência:** risco imediato mitigado; a **história** do Git ainda contém
esses artefatos — limpeza requer reescrita (`git filter-repo`/BFG) e é decisão
separada, por ser operação destrutiva.

## ADR-011 — Alvo de deploy: servidor do J4 Core (sem Render/Railway)

**Contexto:** documentação citava Railway, o workflow de ping apontava para
Render, e nenhum dos dois é o destino desejado.
**Decisão:** não configurar Railway/Render agora. Manter `python main.py` como
entrypoint padrão e documentar execução em VPS/container com `systemd` no runbook.
**Consequência:** nenhum acoplamento a plataforma; `PORT` e `GET /ping`
configuráveis.

## ADR-012 — Um rascunho de conversa por chat (sem estado global)

**Contexto:** `add_veiculo`/`add_manutencao`/`add_servico` mantinham objetos ORM e
listas em variáveis de módulo. Como o objeto já fora persistido, o próximo
`session.add` reanexava a instância e fazia `UPDATE` no registro anterior —
sobrescrevendo dados de outro usuário. `manutencaoProdutos` nunca era limpo.
**Decisão:** rascunhos em `dict[chat_id, Rascunho]` (dados simples, não ORM),
criados no início do fluxo e descartados no fim; gravação em transação única.
**Consequência:** conversas não se misturam; falha no meio não grava lixo.

## ADR-013 — Alargar `notificacoes.status` para `varchar(20)`

**Contexto:** o código grava `"Cancelada"` (9 caracteres) numa coluna
`varchar(8)`; no PostgreSQL isso gera erro de truncamento.
**Decisão:** alargar na migração `0002` (idempotente) e documentar no modelo.
**Consequência:** o fluxo de cancelamento passa a funcionar de fato.

## ADR-015 — Notificação por quilometragem (autorizada em 25/11/2026)

**Contexto:** só havia alerta por data. O KM era coletado nas manutenções, mas não
usado para agendamento, e não existia odômetro corrente.
**Decisão:**
- `servicos.intervaloKm` (opcional) define o intervalo em km por serviço;
  `INTERVALO_KM_PADRAO` cobre serviços sem valor; ausente = regra desligada.
- `veiculos.kmAtual` guarda o odômetro informado — atualizado pelo novo fluxo
  "📍 Atualizar KM" ou automaticamente ao registrar manutenção (usa o KM da nota).
- O aviso dispara quando `kmAtual >= ultima_km + max(intervaloKm)` **ou** quando a
  data entra na janela. Continua sendo um aviso por manutenção (chave única).
**Consequência:** a regra por km é opt-in e auditável; sem odômetro informado ela
simplesmente não dispara, sem gerar falso positivo.

## ADR-016 — Execução em produção a partir do `.env` local

**Contexto:** não há servidor do J4 Core provisionado ainda; o banco real é o
Supabase migrado em 25/11/2026.
**Decisão:** `AMBIENTE=PRODUÇÃO` no `.env`, selecionando `TOKEN` e
`STRING_CONNECTION` (pooler de sessão). Quando o servidor existir, o mesmo arquivo
(ou as mesmas variáveis) deve ser replicado lá, com permissão restrita.
**Consequência:** o processo local passa a falar com produção; iniciar `main.py`
nesta máquina assume o polling do bot e pode enviar notificações reais.

## ADR-014 — `DOCUMENTACAO.md` mantido como histórico

**Contexto:** o documento antigo (756 linhas) descreve arquitetura, fluxos e uma
coluna `intervaloDias` que não existia; também fala em Railway.
**Decisão:** não reescrever por cima; criar `README.md` + `docs/` como fonte
atual e tratar `DOCUMENTACAO.md` como referência histórica.
**Consequência:** nada de documentação duplicada conflitante, sem perder o
registro do desenho original.
