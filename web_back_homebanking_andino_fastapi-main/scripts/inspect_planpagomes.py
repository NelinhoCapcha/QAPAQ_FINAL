from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.cfg_database import engine


with engine.connect() as conn:
    print("columns")
    for row in conn.execute(
        text(
            """
            SELECT column_name, data_type, is_nullable, column_default
            FROM information_schema.columns
            WHERE table_name = 'fplanpagomes'
            ORDER BY ordinal_position
            """
        )
    ):
        print(row)

    print("constraints")
    for row in conn.execute(
        text(
            """
            SELECT conname, pg_get_constraintdef(oid)
            FROM pg_constraint
            WHERE conrelid = 'fplanpagomes'::regclass
            ORDER BY contype DESC, conname
            """
        )
    ):
        print(row)

    print("sample")
    for row in conn.execute(
        text(
            """
            SELECT *
            FROM fplanpagomes
            WHERE pkcuentacredito = (
                SELECT pkcuentacredito
                FROM dcuentacredito
                WHERE codcuentacredito = 'CRED0000006'
            )
            ORDER BY nrocuota
            LIMIT 2
            """
        )
    ).mappings():
        print(dict(row))
