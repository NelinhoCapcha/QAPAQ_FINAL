"""Completa cronogramas cortos creando cuotas pagadas anteriores.

Caso objetivo:
  Si FAG dice 35 cuotas y fplanpagomes solo tiene 12 filas, las 12 filas
  actuales representan las cuotas pendientes. Se desplazan al final (24-35)
  y se crean 23 cuotas anteriores pagadas con fechas inventadas.

Uso:
  python scripts/expand_credit_schedules.py --dry-run
  python scripts/expand_credit_schedules.py --apply
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.cfg_database import engine


SUMMARY_SQL = text(
    """
    SELECT
        cc.codcuentacredito,
        fa.pkcuentacredito,
        fa.nrocuotas AS total_cuotas,
        COUNT(p.*) AS filas_actuales,
        fa.montoaprobadocredito,
        fa.montosaldocapital,
        MIN(p.fechavencimientopagocuota) AS primera_fecha_actual
    FROM fagcuentacredito fa
    JOIN dcuentacredito cc ON cc.pkcuentacredito = fa.pkcuentacredito
    JOIN fplanpagomes p ON p.pkcuentacredito = fa.pkcuentacredito
    WHERE fa.periodomes = 202512
      AND fa.nrocuotas IS NOT NULL
    GROUP BY cc.codcuentacredito, fa.pkcuentacredito, fa.nrocuotas,
             fa.montoaprobadocredito, fa.montosaldocapital
    HAVING COUNT(p.*) < fa.nrocuotas
    ORDER BY cc.codcuentacredito
    LIMIT :limit
    """
)

COUNT_SQL = text(
    """
    SELECT COUNT(*)
    FROM (
        SELECT fa.pkcuentacredito
        FROM fagcuentacredito fa
        JOIN fplanpagomes p ON p.pkcuentacredito = fa.pkcuentacredito
        WHERE fa.periodomes = 202512
          AND fa.nrocuotas IS NOT NULL
        GROUP BY fa.pkcuentacredito, fa.nrocuotas
        HAVING COUNT(p.*) < fa.nrocuotas
    ) x
    """
)

UPDATE_SHIFT_SQL = text(
    """
    WITH base AS (
      SELECT
        fa.pkcuentacredito,
        fa.nrocuotas::int AS total_cuotas,
        COUNT(p.*)::int AS filas_actuales,
        (fa.nrocuotas - COUNT(p.*))::int AS faltantes
      FROM fagcuentacredito fa
      JOIN fplanpagomes p ON p.pkcuentacredito = fa.pkcuentacredito
      WHERE fa.periodomes = 202512
        AND fa.nrocuotas IS NOT NULL
      GROUP BY fa.pkcuentacredito, fa.nrocuotas
      HAVING COUNT(p.*) < fa.nrocuotas
    )
    UPDATE fplanpagomes p
    SET nrocuota = p.nrocuota + base.faltantes,
        fechapagocuota = NULL,
        fecultactualizacion = NOW()
    FROM base
    WHERE p.pkcuentacredito = base.pkcuentacredito
      AND p.periodomes = 202512
    """
)

INSERT_MISSING_SQL = text(
    """
    WITH base AS (
      SELECT
        fa.pkcuentacredito,
        fa.nrocuotas::int AS total_cuotas,
        COUNT(p.*)::int AS filas_actuales,
        (fa.nrocuotas - COUNT(p.*))::int AS faltantes,
        fa.montoaprobadocredito,
        fa.montosaldocapital,
        (COALESCE(fa.montoaprobadocredito, 0) - COALESCE(fa.montosaldocapital, 0)) AS capital_amortizado,
        MIN(p.fechavencimientopagocuota) AS primera_fecha_actual
      FROM fagcuentacredito fa
      JOIN fplanpagomes p ON p.pkcuentacredito = fa.pkcuentacredito
      WHERE fa.periodomes = 202512
        AND fa.nrocuotas IS NOT NULL
      GROUP BY fa.pkcuentacredito, fa.nrocuotas, fa.montoaprobadocredito, fa.montosaldocapital
      HAVING COUNT(p.*) < fa.nrocuotas
    ),
    plantilla AS (
      SELECT DISTINCT ON (p.pkcuentacredito) p.*
      FROM fplanpagomes p
      JOIN base b ON b.pkcuentacredito = p.pkcuentacredito
      WHERE p.periodomes = 202512
      ORDER BY p.pkcuentacredito, p.nrocuota
    ),
    nuevas AS (
      SELECT
        b.*,
        t.codplanpago, t.pksolicitud, t.pkestadocredito, t.pkproducto, t.pkmoneda,
        t.pkmodalidad, t.pkgrupocredito, t.pkactividadeconomica,
        t.pktipotasacompensatoria, t.pktipotasamoratoria, t.pkcliente,
        t.pkcondicioncontable, t.pkcalificacioncrediticiainterna, t.pkagencia,
        t.pkjeferegional, t.pkadministrador, t.pkasesor, t.pkasesornivel,
        t.pkestadodesembolso, t.pkmodalidadpago, t.codestadocuota, t.codestadoplan,
        t.montocuota, t.montomora, t.montocuotavencida, t.montocuotaatrasada,
        t.montomoraprogramado, t.montomorapagada, t.montogasto,
        t.montogastoprogramado, t.montogastopagado, t.montocapitaldesembolsado,
        t.diasatrasocuota, t.diasvencidocuota, t.montopagoanticipado, t.montopagoparcial,
        gs.n AS nrocuota,
        (b.primera_fecha_actual - ((b.faltantes - gs.n + 1) || ' month')::interval)::date AS fecha_cuota,
        ROUND(
          CASE
            WHEN gs.n = b.faltantes THEN b.capital_amortizado - ROUND((b.capital_amortizado / b.faltantes) * (b.faltantes - 1), 2)
            ELSE b.capital_amortizado / b.faltantes
          END::numeric,
          2
        ) AS capital_cuota,
        ROUND((b.montoaprobadocredito - ((b.capital_amortizado / b.faltantes) * gs.n))::numeric, 2) AS saldo_despues
      FROM base b
      JOIN plantilla t ON t.pkcuentacredito = b.pkcuentacredito
      CROSS JOIN LATERAL generate_series(1, b.faltantes) AS gs(n)
    )
    INSERT INTO fplanpagomes (
      periodomes, pkcuentacredito, codplanpago, nrocuota, pksolicitud,
      pkestadocredito, pkproducto, pkmoneda, pkmodalidad, pkgrupocredito,
      pkactividadeconomica, pktipotasacompensatoria, pktipotasamoratoria,
      pkcliente, pkcondicioncontable, pkcalificacioncrediticiainterna,
      pkagencia, pkjeferegional, pkadministrador, pkasesor, pkasesornivel,
      pkestadodesembolso, pkmodalidadpago, codestadocuota, codestadoplan,
      fechavencimientopagocuota, fechapagocuota, montocuota, montosaldo,
      montomora, montocuotavencida, montocuotaatrasada, montointeresprogramado,
      montointerespagado, montointeresalafecha, montomoraprogramado,
      montomorapagada, montogasto, montogastoprogramado, montogastopagado,
      montosaldocapital, montocapitalpagado, montocapitalprogramado,
      montocapitaldesembolsado, diasatrasocuota, diasvencidocuota,
      interesdevengadocuota, montopagoanticipado, montopagoparcial,
      fecultactualizacion
    )
    SELECT
      202512, pkcuentacredito, codplanpago, nrocuota, pksolicitud,
      pkestadocredito, pkproducto, pkmoneda, pkmodalidad, pkgrupocredito,
      pkactividadeconomica, pktipotasacompensatoria, pktipotasamoratoria,
      pkcliente, pkcondicioncontable, pkcalificacioncrediticiainterna,
      pkagencia, pkjeferegional, pkadministrador, pkasesor, pkasesornivel,
      pkestadodesembolso, pkmodalidadpago, codestadocuota, codestadoplan,
      fecha_cuota, fecha_cuota, capital_cuota, saldo_despues,
      0, 0, 0, 0,
      0, 0, 0,
      0, 0, 0, 0,
      saldo_despues, capital_cuota, capital_cuota,
      montocapitaldesembolsado, 0, 0,
      0, 0, 0,
      NOW()
    FROM nuevas
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
        count = conn.execute(COUNT_SQL).scalar_one()
        print(f"creditos_con_cronograma_incompleto={count}")
        for row in conn.execute(SUMMARY_SQL, {"limit": args.limit}).mappings():
            print(dict(row))
        if args.apply:
            shifted = conn.execute(UPDATE_SHIFT_SQL)
            inserted = conn.execute(INSERT_MISSING_SQL)
            print(f"filas_desplazadas={shifted.rowcount}")
            print(f"filas_insertadas={inserted.rowcount}")
        else:
            print("modo=dry-run")


if __name__ == "__main__":
    main()
