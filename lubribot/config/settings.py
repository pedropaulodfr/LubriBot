"""Configuração central da aplicação — seletor de implementação.

Duas variantes, mesma interface pública:

- :mod:`lubribot.config.settings_pydantic` — usada quando Pydantic está instalado
  (servidor/desktop). Validação rica, mensagens de erro detalhadas.
- :mod:`lubribot.config.settings_lite` — usada quando Pydantic **não** está
  disponível (Android/Termux ARM 32 bits, onde não há wheel de ``pydantic-core``).

O restante do código importa apenas ``Settings`` e ``get_settings`` daqui.
"""

from __future__ import annotations

from functools import lru_cache

from lubribot.config.settings_common import (
    PROJECT_ROOT,
    ConfigurationError,
    normalizar_ambiente,
)

try:  # caminho preferencial
    from lubribot.config.settings_pydantic import Settings

    IMPLEMENTACAO = "pydantic"
except Exception:  # ImportError ou instalação quebrada
    from lubribot.config.settings_lite import Settings  # type: ignore[assignment]

    IMPLEMENTACAO = "lite"

__all__ = [
    "IMPLEMENTACAO",
    "PROJECT_ROOT",
    "ConfigurationError",
    "Settings",
    "get_settings",
    "normalizar_ambiente",
    "reload_settings",
]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Retorna a configuração carregada (memoizada)."""
    return Settings()  # type: ignore[call-arg]


def reload_settings() -> Settings:
    """Descarta o cache e recarrega a configuração."""
    get_settings.cache_clear()
    return get_settings()
