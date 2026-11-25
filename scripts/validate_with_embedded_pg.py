"""Valida as migrações e o fluxo de notificações num PostgreSQL embarcado.

Não toca em nenhum banco existente: sobe uma instância temporária em uma pasta
temporária, aplica as migrações do zero, roda a suíte de integração e desliga.

Uso::

    python scripts/validate_with_embedded_pg.py
"""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]


def main() -> int:
    try:
        import pgserver
    except ImportError:
        print("[!] Instale o validador: pip install pgserver")
        return 2

    with tempfile.TemporaryDirectory(prefix="lubribot_pg_") as pasta:
        print(f"[i] subindo PostgreSQL embarcado em {pasta}")
        servidor = pgserver.get_server(pasta)
        try:
            url = servidor.get_uri()
            print("[i] PostgreSQL pronto (url mascarada: postgresql://localhost:<porta>/postgres)")
            ambiente = os.environ.copy()
            ambiente["LUBRIBOT_TEST_DATABASE_URL"] = url
            ambiente["AMBIENTE"] = "QA"
            # Evita que o .env aponte para produção durante o teste.
            ambiente["STRING_CONNECTION_LOCAL"] = url

            print("[i] pytest tests/integration")
            processo = subprocess.run(
                [sys.executable, "-m", "pytest", "tests/integration", "-v", "--no-header"],
                cwd=RAIZ,
                env=ambiente,
            )
            if processo.returncode != 0:
                return processo.returncode

            print("[i] validando scripts/apply_migrations.py contra o banco embarcado")
            apply = subprocess.run(
                [sys.executable, "scripts/apply_migrations.py", "LUBRIBOT_TEST_DATABASE_URL"],
                cwd=RAIZ,
                env=ambiente,
            )
            return apply.returncode
        finally:
            servidor.cleanup()


if __name__ == "__main__":
    raise SystemExit(main())
