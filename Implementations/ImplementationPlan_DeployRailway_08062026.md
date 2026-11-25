# Deploy do LubriBot na Railway

## Descrição

Deploy completo do bot Telegram **LubriBot** (Python + pyTelegramBotAPI) na plataforma Railway, conectando ao banco de dados Supabase (PostgreSQL) já existente, integrando via repositório GitHub.

---

## Análise do Projeto

### Stack Identificada
- **Linguagem**: Python 3.x
- **Framework do Bot**: pyTelegramBotAPI (telebot) v4.26.0
- **Banco de Dados**: PostgreSQL via Supabase (SQLAlchemy + psycopg2)
- **Serviços externos**: AWS S3 (imagens), Google Gemini AI (diagnóstico/dicas)
- **Modo de operação**: Long Polling (infinity_polling) + servidor HTTP interno (porta dinâmica)
- **Repositório**: https://github.com/pedropaulodfr/LubriBot.git

### Estrutura do Projeto
```
LubriBot/
├── main.py                  # Ponto de entrada
├── requirements.txt         # Dependências (74 pacotes)
├── handlers/                # Handlers do Telegram
├── services/                # Serviços (notificações, usuários, etc.)
├── repository/              # Models SQLAlchemy
├── keyboards/               # Teclados inline
├── prompts/                 # Prompts para AI
└── utils/                   # Utilitários
```

### Lógica de Inicialização (main.py)
O bot usa `AMBIENTE` para selecionar o token e a connection string:
- `AMBIENTE=PRODUÇÃO` → usa `TOKEN` + `STRING_CONNECTION` (Supabase)
- `AMBIENTE=QA` → usa `TOKEN_QA` + `STRING_CONNECTION_LOCAL`

No Railway, `AMBIENTE=PRODUÇÃO` será configurado.

---

## Variáveis de Ambiente Necessárias (Produção)

| Variável | Valor | Observação |
|----------|-------|-----------|
| `AMBIENTE` | `PRODUÇÃO` | Ativa modo produção |
| `TOKEN` | Token bot produção | Do .env local |
| `STRING_CONNECTION` | URL Supabase | Do .env local |
| `GEMINI_ApiKey` | Chave Gemini | Do .env local |
| `AWS_AccessKey` | Chave AWS | Do .env local |
| `AWS_SecretKey` | Chave secreta AWS | Do .env local |
| `AWS_Region` | `us-east-2` | Do .env local |
| `AWS_BucketName` | `lubribot` | Do .env local |
| `PORT` | Automático | Railway define |

---

## Problemas Identificados

### 1. psycopg2 vs psycopg2-binary
O `requirements.txt` usa `psycopg2==2.9.10` que requer compilação nativa. No Railway (Linux), isso pode causar falha de build. Será substituído por `psycopg2-binary==2.9.10`.

### 2. Ausência de arquivo de configuração de deploy
Não existe `railway.toml` nem `Procfile`. Será criado um `railway.toml`.

---

## Estratégia de Deploy

### Projeto Railway
- Projeto existente `industrious-spontaneity` não parece ser o LubriBot
- Será criado um **novo projeto** chamado `lubribot`

### Serviço
- Conectado ao repositório GitHub: `pedropaulodfr/LubriBot`
- Branch: `main`
- Build: Nixpacks (detecta Python automaticamente)
- Start Command: `python main.py`

---

## Arquivos a Criar/Modificar

### [NEW] railway.toml
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python main.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### [MODIFY] requirements.txt
- `psycopg2==2.9.10` → `psycopg2-binary==2.9.10`

---

## Plano de Execução

1. ✅ Criar pastas `Implementations/` e `Backups/`
2. Criar `railway.toml` no projeto
3. Atualizar `requirements.txt`
4. Commit + push para GitHub
5. Criar novo projeto `lubribot` na Railway via MCP
6. Criar serviço conectado ao GitHub repo
7. Configurar variáveis de ambiente
8. Verificar logs e corrigir erros
9. Validar funcionamento

---

## Open Questions

> [!IMPORTANT]
> O projeto existente `industrious-spontaneity` na Railway é seu? Devo criar um **novo projeto** `lubribot` separado ou deployar dentro desse projeto existente?

> [!WARNING]
> O `requirements.txt` inclui `psycopg2==2.9.10` que requer compilação nativa no Linux. Será substituído por `psycopg2-binary==2.9.10`. Isso não afeta a funcionalidade.

> [!IMPORTANT]
> **Segredo removido em 24/11/2026.** Este arquivo continha o token de produção do bot em texto claro. O valor foi apagado e o token deve ser rotacionado no BotFather. Nunca grave credenciais em documentos: use `.env` (ignorado pelo Git) ou o gerenciador de segredos do servidor.
