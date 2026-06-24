"""Corrige fplanpagomes.montosaldo para que sea saldo capital posterior a la cuota.

Uso:
  python scripts/repair_credit_schedule_balance.py --dry-run
  python scripts/repair_credit_schedule_balance.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.cfg_database import engine


PREVIEW_SQL = text(
    """
    WITH calc AS (
        SELECT
            cc.codcuentacredito,
            p.periodomes,
            p.pkcuentacredito,
            p.nrocuota,
            p.montosaldo,
            GREATEST(
                fa.montosaldocapital
                - SUM(COALESCE(p.montocapitalprogramado, p.montocuota, 0))
                  OVER (PARTITION BY p.pkcuentacredito ORDER BY p.nrocuota),
                0
            ) AS saldo_correcto
        FROM fplanpagomes p
        JOIN dcuentacredito cc ON cc.pkcuentacredito = p.pkcuentacredito
        JOIN fagcuentacredito fa
          ON fa.pkcuentacredito = p.pkcuentacredito
         AND fa.periodomes = 202512
        WHERE p.fechapagocuota IS NULL
    )
    SELECT codcuentacredito, nrocuota, montosaldo, saldo_correcto
    FROM calc
    WHERE ROUND(COALESCE(montosaldo, 0)::numeric, 2) <> ROUND(saldo_correcto::numeric, 2)
    ORDER BY codcuentacredito, nrocuota
    LIMIT :limit
    """
)

COUNT_SQL = text(
    """
    WITH calc AS (
        SELECT
            p.periodomes,
            p.pkcuentacredito,
            p.nrocuota,
            p.montosaldo,
            GREATEST(
                fa.montosaldocapital
                - SUM(COALESCE(p.montocapitalprogramado, p.montocuota, 0))
                  OVER (PARTITION BY p.pkcuentacredito ORDER BY p.nrocuota),
                0
            ) AS saldo_correcto
        FROM fplanpagomes p
        JOIN fagcuentacredito fa
          ON fa.pkcuentacredito = p.pkcuentacredito
         AND fa.periodomes = 202512
        WHERE p.fechapagocuota IS NULL
    )
    SELECT COUNT(*)
    FROM calc
    WHERE ROUND(COALESCE(montosaldo, 0)::numeric, 2) <> ROUND(saldo_correcto::numeric, 2)
    """
)

UPDATE_SQL = text(
    """
    WITH calc AS (
        SELECT
            p.periodomes,
            p.pkcuentacredito,
            p.nrocuota,
            GREATEST(
                fa.montosaldocapital
                - SUM(COALESCE(p.montocapitalprogramado, p.montocuota, 0))
                  OVER (PARTITION BY p.pkcuentacredito ORDER BY p.nrocuota),
                0
            ) AS saldo_correcto
        FROM fplanpagomes p
        JOIN fagcuentacredito fa
          ON fa.pkcuentacredito = p.pkcuentacredito
         AND fa.periodomes = 202512
        WHERE p.fechapagocuota IS NULL
    )
    UPDATE fplanpagomes p
    SET montosaldo = ROUND(calc.saldo_correcto::numeric, 2),
        fecultactualizacion = NOW()
    FROM calc
    WHERE p.periodomes = calc.periodomes
      AND p.pkcuentacredito = calc.pkcuentacredito
      AND p.nrocuota = calc.nrocuota
      AND ROUND(COALESCE(p.montosaldo, 0)::numeric, 2) <> ROUND(calc.saldo_correcto::numeric, 2)
    """
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Ejecuta la correccion en BD")
    parser.add_argument("--dry-run", action="store_true", help="Solo muestra el impacto")
    parser.add_argument("--limit", type=int, default=8)
    args = parser.parse_args()

    if not args.apply and not args.dry_run:
        args.dry_run = True

    with engine.begin() as conn:
        count = conn.execute(COUNT_SQL).scalar_one()
        print(f"filas_desalineadas={count}")
        for row in conn.execute(PREVIEW_SQL, {"limit": args.limit}).mappings():
            print(dict(row))
        if args.apply:
            result = conn.execute(UPDATE_SQL)
            print(f"filas_actualizadas={result.rowcount}")
        else:
            print("modo=dry-run")


if __name__ == "__main__":
    main()
