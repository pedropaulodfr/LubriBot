# Documentação do LubriBot

> **Aviso (24/11/2026):** este documento descreve a versão **anterior** do bot e é
> mantido como referência histórica. A fonte atual é o [README](README.md) e a
> pasta [docs/](docs/), que refletem a arquitetura modernizada.
>
> Divergências conhecidas: a coluna `servicos.intervaloDias` não existia no
> schema antigo (a regra vivia numa procedure não versionada); o deploy não é mais
> Railway; a geração de notificações agora é feita em Python
> (`lubribot/notifications/`), não por `CALL sp_CriarNotificacaoProximaManutencao`.

## Sumário

1. [Visão Geral](#1-visão-geral)
2. [Stack Tecnológica](#2-stack-tecnológica)
3. [Estrutura do Projeto](#3-estrutura-do-projeto)
4. [Arquitetura](#4-arquitetura)
5. [Banco de Dados](#5-banco-de-dados)
6. [Fluxos de Funcionalidades](#6-fluxos-de-funcionalidades)
7. [Camada de Serviços](#7-camada-de-serviços)
8. [Teclados (Keyboards)](#8-teclados-keyboards)
9. [Integração com Google Gemini AI](#9-integração-com-google-gemini-ai)
10. [Upload de Arquivos (AWS S3)](#10-upload-de-arquivos-aws-s3)
11. [Sistema de Notificações](#11-sistema-de-notificações)
12. [Ferramenta de Migração de Banco](#12-ferramenta-de-migração-de-banco)
13. [Variáveis de Ambiente](#13-variáveis-de-ambiente)
14. [Deploy](#14-deploy)
15. [Guia de Desenvolvimento](#15-guia-de-desenvolvimento)

---

## 1. Visão Geral

O **LubriBot** é um bot do Telegram desenvolvido em Python que auxilia proprietários de veículos a gerenciar a manutenção de sua frota. O bot permite registrar manutenções, veículos, serviços e produtos, além de oferecer diagnósticos e dicas geradas por inteligência artificial (Google Gemini).

### Público-alvo
Proprietários de veículos (carros, motos, caminhões, vans, ônibus) que desejam controlar gastos, histórico de manutenção e receber lembretes preventivos.

### Funcionalidades Principais
- Cadastro e gerenciamento de veículos
- Registro de manutenções com fotos e nota fiscal
- Catálogo de serviços e produtos
- Diagnóstico de problemas via IA
- Dicas de manutenção preventiva via IA
- Notificações programadas de manutenção
- Configurações personalizadas por usuário

---

## 2. Stack Tecnológica

| Componente | Tecnologia |
|---|---|
| **Linguagem** | Python 3.x |
| **Framework Bot** | pyTelegramBotAPI (telebot) v4.26.0 |
| **ORM** | SQLAlchemy 2.0.44 |
| **Banco de Dados** | PostgreSQL (via Supabase) |
| **Driver BD** | psycopg2 2.9.10 |
| **IA Generativa** | Google Gemini (`gemini-2.5-flash`) via `google-generativeai` |
| **Armazenamento** | AWS S3 (imagens) |
| **Consulta Veicular (VPIC)** | vpic-api 0.7.4 (NHTSA) |
| **HTTP Server** | Interno (BaseHTTPRequestHandler) para health check |
| **Deploy** | Railway (Nixpacks) |
| **Automação** | GitHub Actions (ping) |

---

## 3. Estrutura do Projeto

```
LubriBot/
├── main.py                          # Ponto de entrada do bot
├── requirements.txt                 # Dependências Python
├── .env                             # Variáveis de ambiente (ignorado pelo git)
├── .gitignore
├── DOCUMENTACAO.md                  # Esta documentação
│
├── handlers/                        # Handlers de mensagens do Telegram
│   ├── start_handle.py              # Comando /start e /teste
│   ├── add_veiculo_handle.py        # Fluxo de cadastro de veículo
│   ├── add_manutencao_handle.py     # Fluxo de registro de manutenção
│   ├── add_produtos_handle.py       # Cadastro de produto
│   ├── add_servico_handle.py        # Cadastro de serviço
│   ├── ver_veiculos_handle.py       # Visualização de veículos
│   ├── ver_manutencoes_handle.py    # Visualização de manutenções
│   ├── ver_produtos_handle.py       # Visualização de produtos
│   ├── ver_servicos_handle.py       # Visualização de serviços
│   ├── ver_dicas_handle.py          # Dicas de manutenção (IA)
│   ├── ver_diagnostico_handle.py    # Diagnóstico de problemas (IA)
│   ├── del_veiculo_handle.py        # Exclusão (soft delete) de veículo
│   ├── gerenciar_veiculos_handle.py # Submenu de veículos
│   ├── gerenciar_produtos_handle.py # Submenu de produtos
│   ├── gerenciar_servicos_handle.py # Submenu de serviços
│   ├── configuracoes_handle.py      # Configurações do usuário
│   └── mais_handle.py               # Submenu "Mais opções"
│
├── services/                        # Lógica de negócio
│   ├── veiculos_service.py          # CRUD veículos
│   ├── manutencoes_service.py       # Consultas de manutenção
│   ├── produtos_service.py          # CRUD produtos
│   ├── servicos_service.py          # CRUD serviços
│   ├── usuarios_service.py          # CRUD usuários
│   ├── usuarioparametros_service.py # Parâmetros de usuário
│   ├── notificacoes_service.py      # Processamento e envio de notificações
│   └── vpic_service.py             # Consulta NHTSA VPIC
│
├── keyboards/                       # Teclados do Telegram
│   ├── menu_principal_keyboard.py   # Menu principal
│   ├── veiculos_keyboard.py         # Lista de veículos / gerenciar
│   ├── tipos_veiculos_keyboard.py   # Tipos (Carro, Moto, etc.)
│   ├── modelos_veiculos_keyboard.py # Modelos (via VPIC + manual)
│   ├── markups_genericos_keyboard.py# Gerador genérico de teclados
│   ├── checkbox_genericos_keyboard.py # Checkbox inline universal
│   └── configuracoes_keyboard.py    # Teclado de configurações
│
├── repository/                      # Camada de dados
│   └── models.py                    # Modelos SQLAlchemy + engine
│
├── prompts/                         # Prompts para IA
│   ├── __init__.py
│   ├── dicas_prompt.py              # Prompt para dicas
│   └── diagnosticos_prompt.py       # Prompt para diagnósticos
│
├── utils/                           # Utilitários
│   ├── upload_file_async.py         # Upload para AWS S3
│   └── envio_mensagem.py            # Envio com auto-delete
│
├── migration/                       # Scripts de migração de BD
│   ├── main.py                      # Orquestrador
│   ├── models.py                    # Modelos (cópia para migração)
│   ├── extract.py                   # Extração do banco legado
│   ├── load.py                      # Carga no Supabase
│   ├── validate.py                  # Validação pós-migração
│   └── generate_sql.py             # Geração de script SQL
│
├── Implementations/
│   └── ImplementationPlan_DeployRailway_08062026.md  # Plano de deploy
│
├── .github/workflows/
│   └── ping-bot.yml                 # Health check periódico
│
├── Backups/                         # Backups locais
└── downloads/                       # Downloads temporários
```

---

## 4. Arquitetura

### 4.1 Inicialização (`main.py`)

O bot opera em **long polling** (não usa webhooks) com 3 threads paralelas:

```
main.py
│
├── Thread 1: start_bot()
│   └── bot.infinity_polling() — Escuta mensagens do Telegram
│
├── Thread 2: tarefa_periodica()
│   ├── ProcessarNotificacoes() — Gera notificações pendentes
│   └── EnviaNotificacoes(bot) — Envia notificações via bot
│
└── Thread Principal: start_server()
    └── Servidor HTTP na porta $PORT (obrigatório no Render/Railway)
        └── GET /ping → {"status": "ok", "message": "bot ativo"}
```

### 4.2 Fluxo de Mensagens

```
Telegram → pyTelegramBotAPI → Handler (filtro por message.text)
    → Validação (usuário existe?)
    → Fluxo de perguntas (register_next_step_handler)
    → Services (lógica)
    → Repository (SQLAlchemy)
    → PostgreSQL (Supabase)
```

### 4.3 Seleção de Ambiente

O bot suporta dois ambientes controlados pela env var `AMBIENTE`:

| Ambiente | `AMBIENTE` | Token | String de Conexão |
|---|---|---|---|
| Produção | `PRODUÇÃO` | `TOKEN` | `STRING_CONNECTION` |
| QA/Dev | qualquer outro | `TOKEN_QA` | `STRING_CONNECTION_LOCAL` |

---

## 5. Banco de Dados

### 5.1 Modelo Relacional

```
usuarios
├── id (PK)
├── telegram_id
├── perfil ("Proprietario")
├── primeiroNome, ultimoNome, usuarioNome
├── CPF, email, telefone, foto
└── status ("Ativo"/"Inativo")

usuarioparametros
├── id (PK)
├── usuario_id (FK → usuarios.id)
├── receberNotificacoes (Boolean)
└── diasNotificacao (Integer)

veiculos
├── id (PK)
├── usuario_id (FK → usuarios.id)
├── tipo (Carro/Moto/Caminhão/Ônibus/Van/Outro)
├── placa (7 caracteres)
├── renavam
├── fabricante, modelo, cor
├── anoModelo, anoFabricacao
└── status ("Ativo"/"Deletado")

veiculodica
├── id (PK)
├── veiculo_id (FK → veiculos.id)
├── texto (Text — HTML formatado pela IA)
└── datacriacao

veiculodiagnosticos
├── id (PK)
├── veiculo_id (FK → veiculos.id)
├── problema, diagnostico (Text)
├── datacriacao
├── resolvido (Boolean)
└── util (Boolean)

manutencoes
├── id (PK)
├── data, km
├── veiculo_id (FK → veiculos.id)
├── observacao
├── status ("Finalizada")
├── custo (Float)
├── imagem (file_id.jpg)
└── imagemNotaServico (file_id.jpg)

servicos
├── id (PK)
├── descricao
├── status ("Ativo"/"Excluido")
└── usuario_id (FK → usuarios.id)

produtos
├── id (PK)
├── descricao
├── status ("Ativo"/"Excluido")
└── usuario_id (FK → usuarios.id)

manutencaoservicos
├── id (PK)
├── manutencao_id (FK → manutencoes.id)
└── servico_id (FK → servicos.id)

manutencaoprodutos
├── id (PK)
├── manutencao_id (FK → manutencoes.id)
└── produto_id (FK → produtos.id)

servicoprodutos
├── id (PK)
├── servico_id (FK → servicos.id)
└── produto_id (FK → produtos.id)

notificacoes
├── id (PK)
├── dataNotificacao
├── tipoNotificacao ("ProximaManutencao")
├── usuario_id (FK → usuarios.id)
├── servico_id (FK → servicos.id)
├── manutencao_id (FK → manutencoes.id)
├── veiculo_id (FK → veiculos.id)
├── titulo, conteudo (Text)
└── status ("Pendente"/"Enviada"/"Cancelada")
```

### 5.2 Relacionamentos Chave

- `usuarios` 1:N `veiculos`
- `usuarios` 1:1 `usuarioparametros`
- `veiculos` 1:N `manutencoes`
- `veiculos` 1:N `veiculodica`
- `veiculos` 1:N `veiculodiagnosticos`
- `manutencoes` N:N `servicos` via `manutencaoservicos`
- `manutencoes` N:N `produtos` via `manutencaoprodutos`
- `servicos` N:N `produtos` via `servicoprodutos`

### 5.3 Criação Automática

`Base.metadata.create_all(engine)` é chamado ao importar `repository/models.py`, criando todas as tabelas automaticamente se não existirem.

---

## 6. Fluxos de Funcionalidades

### 6.1 Menu Principal

```
🛠️ Registrar Manutenção
🚘 Gerenciar Veículos
... (mais opções)
💡 Dicas
⚠️ Diagnósticos
⚙️ Configurações
```

O botão `...` abre um submenu com:
```
🔎 Ver Manutenções
🛢️ Gerenciar Produtos
🧰 Gerenciar Serviços
```

### 6.2 Cadastro de Veículo (`add_veiculo_handle.py`)

**Entrada**: Botão "➕ Adicionar Veículo" (via submenu "🚘 Gerenciar Veículos")

**Fluxo**:
1. Verifica se usuário existe, cria veículo com `status = "Ativo"`
2. Solicita placa (7 caracteres, valida duplicidade por usuário)
3. Solicita tipo (Carro/Moto/Caminhão/Ônibus/Van/Outro)
4. Solicita fabricante/marca
5. Busca modelos na API VPIC da NHTSA (consulta por marca + tipo)
   - Se encontrar modelos, exibe lista + opção "Inserir manualmente"
   - Se não encontrar, solicita digitação manual
6. Solicita cor (inline keyboard com cores predefinidas + manual)
7. Solicita ano de fabricação e ano do modelo (4 dígitos)
8. Solicita RENAVAM (opcional)
9. Salva no banco

### 6.3 Registro de Manutenção (`add_manutencao_handle.py`)

**Entrada**: Botão "🛠️ Registrar Manutenção"

**Fluxo**:
1. Verifica usuário e veículos cadastrados
2. Seleciona veículo (teclado com placas)
3. Escolhe data ("Hoje" ou data manual DD/MM/AAAA)
4. Seleciona serviço realizado (lista do usuário + "Outro" que cria novo serviço)
5. Informa quilometragem (KM)
6. Envia foto do painel (upload para AWS S3)
7. Pergunta se deseja informar produtos utilizados
   - Se sim: checkbox inline com produtos disponíveis
8. Informa custo (R$)
9. Observação opcional
10. Pergunta se deseja anexar nota de serviço/recibo (foto → S3)
11. Salva manutenção + associa serviços e produtos

### 6.4 Visualização de Veículos (`ver_veiculos_handle.py`)

**Entrada**: Botão "🔎 Visualizar Veículos"

Exibe todos os veículos ativos do usuário com informações formatadas:
```
🏍️ Tipo: Moto
🔖 Marca: Honda
🚘 Modelo: CG 160
🪧 Placa: ABC-1234
📆 Ano de Fabricação: 2024
📆 Ano do Modelo: 2024
🎨 Cor: Vermelha
📄 RENAVAM: 12345678901
🔎 Status: Ativo
```

### 6.5 Visualização de Manutenções (`ver_manutencoes_handle.py`)

**Entrada**: Botão "🔎 Ver Manutenções" (submenu `...`)

Oferece duas opções:
- **Ver por veículo**: Seleciona veículo, exibe manutenções daquele veículo
- **Ver todas**: Exibe manutenções de todos os veículos

Cada manutenção exibe: veículo, data, serviço, produtos, custo, observações.
Se houver imagem ou nota, exibe botão inline para visualizar (URL do S3).

### 6.6 Gerenciamento de Produtos (`gerenciar_produtos_handle.py`)

**Entrada**: Botão "🛢️ Gerenciar Produtos" (submenu `...`)

Submenu com:
- "🔍🛢️ Ver Produtos" → Lista produtos com botão "🗑️ Excluir" (soft delete)
- "➕🛢️ Adicionar Produtos" → Solicita descrição e salva

### 6.7 Gerenciamento de Serviços (`gerenciar_servicos_handle.py`)

**Entrada**: Botão "🧰 Gerenciar Serviços" (submenu `...`)

Submenu com:
- "🔍🧰 Ver Serviços" → Lista serviços com botão "🗑️ Excluir" (soft delete)
- "➕🧰 Adicionar Serviço" → Solicita descrição e salva

### 6.8 Remoção de Veículo (`del_veiculo_handle.py`)

**Entrada**: Botão "➖ Remover Veículo" (submenu "🚘 Gerenciar Veículos")

Soft delete: altera `status` para `"Deletado"`. O registro permanece no banco.

### 6.9 Dicas de Manutenção (`ver_dicas_handle.py`)

**Entrada**: Botão "💡 Dicas"

1. Seleciona veículo
2. Verifica se já existe dica gerada nos últimos 30 dias
   - Se sim, reutiliza (evita custos desnecessários de API)
   - Se não, gera nova dica via Google Gemini
3. Exibe dica formatada com HTML
4. Salva/atualiza no banco

### 6.10 Diagnóstico de Problemas (`ver_diagnostico_handle.py`)

**Entrada**: Botão "⚠️ Diagnósticos"

1. Seleciona veículo
2. Relata o problema (texto livre)
3. Verifica limite diário (máx. 3 diagnósticos/dia)
4. Envia para Google Gemini com prompt especializado
5. Exibe diagnóstico com causas, soluções e recomendações
6. Pergunta se o problema foi resolvido (feedback)
7. Salva no banco

### 6.11 Configurações (`configuracoes_handle.py`)

**Entrada**: Botão "⚙️ Configurações"

- **🔔 Ativar / 🔕 Desativar Notificações**: Alterna `receberNotificacoes`
- **⏱️ Configurar Período de Notificação**: Define `diasNotificacao` (antecedência em dias)
- **❌ Cancelar**: Volta ao menu principal

---

## 7. Camada de Serviços

### 7.1 `veiculos_service.py`
| Função | Descrição |
|---|---|
| `get_veiculos_by_usuario(usuario_id)` | Retorna veículos ativos de um usuário |
| `get_veiculos_by_telegram_id(telegram_id)` | Veículos por Telegram ID (via join) |
| `get_veiculo_by_placa(placa)` | Busca veículo por placa |
| `add_veiculo(...)` | Cria novo veículo |

### 7.2 `manutencoes_service.py`
| Função | Descrição |
|---|---|
| `get_manutencoes_by_usuario(usuario_id)` | Manutenções de todos veículos do usuário |
| `get_manutencoes_by_veiculos(veiculo_id)` | Manutenções de um veículo específico |

### 7.3 `produtos_service.py`
| Função | Descrição |
|---|---|
| `get_all_produtos()` | Todos produtos ativos (descrição + ID formatado) |
| `get_all_produtos_manutencao(usuario_id)` | Produtos disponíveis para manutenção (globais + do usuário) |
| `get_produto_by_descricao_completa(desc)` | Busca por "descricao (000001)" |
| `get_produtos_by_usuario(usuario_id)` | Produtos do usuário |
| `get_produtos_by_telegram_id(telegram_id)` | Produtos por Telegram ID |

### 7.4 `servicos_service.py`
| Função | Descrição |
|---|---|
| `get_all_servicos(usuario_id)` | Serviços ativos (opcional: filtrados por usuário) |
| `get_servico_by_descricao(descricao)` | Busca por descrição |
| `get_servico_by_id(id)` | Busca por ID |
| `get_servicos_by_usuario(usuario_id)` | Serviços do usuário |

### 7.5 `vpic_service.py`
Consulta a API pública **NHTSA VPIC** (Vehicle Product Information Catalog) para obter modelos de veículos por marca e tipo.

| Função | Descrição |
|---|---|
| `get_modelos_por_marca_ano(marca, ano, tipo_veiculo)` | Retorna lista ordenada de modelos |

Mapeamento de tipos:
- "Moto" → "Motorcycle"
- "Carro" → "Passenger Car"
- "Caminhão" → "Truck"

### 7.6 `notificacoes_service.py`
Sistema de notificações preditivas de manutenção. Executado em loop a cada `INTERVALO_NOTIFICACAO` minutos (variável de ambiente).

**`ProcessarNotificacoes()`**:
1. Para cada veículo ativo:
   - Verifica se usuário tem notificações ativas (`receberNotificacoes == True`)
   - Busca a última manutenção finalizada
   - Calcula `max_intervalo` entre os serviços realizados
   - Calcula `proxima_data = ultima_manutencao.data + max_intervalo`
   - Se a próxima data está dentro da janela de notificação do usuário (`diasNotificacao`)
   - Cria `Notificacao` com status "Pendente" (evita duplicatas)

**`EnviaNotificacoes(bot)`**:
1. Busca notificações "Pendente"
2. Para cada uma:
   - Verifica se usuário ainda quer receber notificações
   - Envia mensagem via `bot.send_message()`
   - Atualiza status para "Enviada" ou "Cancelada"

---

## 8. Teclados (Keyboards)

### 8.1 `menu_principal_keyboard.py`
Teclado Reply principal com 6 botões organizados em layout 2-colunas.

### 8.2 `veiculos_keyboard.py`
- `gerenciar_veiculos_keyboard()`: Submenu de ações (Visualizar, Adicionar, Remover)
- `veiculos_keyboard(veiculos)`: Gera botões dinâmicos no formato `PLACA-1234 - Tipo Marca Modelo Cor (Ano)`

### 8.3 `tipos_veiculos_keyboard.py`
Teclado fixo com tipos: Carro, Moto, Caminhão, Ônibus, Van, Outro, Cancelar.

### 8.4 `modelos_veiculos_keyboard.py`
Teclado dinâmico com modelos da VPIC + opções "Inserir manualmente" e "Cancelar".

### 8.5 `markups_genericos_keyboard.py`
Função genérica que aceita uma lista de dicionários/objetos e um campo identificador, gerando teclados Reply dinâmicos. Usado em múltiplos fluxos (datas, confirmações, seleções).

### 8.6 `checkbox_genericos_keyboard.py`
Sistema de checkbox inline universal que suporta múltiplos usuários simultâneos:
- Estado gerenciado via dicionário global `CHECKBOX_STATE` (por `chat_id`)
- Exibe opções com ☐/☑
- Botão "✅ Confirmar" finaliza e executa callback
- Edita mensagem inline sem enviar novas mensagens

### 8.7 `configuracoes_keyboard.py`
Teclado dinâmico baseado no estado atual do usuário:
- Exibe "🔕 Desativar" ou "🔔 Ativar" conforme estado atual
- Botão "⏱️ Configurar Período de Notificação"
- Botão "❌ Cancelar"

---

## 9. Integração com Google Gemini AI

### 9.1 Configuração
```python
genai.configure(api_key=os.getenv("GEMINI_ApiKey"))
modelo = genai.GenerativeModel("gemini-2.5-flash")
```

### 9.2 Dicas de Manutenção (`dicas_prompt.py`)
Prompt que instrui o modelo a atuar como mecânico sênior, gerando dicas curtas e práticas para o veículo específico do usuário.

**Diretrizes do prompt**:
- Texto dinâmico e amigável com emojis
- Tags HTML permitidas: `<b>`, `<i>`, `<u>`, `<code>`, etc.
- Tópicos de 2-3 frases
- Foco em: vida útil, desempenho, problemas comuns, redução de custos
- Máximo 1500 caracteres
- Sem cumprimentos ou histórias

### 9.3 Diagnóstico de Problemas (`diagnosticos_prompt.py`)
Prompt que instrui o modelo a diagnosticar problemas relatados pelo usuário.

**Estrutura do diagnóstico**:
1. Possíveis causas
2. Passos para solução
3. Sugestões de manutenção preventiva
4. Indicação se pode resolver sozinho ou precisa de mecânico

**Limitações**:
- Máximo 3 diagnósticos por dia por usuário (controlado por query no banco)
- Cache de dicas por 30 dias

---

## 10. Upload de Arquivos (AWS S3)

### 10.1 `upload_file_async.py`
Função `upload(base64, tipo, filename)`:

1. Decodifica base64
2. Inicializa cliente S3 com credenciais do ambiente
3. Envia para bucket S3 no caminho `uploads/{tipo}/{filename}`
4. Retorna URL pública

### 10.2 Fluxo de Upload
```
[Usuário envia foto no Telegram]
    → bot.get_file(file_id)
    → bot.download_file(file_path)
    → base64.b64encode()
    → upload(base64, tipo="imagens", filename="file_id.jpg")
    → AWS S3: lubribot/uploads/imagens/file_id.jpg
```

As imagens são referenciadas via URL pública:
```
https://{BUCKET_NAME}.s3.{REGION}.amazonaws.com/uploads/imagens/{filename}
```

### 10.3 Utilitário `envio_mensagem.py`
`send_and_delete(bot, chat_id, text, delay)`:
- Envia mensagem e a deleta automaticamente após `delay` segundos
- Usado para mensagens temporárias ("Aguarde...", "Gerando...")
- Executa em thread separada (daemon)

---

## 11. Sistema de Notificações

### 11.1 Configuração
- **Intervalo de verificação**: `INTERVALO_NOTIFICACAO` minutos (via `env`)
- **Por usuário**: Ativar/desativar + período de antecedência em dias

### 11.2 Lógica de Cálculo
```
proxima_data = ultima_manutencao.data + max(intervaloDias dos serviços realizados)
```

Exemplo: Se o serviço "Troca de Óleo" tem `intervaloDias = 180` (6 meses), a próxima manutenção será calculada 180 dias após a última.

### 11.3 Estados da Notificação
- `Pendente`: Aguardando envio
- `Enviada`: Enviada com sucesso
- `Cancelada`: Usuário desativou notificações

---

## 12. Ferramenta de Migração de Banco

### 12.1 Visão Geral
Scripts em `migration/` para migrar dados de um banco PostgreSQL legado para o Supabase.

### 12.2 Componentes

| Arquivo | Função |
|---|---|
| `main.py` | Orquestrador: executa ETL completo na ordem correta |
| `models.py` | Cópia dos modelos SQLAlchemy (sem `create_all`) |
| `extract.py` | Extrai todos registros do banco de origem |
| `load.py` | Insere no Supabase em lotes de 500, preservando IDs, com `ON CONFLICT DO NOTHING` |
| `validate.py` | Compara contagem de registros entre origem e destino |
| `generate_sql.py` | Gera script SQL para migração manual |

### 12.3 Ordem de Migração (baseada em FK)
```
Usuario → UsuarioParametro → Veiculo → Servico → Produto →
VeiculoDica → VeiculoDiagnosticos → Manutencao →
ServicoProduto → ManutencaoServico → ManutencaoProduto → Notificacao
```

### 12.4 Uso
```bash
# Migração completa
python -m migration.main

# Apenas gerar script SQL
python -m migration.generate_sql
```

Variáveis de ambiente necessárias:
- `SOURCE_DB_URL` ou `STRING_CONNECTION` (origem)
- `SUPABASE_DB_URL` (destino)

---

## 13. Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `AMBIENTE` | Sim | `"PRODUÇÃO"` para produção, qualquer outro para QA |
| `TOKEN` | Sim | Token do bot Telegram (produção) |
| `TOKEN_QA` | Não | Token do bot Telegram (QA/desenvolvimento) |
| `STRING_CONNECTION` | Sim | URL de conexão PostgreSQL (produção) |
| `STRING_CONNECTION_LOCAL` | Não | URL de conexão PostgreSQL (QA/desenvolvimento) |
| `GEMINI_ApiKey` | Sim | Chave da API Google Gemini |
| `AWS_AccessKey` | Sim | Access Key AWS S3 |
| `AWS_SecretKey` | Sim | Secret Key AWS S3 |
| `AWS_Region` | Sim | Região AWS (ex: `us-east-2`) |
| `AWS_BucketName` | Sim | Nome do bucket S3 (ex: `lubribot`) |
| `INTERVALO_NOTIFICACAO` | Não | Minutos entre verificações de notificação (default: valor fixo no código) |
| `PORT` | Não | Porta do servidor HTTP (definido pela plataforma de deploy) |

---

## 14. Deploy

### 14.1 Plataforma
O deploy é feito na **Railway** usando Nixpacks (build automático para Python).

### 14.2 Configuração (`railway.toml`)
```toml
[build]
builder = "NIXPACKS"

[deploy]
startCommand = "python main.py"
restartPolicyType = "ON_FAILURE"
restartPolicyMaxRetries = 10
```

### 14.3 Dependência psycopg2
Em ambientes Linux (Railway), `psycopg2` requer compilação nativa. Para deploy, recomenda-se substituir por `psycopg2-binary` no `requirements.txt`.

### 14.4 Servidor HTTP
O bot inicia um servidor HTTP interno na porta `$PORT` (ou 10000) para atender aos requisitos de health check da plataforma:

```bash
GET /ping → 200 {"status": "ok", "message": "bot ativo"}
```

### 14.5 GitHub Actions
`.github/workflows/ping-bot.yml` faz health check periódico para manter o bot ativo (evita sleep em plataformas free).

---

## 15. Guia de Desenvolvimento

### 15.1 Ambiente Local

```bash
# Clone o repositório
git clone https://github.com/pedropaulodfr/LubriBot.git
cd LubriBot

# Crie ambiente virtual
python -m venv venv
.\venv\Scripts\activate  # Windows

# Instale dependências
pip install -r requirements.txt

# Configure .env (veja seção 13)
# Execute
python main.py
```

### 15.2 Estrutura para Novas Funcionalidades

1. **Handler** em `handlers/`: Lida com a entrada do usuário e fluxo de mensagens
2. **Service** em `services/`: Lógica de negócio e consultas ao banco
3. **Model** em `repository/models.py`: Se necessário, novo modelo SQLAlchemy
4. **Keyboard** em `keyboards/`: Se necessário, novo teclado
5. Registrar no `main.py`: Chamar a função handler passando o bot

### 15.3 Convenções

- **Handlers**: Função que recebe `bot`, registra `@bot.message_handler` e/ou `@bot.callback_query_handler`
- **Services**: Funções puras que recebem/são dados, sem dependência do bot
- **Soft delete**: Registros são marcados como "Deletado" ou "Excluido", não removidos
- **Sessões SQLAlchemy**: Sempre usar `try/finally` com `session.close()`
- **Variáveis de ambiente**: Carregadas via `python-dotenv`

### 15.4 Dependências Principais

| Pacote | Versão | Uso |
|---|---|---|
| pyTelegramBotAPI | 4.26.0 | Framework do bot |
| SQLAlchemy | 2.0.44 | ORM |
| psycopg2 | 2.9.10 | Driver PostgreSQL |
| google-generativeai | 0.8.5 | Google Gemini |
| boto3 | 1.41.3 | AWS S3 |
| python-dotenv | 1.2.1 | Variáveis de ambiente |
| vpic-api | 0.7.4 | Consulta NHTSA VPIC |
| Flask | 3.1.0 | Dependência (não utilizado ativamente) |

---

> Documentação gerada em Julho de 2026.
> Projeto: [github.com/pedropaulodfr/LubriBot](https://github.com/pedropaulodfr/LubriBot)
