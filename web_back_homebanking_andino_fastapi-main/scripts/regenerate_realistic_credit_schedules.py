"""Regenera cronogramas de credito con una amortizacion coherente.

Mantiene:
- cantidad total de cuotas
- fechas existentes
- cuotas pagadas vs pendientes segun fechapagocuota

Recalcula:
- capital de cada cuota
- interes compensatorio por saldo y dias
- monto de cuota con seguro de desgravamen
- saldo capital despues de cada cuota
- saldos agregados en fagcuentacredito
"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.core.cfg_database import engine

getcontext().prec = 28

PERIODO = 202512
MONEY = Decimal("0.01")
YEAR_DAYS = Decimal("360")
INSURANCE_RATE = Decimal("0.0008")


def money(value: Decimal | int | str | float) -> Decimal:
    return Decimal(str(value or 0)).quantize(MONEY, rounding=ROUND_HALF_UP)


def rate(value: Decimal | int | str | float) -> Decimal:
    raw = Decimal(str(value or 0))
    return raw / Decimal("100") if raw > 1 else raw


def interest(balance: Decimal, tea: Decimal, days: int) -> Decimal:
    if balance <= 0 or days <= 0:
        return money(0)
    factor = (Decimal(1) + tea) ** (Decimal(days) / YEAR_DAYS)
    return money(balance * (factor - Decimal(1)))


def final_balance_for_payment(principal: Decimal, tea: Decimal, days_by_row: list[int], payment: Decimal) -> Decimal:
    balance = principal
    for days in days_by_row:
        cuota_interest = interest(balance, tea, days)
        capital = payment - cuota_interest
        if capital <= 0:
            return principal * Decimal("999")
        balance = money(balance - capital)
    return balance


def solved_payment(principal: Decimal, tea: Decimal, days_by_row: list[int]) -> Decimal:
    if principal <= 0 or not days_by_row:
        return money(0)
    low = Decimal("0")
    high = principal
    while final_balance_for_payment(principal, tea, days_by_row, high) > 0:
        high *= Decimal("2")
    for _ in range(80):
        mid = (low + high) / Decimal("2")
        if final_balance_for_payment(principal, tea, days_by_row, mid) > 0:
            low = mid
        else:
            high = mid
    return money(high)


CREDITS_SQL = text(
    """
    SELECT
        cc.codcuentacredito,
        fa.pkcuentacredito,
        fa.nrocuotas,
        fa.montoaprobadocredito,
        fa.tasainterescompensatoria
    FROM fagcuentacredito fa
    JOIN dcuentacredito cc ON cc.pkcuentacredito = fa.pkcuentacredito
    WHERE fa.periodomes = :periodo
      AND COALESCE(fa.nrocuotas, 0) > 0
      AND COALESCE(fa.montoaprobadocredito, 0) > 0
      AND EXISTS (
        SELECT 1
        FROM fplanpagomes p
        WHERE p.periodomes = fa.periodomes
          AND p.pkcuentacredito = fa.pkcuentacredito
      )
    ORDER BY cc.codcuentacredito
    """
)

ROWS_SQL = text(
    """
    SELECT nrocuota, fechavencimientopagocuota, fechapagocuota
    FROM fplanpagomes
    WHERE periodomes = :periodo
      AND pkcuentacredito = :pk
    ORDER BY nrocuota
    """
)

UPDATE_ROW_SQL = text(
    """
    UPDATE fplanpagomes
    SET montocuota = :montocuota,
        montosaldo = :saldo_despues,
        montointeresprogramado = :interes,
        montointerespagado = CASE WHEN fechapagocuota IS NOT NULL THEN :interes ELSE 0 END,
        montointeresalafecha = :interes,
        montomora = 0,
        montomoraprogramado = 0,
        montomorapagada = 0,
        montogasto = 0,
        montogastoprogramado = 0,
        montogastopagado = 0,
        montocuotavencida = CASE WHEN fechapagocuota IS NULL AND :dias_atraso > 0 THEN :montocuota ELSE 0 END,
        montocuotaatrasada = CASE WHEN fechapagocuota IS NULL AND :dias_atraso > 0 THEN :montocuota ELSE 0 END,
        montosaldocapital = :saldo_despues,
        montocapitalprogramado = :capital,
        montocapitalpagado = CASE WHEN fechapagocuota IS NOT NULL THEN :capital ELSE 0 END,
        diasatrasocuota = :dias_atraso,
        diasvencidocuota = :dias_atraso,
        interesdevengadocuota = :interes,
        fecultactualizacion = NOW()
    WHERE periodomes = :periodo
      AND pkcuentacredito = :pk
      AND nrocuota = :nrocuota
    """
)

UPDATE_CREDIT_SQL = text(
    """
    UPDATE fagcuentacredito
    SET montosaldocapital = :saldo_capital,
        montosaldointeres = :saldo_interes,
        montosaldomoratorio = 0,
        montosaldogasto = 0,
        montosaldocliente = :saldo_cliente,
        montosaldovencido = :saldo_vencido,
        diasatrasocredito = :dias_atraso,
        fecultactualizacion = NOW()
    WHERE periodomes = :periodo
      AND pkcuentacredito = :pk
    """
)


def regenerate_credit(conn, credit: dict, today: date) -> dict:
    rows = [dict(r) for r in conn.execute(ROWS_SQL, {"periodo": PERIODO, "pk": credit["pkcuentacredito"]}).mappings()]
    if not rows:
        return {"updated": 0}

    principal = money(credit["montoaprobadocredito"])
    tea = rate(credit["tasainterescompensatoria"])
    total_months = int(credit["nrocuotas"] or len(rows))
    days_by_row = []
    previous_due_for_days = None
    for row in rows:
        due = row["fechavencimientopagocuota"]
        days = 30 if previous_due_for_days is None or due is None else max(1, (due - previous_due_for_days).days)
        days_by_row.append(days)
        previous_due_for_days = due
    scheduled_payment = solved_payment(principal, tea, days_by_row)
    insurance = money(principal * INSURANCE_RATE)
    balance = principal
    previous_due = None
    paid_count = 0
    pending_balance_before = Decimal("0")
    next_pending_interest = Decimal("0")
    overdue_total = Decimal("0")
    max_overdue_days = 0

    calculated = []
    for index, row in enumerate(rows, start=1):
        due = row["fechavencimientopagocuota"]
        days = 30 if previous_due is None or due is None else max(1, (due - previous_due).days)
        cuota_interest = interest(balance, tea, days)
        if index == len(rows):
            capital = balance
        else:
            capital = money(scheduled_payment - cuota_interest)
            if capital <= 0:
                capital = money(principal / Decimal(total_months))
            if capital > balance:
                capital = balance
        saldo_despues = money(balance - capital)
        installment = money(capital + cuota_interest + insurance)
        is_paid = row["fechapagocuota"] is not None
        overdue_days = 0 if is_paid or due is None or due >= today else (today - due).days

        if is_paid:
            paid_count += 1
        elif pending_balance_before == 0:
            pending_balance_before = balance
            next_pending_interest = cuota_interest

        if not is_paid and overdue_days > 0:
            overdue_total += installment
            max_overdue_days = max(max_overdue_days, overdue_days)

        calculated.append(
            {
                "periodo": PERIODO,
                "pk": credit["pkcuentacredito"],
                "nrocuota": row["nrocuota"],
                "montocuota": installment,
                "saldo_despues": saldo_despues,
                "interes": cuota_interest,
                "capital": capital,
                "dias_atraso": overdue_days,
            }
        )
        balance = saldo_despues
        previous_due = due

    if pending_balance_before == 0:
        pending_balance_before = Decimal("0")
        next_pending_interest = Decimal("0")

    for item in calculated:
        conn.execute(UPDATE_ROW_SQL, item)

    saldo_cliente = money(pending_balance_before + next_pending_interest)
    conn.execute(
        UPDATE_CREDIT_SQL,
        {
            "periodo": PERIODO,
            "pk": credit["pkcuentacredito"],
            "saldo_capital": money(pending_balance_before),
            "saldo_interes": money(next_pending_interest),
            "saldo_cliente": saldo_cliente,
            "saldo_vencido": money(overdue_total),
            "dias_atraso": max_overdue_days,
        },
    )
    return {
        "updated": len(calculated),
        "paid": paid_count,
        "pending": len(calculated) - paid_count,
        "saldo_capital": money(pending_balance_before),
        "next_interest": money(next_pending_interest),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--codigo", default=None)
    args = parser.parse_args()

    today = date(2026, 6, 16)
    total_credits = 0
    total_rows = 0
    examples = []
    with engine.begin() as conn:
        credits = [dict(r) for r in conn.execute(CREDITS_SQL, {"periodo": PERIODO}).mappings()]
        if args.codigo:
            credits = [c for c in credits if c["codcuentacredito"] == args.codigo]
        for credit in credits:
            if args.apply:
                result = regenerate_credit(conn, credit, today)
            else:
                rows = conn.execute(ROWS_SQL, {"periodo": PERIODO, "pk": credit["pkcuentacredito"]}).fetchall()
                result = {"updated": len(rows), "paid": sum(1 for r in rows if r.fechapagocuota is not None)}
            total_credits += 1
            total_rows += result["updated"]
            if len(examples) < 8:
                examples.append({**{"codigo": credit["codcuentacredito"]}, **result})

    print(f"modo={'apply' if args.apply else 'dry-run'}")
    print(f"creditos={total_credits}")
    print(f"filas_cronograma={total_rows}")
    for item in examples:
        print(item)


if __name__ == "__main__":
    main()
