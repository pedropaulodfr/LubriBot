# Runbook — instalação, migração e operação

## 1. Pré-requisitos

- Python 3.12+
- PostgreSQL 14+ (Supabase ou instância própria)
- Token de bot do Telegram (BotFather)
- Credenciais opcionais: Google Gemini, AWS S3 (sem elas, dicas/diagnóstico e
  fotos ficam indisponíveis, mas o bot sobe)

## 2. Instalação local

```bash
git clone <repo> && cd LubriBot
python -m venv .venv
# Windows: .venv\Scripts\activate    Linux/macOS: source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
```

Preencha o `.env`. Para desenvolvimento use `AMBIENTE=QA` com `TOKEN_QA` e
`STRING_CONNECTION_LOCAL`.

## 3. Banco de dados (Alembic)

### 3.1 Banco já existente (produção/QA atual)

O schema legado já está lá. Marque o baseline e aplique o hardening:

```bash
alembic stamp 0001
alembic upgrade head
```

O `0002` é idempotente (`IF NOT EXISTS`) e **não apaga dados**:

- alarga `notificacoes.status` para `varchar(20)`;
- adiciona `servicos.intervaloDias` (nullable);
- adiciona colunas do outbox em `notificacoes`;
- preenche `chave` das notificações antigas e renomeia duplicatas para
  `legacy:<id>` (sem excluir linhas);
- cria índices e o índice único `uq_notificacoes_chave`.

### 3.2 Banco novo

```bash
alembic upgrade head
```

### 3.3 Conferir sem conectar

```bash
alembic upgrade head --sql       # gera o SQL
alembic current                  # revisão aplicada
alembic history --verbose
```

### 3.4 Reverter

```bash
alembic downgrade 0001           # desfaz o hardening (mantém o schema legado)
```

> Em banco com dados, faça backup antes de qualquer `downgrade`.

## 4. Execução

```bash
python main.py
```

Sobe: long polling + job de notificações + health check `GET /ping`.

Variáveis que mudam o comportamento:

| Variável | Efeito |
|---|---|
| `AMBIENTE` | `PRODUÇÃO`/`PRODUCAO` seleciona credenciais de produção |
| `INTERVALO_NOTIFICACAO` | minutos entre ciclos (padrão 60) |
| `INTERVALO_MANUTENCAO_DIAS` | intervalo padrão quando o serviço não define (padrão 180) |
| `PORT` / `LOG_LEVEL` | porta do `/ping` e verbosidade |

## 5. Operação das notificações

### 5.1 Observar

Logs estruturados (texto por padrão, JSON com `LOG_JSON=true`). Eventos-chave:

```
scheduler_iniciado
scheduler_ciclo_concluido      resumo do planejamento e do despacho
notificacao_criada             chave, veiculo_id, proxima_data
notificacao_enviada
notificacao_reagendada         tentativas, atraso_segundos
notificacao_falha_definitiva   erro
scheduler_ciclo_ignorado_outra_instancia
```

### 5.2 Inspecionar o estado no banco

```sql
-- pendências e tentativas
SELECT id, chave, status, tentativas, "proximaTentativaEm", "ultimoErro", "enviadaEm"
  FROM notificacoes
 ORDER BY id DESC LIMIT 20;

-- o que ainda vai ser avaliado
SELECT id, tipo, status FROM veiculos WHERE status = 'Ativo';
```

### 5.3 Reprocessar uma pendência

```sql
UPDATE notificacoes
   SET status = 'Pendente', tentativas = 0,
       "proximaTentativaEm" = NULL, "ultimoErro" = NULL
 WHERE id = <id>;
```

O próximo ciclo envia. Para uma manutenção específica ser reavaliada, basta a
chave `ProximaManutencao:<manutencao_id>` não existir (ou ser removida).

### 5.4 Diagnóstico rápido

| Sintoma | Verificar |
|---|---|
| Nenhuma notificação criada | `servicos.intervaloDias` / `INTERVALO_MANUTENCAO_DIAS`; usuário com `receberNotificacoes = false`; veículo sem manutenção `Finalizada` |
| Cria mas não envia | `usuarios.telegram_id`; bloqueio do bot (403 → `Falha`) |
| Envia duplicado | mais de uma instância sem lock; conferir `scheduler_ciclo_ignorado_outra_instancia` |
| Status fora do esperado | coluna precisa ser `varchar(20)` (migração `0002`) |

## 6. Testes e qualidade

```bash
pytest                     # 94 testes, sem banco/rede
pytest -q tests/test_domain_maintenance.py
ruff check .               # se instalado
mypy lubribot              # se instalado
```

Testes de integração com Postgres (fase futura) usarão
`LUBRIBOT_TEST_DATABASE_URL` e banco dedicado — **nunca** produção.

## 7. Deploy no servidor do J4 Core

Alvo definido: VPS/container próprio. Sem Railway/Render.

### 7.1 Serviço systemd (exemplo)

```ini
[Unit]
Description=LubriBot
After=network-online.target

[Service]
Type=simple
User=lubribot
WorkingDirectory=/opt/lubribot
EnvironmentFile=/opt/lubribot/.env
ExecStart=/opt/lubribot/.venv/bin/python main.py
Restart=on-failure
RestartSec=10
# encerramento gracioso: o app trata SIGTERM
KillSignal=SIGTERM
TimeoutStopSec=45

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now lubribot
journalctl -u lubribot -f
```

### 7.2 Health check

```bash
curl -s http://127.0.0.1:10000/ping
# {"status": "ok", "message": "bot ativo"}
```

Em produção, exponha a porta apenas na rede interna/reverse proxy; o endpoint não
tem autenticação (retorna só status).

### 7.3 Checklist antes de subir

- [ ] `.env` no servidor com permissão `600`, fora do Git.
- [ ] `alembic current` mostra `0002`.
- [ ] Token rotacionado no BotFather se o antigo foi exposto.
- [ ] Backup do banco antes da primeira migração.
- [ ] `GET /ping` respondendo e `journalctl` sem traceback.
- [ ] Uma notificação de teste marcada `Pendente` foi enviada.

## 8. Backup e recuperação

- **Banco:** backup gerenciado do Supabase ou `pg_dump` agendado.
- **Estado das notificações:** está no banco; restaurar backup restaura a fila.
- **Segredos:** guardar no gerenciador de segredos do servidor, nunca em imagem
  Docker nem em repositório.
- **Rollback de aplicação:** `git checkout <tag>` + `pip install -r requirements.txt`
  + reinício do serviço (migrações não são revertidas automaticamente).

## 9. Segurança operacional

- Não versionar `.env`, dumps (`migration_data.sql`) nem bytecode.
- Rotacionar token do bot e chaves de IA/S3 se houver suspeita de exposição.
- O histórico Git ainda contém artefatos antigos (`.pyc` e dump). Limpar exige
  reescrita do histórico (`git filter-repo`) — decisão do dono, com clone de
  backup antes.
- Revisar permissões do role do banco: o bot precisa de DML nas tabelas, não de
  superusuário.
