"""Configuração compartilhada dos testes.

Os testes de domínio/notificação não tocam banco nem Telegram: usam dublês que
implementam as portas. Testes de integração com Postgres ficam marcados com
``@pytest.mark.integration`` e são pulados quando não há ``LUBRIBOT_TEST_DATABASE_URL``.
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
