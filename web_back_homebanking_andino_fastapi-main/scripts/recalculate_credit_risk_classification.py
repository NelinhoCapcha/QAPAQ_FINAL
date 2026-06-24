"""Recalcula la calificacion crediticia segun dias de atraso.

Regla usada:
- 0 a 8 dias: Normal
- 9 a 30 dias: CPP
- 31 a 60 dias: Deficiente
- 61 a 120 dias: Dudoso
- 121+ dias: Perdida

Actualiza FAGCUENTACREDITO y FPLANPAGOMES para que Core y HomeBanking lean
la misma clasificacion desde la BD.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.cfg_database import engine

PERIODO = 202512


SUMMARY_BEFORE_SQL = text(
    """
    SELECT
      cal.descalificacioncrediticia AS calificacion_actual,
      CASE
        WHEN COALESCE(f.diasatrasocredito, 0) <= 8 THEN 'Normal'
        WHEN COALESCE(f.diasatrasocredito, 0) <= 30 THEN 'Con Problemas Potenciales (CPP)'
        WHEN COALESCE(f.diasatrasocredito, 0) <= 60 THEN 'Deficiente'
        WHEN COALESCE(f.diasatrasocredito, 0) <= 120 THEN 'Dudoso'
        ELSE 'Pérdida'
      END AS calificacion_calculada,
      COUNT(*) AS creditos
    FROM fagcuentacredito f
    LEFT JOIN dcalificacioncrediticia cal
      ON cal.pkcalificacioncrediticia = f.pkcalificacioncrediticiainterna
    WHERE f.periodomes = :periodo
    GROUP BY calificacion_actual, calificacion_calculada
    ORDER BY calificacion_actual, calificacion_calculada
    """
)

UPDATE_FAG_SQL = text(
    """
    WITH target AS (
      SELECT
        f.pkcuentacredito,
        CASE
          WHEN COALESCE(f.diasatrasocredito, 0) <= 8 THEN '0'
          WHEN COALESCE(f.diasatrasocredito, 0) <= 30 THEN '1'
          WHEN COALESCE(f.diasatrasocredito, 0) <= 60 THEN '2'
          WHEN COALESCE(f.diasatrasocredito, 0) <= 120 THEN '3'
          ELSE '4'
        END AS cod_calificacion
      FROM fagcuentacredito f
      WHERE f.periodomes = :periodo
    )
    UPDATE fagcuentacredito f
    SET pkcalificacioncrediticiainterna = cal.pkcalificacioncrediticia,
        fecultactualizacion = NOW()
    FROM target t
    JOIN dcalificacioncrediticia cal
      ON TRIM(cal.codcalificacioncrediticia) = t.cod_calificacion
    WHERE f.periodomes = :periodo
      AND f.pkcuentacredito = t.pkcuentacredito
    """
)

UPDATE_PLAN_SQL = text(
    """
    UPDATE fplanpagomes p
    SET pkcalificacioncrediticiainterna = f.pkcalificacioncrediticiainterna,
        fecultactualizacion = NOW()
    FROM fagcuentacredito f
    WHERE p.periodomes = f.periodomes
      AND p.pkcuentacredito = f.pkcuentacredito
      AND p.periodomes = :periodo
    """
)

CHECK_CREDIT_SQL = text(
    """
    SELECT
      cc.codcuentacredito,
      f.diasatrasocredito,
      TRIM(cal.codcalificacioncrediticia) AS cod_calificacion,
      cal.descalificacioncrediticia AS calificacion
    FROM fagcuentacredito f
    JOIN dcuentacredito cc ON cc.pkcuentacredito = f.pkcuentacredito
    LEFT JOIN dcalificacioncrediticia cal
      ON cal.pkcalificacioncrediticia = f.pkcalificacioncrediticiainterna
    WHERE f.periodomes = :periodo
      AND (:codigo IS NULL OR cc.codcuentacredito = :codigo)
    ORDER BY cc.codcuentacredito
    LIMIT :limit
    """
)

SUMMARY_AFTER_SQL = text(
    """
    SELECT
      TRIM(cal.codcalificacioncrediticia) AS cod,
      cal.descalificacioncrediticia AS calificacion,
      COUNT(*) AS creditos
    FROM fagcuentacredito f
    JOIN dcalificacioncrediticia cal
      ON cal.pkcalificacioncrediticia = f.pkcalificacioncrediticiainterna
    WHERE f.periodomes = :periodo
    GROUP BY cod, calificacion
    ORDER BY CAST(TRIM(cal.codcalificacioncrediticia) AS INTEGER)
    """
)


def print_rows(label: str, rows) -> None:
    print(label)
    for row in rows:
        print(dict(row))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--codigo", default="CRED0000006")
    parser.add_argument("--limit", type=int, default=10)
    args = parser.parse_args()

    with engine.begin() as conn:
        print_rows(
            "resumen_antes",
            conn.execute(SUMMARY_BEFORE_SQL, {"periodo": PERIODO}).mappings(),
        )
        if args.apply:
            fag = conn.execute(UPDATE_FAG_SQL, {"periodo": PERIODO})
            plan = conn.execute(UPDATE_PLAN_SQL, {"periodo": PERIODO})
            print(f"creditos_actualizados={fag.rowcount}")
            print(f"cuotas_actualizadas={plan.rowcount}")
        else:
            print("modo=dry-run")
        print_rows(
            "verificacion_credito",
            conn.execute(
                CHECK_CREDIT_SQL,
                {"periodo": PERIODO, "codigo": args.codigo, "limit": args.limit},
            ).mappings(),
        )
        print_rows(
            "resumen_despues",
            conn.execute(SUMMARY_AFTER_SQL, {"periodo": PERIODO}).mappings(),
        )


if __name__ == "__main__":
    main()
