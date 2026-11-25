"""LubriBot — pacote principal da aplicação modernizada.

Organização em camadas (dependências apontam sempre para dentro):

    config      -> configuração validada (Pydantic Settings)
    database    -> engine, sessão e unidade de trabalho
    models      -> mapeamento SQLAlchemy (fonte única de verdade do schema)
    domain      -> regras de negócio puras, sem I/O
    repositories-> consultas e persistência
    notifications -> planejamento e despacho de notificações
    integrations -> serviços externos (Telegram, IA, S3)
    jobs        -> execução periódica e idempotente
    bot         -> bootstrap do Telegram
"""

__version__ = "2.0.0.dev0"
