"""Medição de tempo das operações caras (F6).

O bot é síncrono: uma chamada ao Gemini ou ao S3 segura o polling. Antes de
otimizar, é preciso medir. Este contexto registra a duração em log estruturado,
para permitir comparar p50/p95 depois com dados reais.
"""

from __future__ import annotations

import time
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any

from lubribot.utils.logging import get_logger

logger = get_logger(__name__)


@contextmanager
def medir(evento: str, **campos: Any) -> Iterator[dict[str, Any]]:
    """Mede a duração de um bloco e loga ``evento`` com ``duracao_ms``.

    Uso::

        with medir("gemini_diagnostico", usuario_id=1) as info:
            resposta = modelo.generate_content(prompt)
        # log: gemini_diagnostico duracao_ms=...
        info["ok"]  # False se houve exceção (a exceção é propagada)
    """
    inicio = time.perf_counter()
    info: dict[str, Any] = {"ok": False}
    try:
        yield info
        info["ok"] = True
    finally:
        duracao_ms = round((time.perf_counter() - inicio) * 1000, 1)
        logger.info(
            evento,
            extra={
                "duracao_ms": duracao_ms,
                "ok": info["ok"],
                **campos,
            },
        )


def excedeu(info: dict[str, Any], limite_ms: int) -> bool:
    """Açúcar para checar se um bloco passou do orçamento de tempo."""
    return bool(info.get("duracao_ms", 0) > limite_ms)
