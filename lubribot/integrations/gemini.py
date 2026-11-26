"""Cliente de IA (Google Gemini) com dois transportes.

- **SDK oficial** (``google-generativeai``), usado quando instalado
  (servidor/desktop).
- **REST** via ``requests``, usado onde o SDK não está disponível — caso do
  Android/Termux ARM 32 bits, onde ``grpcio`` não tem wheel.

A interface é a mesma (``gerar(prompt) -> str``), então os handlers não sabem
qual transporte está em uso.
"""

from __future__ import annotations

from typing import Any

from lubribot.config.settings import get_settings
from lubribot.utils.logging import get_logger

logger = get_logger(__name__)

MODELO_PADRAO = "gemini-2.5-flash"
ENDPOINT_REST = "https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"


def _texto_segredo(valor: Any) -> str | None:
    """Aceita ``str`` (perfil lite) ou ``SecretStr`` (perfil pydantic)."""
    if valor is None:
        return None
    if hasattr(valor, "get_secret_value"):
        return valor.get_secret_value()
    return str(valor)


class GeminiClient:
    """Gera texto com Gemini usando SDK ou REST, conforme disponibilidade."""

    def __init__(self, api_key: str | None, *, modelo: str = MODELO_PADRAO) -> None:
        self._api_key = api_key
        self._modelo = modelo
        self._sdk: Any = None
        if api_key:
            try:
                import google.generativeai as genai

                genai.configure(api_key=api_key)
                self._sdk = genai.GenerativeModel(modelo)
            except Exception:
                # Sem SDK (ou SDK quebrado): cai para REST.
                self._sdk = None

    @property
    def usa_sdk(self) -> bool:
        return self._sdk is not None

    def gerar(self, prompt: str) -> str:
        if not self._api_key:
            raise RuntimeError("GEMINI_ApiKey não configurada")
        if self._sdk is not None:
            resposta = self._sdk.generate_content(prompt)
            return (getattr(resposta, "text", "") or "").strip()
        return self._gerar_rest(prompt)

    # ------------------------------------------------------------------ REST
    def _gerar_rest(self, prompt: str) -> str:
        import requests

        url = ENDPOINT_REST.format(modelo=self._modelo)
        resposta = requests.post(
            url,
            params={"key": self._api_key},
            json={"contents": [{"parts": [{"text": prompt}]}]},
            timeout=90,
        )
        if resposta.status_code != 200:
            raise RuntimeError(
                f"Gemini HTTP {resposta.status_code}: {resposta.text[:200]}"
            )
        dados = resposta.json()
        try:
            return (dados["candidates"][0]["content"]["parts"][0]["text"] or "").strip()
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("resposta inesperada do Gemini") from exc


def get_gemini_client() -> GeminiClient:
    """Cria o cliente com a chave configurada no ambiente."""
    return GeminiClient(_texto_segredo(get_settings().gemini_api_key))
