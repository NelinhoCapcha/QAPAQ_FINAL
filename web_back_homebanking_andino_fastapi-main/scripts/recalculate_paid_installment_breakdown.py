"""Recalcula interes y cuota de las cuotas historicas pagadas.

Las cuotas historicas creadas para completar cronogramas no deben mostrarse
como solo capital. Este script mantiene intacto el saldo de capital, pero
calcula el interes compensatorio por dias usando la TEA del credito.
"""
from __future__ import annotations

import sys
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.cfg_database import engine


UPDATE_SQL = text(
    """
    WITH base AS (
      SELECT
        p.periodomes,
        p.pkcuentacredito,
        p.nrocuota,
        COALESCE(p.montocapitalprogramado, p.montocapitalpagado, 0)::numeric AS capital,
        (COALESCE(p.montosaldo, 0) + COALESCE(p.montocapitalprogramado, p.montocapitalpagado, 0))::numeric AS saldo_antes,
        COALESCE(fa.montoaprobadocredito, 0)::numeric AS monto_aprobado,
        CASE
          WHEN COALESCE(fa.tasainterescompensatoria, 0) > 1
            THEN COALESCE(fa.tasainterescompensatoria, 0)::numeric / 100
          ELSE COALESCE(fa.tasainterescompensatoria, 0)::numeric
        END AS tea,
        GREATEST(
          1,
          COALESCE(
            p.fechavencimientopagocuota
              - LAG(p.fechavencimientopagocuota) OVER (
                  PARTITION BY p.pkcuentacredito
                  ORDER BY p.nrocuota
                ),
            30
          )
        )::numeric AS dias
      FROM fplanpagomes p
      JOIN fagcuentacredito fa
        ON fa.pkcuentacredito = p.pkcuentacredito
       AND fa.periodomes = p.periodomes
      WHERE p.periodomes = 202512
        AND p.fechapagocuota IS NOT NULL
    ),
    calc AS (
      SELECT
        periodomes,
        pkcuentacredito,
        nrocuota,
        capital,
        ROUND((saldo_antes * (POWER((1 + tea)::double precision, (dias / 360)::double precision) - 1))::numeric, 2) AS interes,
        ROUND((monto_aprobado * 0.0008)::numeric, 2) AS seguro
      FROM base
    )
    UPDATE fplanpagomes p
    SET montointeresprogramado = calc.interes,
        montointerespagado = calc.interes,
        montointeresalafecha = calc.interes,
        montocuota = ROUND((calc.capital + calc.interes + calc.seguro)::numeric, 2),
        fecultactualizacion = NOW()
    FROM calc
    WHERE p.periodomes = calc.periodomes
      AND p.pkcuentacredito = calc.pkcuentacredito
      AND p.nrocuota = calc.nrocuota
    """
)

CHECK_SQL = text(
    """
    SELECT
        c.codcuentacredito,
        p.nrocuota,
        p.fechavencimientopagocuota,
        p.fechapagocuota,
        p.montocapitalprogramado,
        p.montointeresprogramado,
        ROUND((fa.montoaprobadocredito * 0.0008)::numeric, 2) AS seguro_ref,
        p.montocuota
    FROM fplanpagomes p
    JOIN dcuentacredito c ON c.pkcuentacredito = p.pkcuentacredito
    JOIN fagcuentacredito fa
      ON fa.pkcuentacredito = p.pkcuentacredito
     AND fa.periodomes = p.periodomes
    WHERE c.codcuentacredito = :codigo
      AND p.periodomes = 202512
    ORDER BY p.nrocuota
    LIMIT 6
    """
)


def main() -> None:
    codigo = sys.argv[1] if len(sys.argv) > 1 else "CRED0000006"
    with engine.begin() as conn:
        result = conn.execute(UPDATE_SQL)
        print(f"filas_actualizadas={result.rowcount}")
        for row in conn.execute(CHECK_SQL, {"codigo": codigo}).mappings():
            print(dict(row))


if __name__ == "__main__":
    main()
