"""Ponto de entrada do LubriBot.

Mantido enxuto de propósito: toda a inicialização vive em ``lubribot.app``.
"""

from __future__ import annotations

import sys

from lubribot.app import run

if __name__ == "__main__":
    sys.exit(run())
