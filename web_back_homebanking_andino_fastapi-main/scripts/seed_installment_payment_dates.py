"""Siembra fechas de pago faltantes en cuotas ya amortizadas.

La fuente de verdad para estimar cuotas pagadas es:
  montoaprobadocredito - montosaldocapital

Para no inventar pagos de mas, solo se fechan las primeras cuotas cuyo capital
acumulado esta cubierto por el capital amortizado real.

Uso:
  python scripts/seed_installment_payment_dates.py --dry-run
  python scripts/seed_installment_payment_dates.py --apply
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
    WITH cuotas AS (
        SELECT
            cc.codcuentacredito,
            p.periodomes,
            p.pkcuentacredito,
            p.nrocuota,
            p.fechavencimientopagocuota,
            p.fechapagocuota,
            COALESCE(fa.montoaprobadocredito, 0) - COALESCE(fa.montosaldocapital, 0) AS capital_amortizado,
            SUM(COALESCE(p.montocapitalpagado, p.montocapitalprogramado, p.montocuota, 0))
              OVER (PARTITION BY p.pkcuentacredito ORDER BY p.nrocuota) AS capital_acumulado
        FROM fplanpagomes p
        JOIN dcuentacredito cc ON cc.pkcuentacredito = p.pkcuentacredito
        JOIN fagcuentacredito fa
          ON fa.pkcuentacredito = p.pkcuentacredito
         AND fa.periodomes = 202512
        WHERE COALESCE(fa.montoaprobadocredito, 0) > COALESCE(fa.montosaldocapital, 0)
    )
    SELECT
        codcuentacredito,
        nrocuota,
        fechapagocuota AS fecha_actual,
        fechavencimientopagocuota AS fecha_inventada,
        capital_amortizado,
        capital_acumulado
    FROM cuotas
    WHERE fechapagocuota IS NULL
      AND capital_acumulado <= capital_amortizado + 0.01
    ORDER BY codcuentacredito, nrocuota
    LIMIT :limit
    """
)

COUNT_SQL = text(
    """
    WITH cuotas AS (
        SELECT
            p.fechapagocuota,
            COALESCE(fa.montoaprobadocredito, 0) - COALESCE(fa.montosaldocapital, 0) AS capital_amortizado,
            SUM(COALESCE(p.montocapitalpagado, p.montocapitalprogramado, p.montocuota, 0))
              OVER (PARTITION BY p.pkcuentacredito ORDER BY p.nrocuota) AS capital_acumulado
        FROM fplanpagomes p
        JOIN fagcuentacredito fa
          ON fa.pkcuentacredito = p.pkcuentacredito
         AND fa.periodomes = 202512
        WHERE COALESCE(fa.montoaprobadocredito, 0) > COALESCE(fa.montosaldocapital, 0)
    )
    SELECT COUNT(*)
    FROM cuotas
    WHERE fechapagocuota IS NULL
      AND capital_acumulado <= capital_amortizado + 0.01
    """
)

SUMMARY_SQL = text(
    """
    WITH cuotas AS (
        SELECT
            p.pkcuentacredito,
            COALESCE(fa.montoaprobadocredito, 0) - COALESCE(fa.montosaldocapital, 0) AS capital_amortizado,
            SUM(COALESCE(p.montocapitalpagado, p.montocapitalprogramado, p.montocuota, 0))
              OVER (PARTITION BY p.pkcuentacredito ORDER BY p.nrocuota) AS capital_acumulado,
            p.fechapagocuota
        FROM fplanpagomes p
        JOIN fagcuentacredito fa
          ON fa.pkcuentacredito = p.pkcuentacredito
         AND fa.periodomes = 202512
        WHERE COALESCE(fa.montoaprobadocredito, 0) > COALESCE(fa.montosaldocapital, 0)
    )
    SELECT
        COUNT(DISTINCT pkcuentacredito) FILTER (
            WHERE fechapagocuota IS NULL
              AND capital_acumulado <= capital_amortizado + 0.01
        ) AS creditos_afectados,
        COUNT(*) FILTER (
            WHERE fechapagocuota IS NULL
              AND capital_acumulado <= capital_amortizado + 0.01
        ) AS cuotas_a_fechar
    FROM cuotas
    """
)

UPDATE_SQL = text(
    """
    WITH cuotas AS (
        SELECT
            p.periodomes,
            p.pkcuentacredito,
            p.nrocuota,
            COALESCE(
              p.fechavencimientopagocuota,
              (fa.fechadesembolsocredito + (p.nrocuota || ' month')::interval)::date
            ) AS fecha_inventada,
            p.fechapagocuota,
            COALESCE(fa.montoaprobadocredito, 0) - COALESCE(fa.montosaldocapital, 0) AS capital_amortizado,
            SUM(COALESCE(p.montocapitalpagado, p.montocapitalprogramado, p.montocuota, 0))
              OVER (PARTITION BY p.pkcuentacredito ORDER BY p.nrocuota) AS capital_acumulado
        FROM fplanpagomes p
        JOIN fagcuentacredito fa
          ON fa.pkcuentacredito = p.pkcuentacredito
         AND fa.periodomes = 202512
        WHERE COALESCE(fa.montoaprobadocredito, 0) > COALESCE(fa.montosaldocapital, 0)
    )
    UPDATE fplanpagomes p
    SET fechapagocuota = cuotas.fecha_inventada,
        fecultactualizacion = NOW()
    FROM cuotas
    WHERE p.periodomes = cuotas.periodomes
      AND p.pkcuentacredito = cuotas.pkcuentacredito
      AND p.nrocuota = cuotas.nrocuota
      AND cuotas.fechapagocuota IS NULL
      AND cuotas.capital_acumulado <= cuotas.capital_amortizado + 0.01
    """
)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()
    if not args.apply and not args.dry_run:
        args.dry_run = True

    with engine.begin() as conn:
        summary = conn.execute(SUMMARY_SQL).mappings().one()
        count = conn.execute(COUNT_SQL).scalar_one()
        print(f"creditos_afectados={summary['creditos_afectados']}")
        print(f"cuotas_a_fechar={count}")
        for row in conn.execute(PREVIEW_SQL, {"limit": args.limit}).mappings():
            print(dict(row))
        if args.apply:
            result = conn.execute(UPDATE_SQL)
            print(f"cuotas_fechadas={result.rowcount}")
        else:
            print("modo=dry-run")


if __name__ == "__main__":
    main()
