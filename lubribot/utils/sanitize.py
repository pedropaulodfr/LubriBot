"""Sanitização de HTML gerado pela IA antes de enviar ao Telegram.

O modelo pode devolver tags arbitrárias (inclusive `<script>`, atributos com
`onerror`, links `javascript:`). O Telegram aceita um subconjunto pequeno de
tags; qualquer coisa fora disso derruba o envio ou vira texto estranho.

Esta função:
- mantém apenas as tags permitidas pelo Telegram;
- remove **todos** os atributos, exceto `href` de `<a>` com esquema http/https;
- escapa o texto para não interpretar `<`/`>`/`&` indevidamente;
- descarta tags não permitidas mantendo o conteúdo textual.
"""

from __future__ import annotations

from html import escape
from html.parser import HTMLParser

TAGS_PERMITIDAS = {
    "b",
    "strong",
    "i",
    "em",
    "u",
    "s",
    "code",
    "pre",
    "a",
    "tg-spoiler",
    "br",
    "blockquote",
}

TAGS_SEM_FECHAMENTO = {"br"}

_ESQUEMAS_SEGUROS = ("http://", "https://")


class _Sanitizador(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.partes: list[str] = []
        self._pilha: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        tag = tag.lower()
        if tag not in TAGS_PERMITIDAS:
            return  # descarta a tag, mantém o conteúdo
        if tag == "a":
            href = ""
            for nome, valor in attrs:
                if nome.lower() == "href" and valor:
                    href = valor.strip()
                    break
            if not href.lower().startswith(_ESQUEMAS_SEGUROS):
                return  # link inseguro: mantém só o texto
            self.partes.append(f'<a href="{escape(href, quote=True)}">')
            self._pilha.append(tag)
            return
        if tag in TAGS_SEM_FECHAMENTO:
            self.partes.append("<br/>")
            return
        self.partes.append(f"<{tag}>")
        self._pilha.append(tag)

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if tag not in TAGS_PERMITIDAS or tag in TAGS_SEM_FECHAMENTO:
            return
        if tag in self._pilha:
            while self._pilha:
                aberta = self._pilha.pop()
                self.partes.append(f"</{aberta}>")
                if aberta == tag:
                    break

    def handle_data(self, data: str) -> None:
        self.partes.append(escape(data, quote=False))

    def handle_entityref(self, name: str) -> None:
        self.partes.append(f"&{name};")

    def handle_charref(self, name: str) -> None:
        self.partes.append(f"&#{name};")


def sanitizar_html(texto: str | None) -> str:
    """Devolve HTML seguro para `parse_mode="HTML"` do Telegram."""
    if not texto:
        return ""
    sanitizador = _Sanitizador()
    try:
        sanitizador.feed(texto)
        sanitizador.close()
    except Exception:
        # Em caso de HTML malformado, envia como texto puro (sem interpretação).
        return escape(texto, quote=False)
    while sanitizador._pilha:  # fecha tags abertas
        sanitizador.partes.append(f"</{sanitizador._pilha.pop()}>")
    return "".join(sanitizador.partes).strip()


def texto_simples(texto: str | None) -> str:
    """Remove todas as tags (para mensagens sem parse_mode)."""
    if not texto:
        return ""
    class _Limpar(HTMLParser):
        def __init__(self):
            super().__init__(convert_charrefs=True)
            self.partes: list[str] = []

        def handle_data(self, data):
            self.partes.append(data)

    limpador = _Limpar()
    limpador.feed(texto)
    limpador.close()
    return "".join(limpador.partes).strip()
