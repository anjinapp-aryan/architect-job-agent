"""Thin Alembic wrapper so ops can run ``python -m scripts.migrate upgrade``.

Usage:
    python scripts/migrate.py upgrade head
    python scripts/migrate.py downgrade -1
    python scripts/migrate.py revision --autogenerate -m "add x"
    python scripts/migrate.py current
    python scripts/migrate.py history
"""
from __future__ import annotations

import sys
from pathlib import Path

from alembic.config import CommandLine

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    cli = CommandLine(prog="aja-migrate")
    sys.exit(cli.main(argv=["-c", str(ROOT / "alembic.ini"), *sys.argv[1:]]))


if __name__ == "__main__":
    main()
