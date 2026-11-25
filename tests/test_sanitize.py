"""Testes da sanitização de HTML gerado pela IA."""

from __future__ import annotations

from lubribot.utils.sanitize import sanitizar_html, texto_simples


class TestSanitizarHtml:
    def test_mantem_tags_permitidas(self):
        assert sanitizar_html("<b>negrito</b> e <i>itálico</i>") == (
            "<b>negrito</b> e <i>itálico</i>"
        )

    def test_remove_script_e_mantem_texto(self):
        resultado = sanitizar_html("<script>alert('x')</script>Faça a troca")
        assert "<script>" not in resultado
        assert "Faça a troca" in resultado

    def test_remove_atributos_perigosos(self):
        resultado = sanitizar_html('<b onclick="alert(1)">texto</b>')
        assert resultado == "<b>texto</b>"

    def test_remove_img_com_onerror(self):
        resultado = sanitizar_html('<img src=x onerror="alert(1)">dica')
        assert "<img" not in resultado
        assert "dica" in resultado

    def test_link_https_e_mantido(self):
        resultado = sanitizar_html('<a href="https://exemplo.com" onclick="x">site</a>')
        assert resultado == '<a href="https://exemplo.com">site</a>'

    def test_link_javascript_e_descartado(self):
        resultado = sanitizar_html('<a href="javascript:alert(1)">clique</a>')
        assert "javascript" not in resultado
        assert "clique" in resultado

    def test_tags_nao_fechadas_sao_fechadas(self):
        assert sanitizar_html("<b>texto solto") == "<b>texto solto</b>"

    def test_fecha_tags_aninhadas_na_ordem(self):
        assert sanitizar_html("<b><i>texto") == "<b><i>texto</i></b>"

    def test_texto_escapado(self):
        assert "&lt;1&gt;" in sanitizar_html("use <1> litro")

    def test_texto_vazio(self):
        assert sanitizar_html(None) == ""
        assert sanitizar_html("") == ""

    def test_html_malformado_nao_quebra(self):
        assert sanitizar_html("<b><<>>") is not None


class TestTextoSemTags:
    def test_remove_tags(self):
        assert texto_simples("<b>Olá</b> mundo") == "Olá mundo"

    def test_texto_vazio(self):
        assert texto_simples(None) == ""
