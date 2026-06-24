from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.cfg_database import engine


DETAIL_SQL = text(
    """
    SELECT
        p.nrocuota,
        p.fechavencimientopagocuota,
        p.fechapagocuota,
        p.montocapitalprogramado,
        p.montointeresprogramado,
        p.montocuota,
        p.montosaldo
    FROM fplanpagomes p
    JOIN dcuentacredito c ON c.pkcuentacredito = p.pkcuentacredito
    WHERE c.codcuentacredito = :codigo
      AND p.periodomes = 202512
    ORDER BY p.nrocuota
    """
)

SUMMARY_SQL = text(
    """
    SELECT
        COUNT(*) AS total,
        COUNT(*) FILTER (WHERE p.fechapagocuota IS NOT NULL) AS pagadas,
        COUNT(*) FILTER (WHERE p.fechapagocuota IS NULL) AS pendientes,
        MIN(p.nrocuota) FILTER (WHERE p.fechapagocuota IS NULL) AS proxima_pendiente
    FROM fplanpagomes p
    JOIN dcuentacredito c ON c.pkcuentacredito = p.pkcuentacredito
    WHERE c.codcuentacredito = :codigo
      AND p.periodomes = 202512
    """
)


def main() -> None:
    codigo = sys.argv[1] if len(sys.argv) > 1 else "CRED0000006"
    with engine.connect() as conn:
        rows = conn.execute(DETAIL_SQL, {"codigo": codigo}).fetchall()
        summary = conn.execute(SUMMARY_SQL, {"codigo": codigo}).mappings().one()

    print(dict(summary))
    print("primeras_5:")
    for row in rows[:5]:
        print(row)
    print("cuotas_22_a_25:")
    for row in rows[21:25]:
        print(row)
    print("ultimas_3:")
    for row in rows[-3:]:
        print(row)


if __name__ == "__main__":
    main()
