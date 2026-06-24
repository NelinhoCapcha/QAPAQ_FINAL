"""Consultas SQL de cuentas: ahorro, crédito, movimientos y cronograma."""
from datetime import date
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.services.financial import ITFEngine, InstallmentService
from app.services.financial.engines import money

# Periodo de la cartera de créditos (fagcuentacredito) verificado en la BD.
PERIODO_CARTERA = 202512
TOLERANCIA_CANCELACION = money("1.00")


def listar_ahorros(conn: Connection, pkcliente: int) -> list[dict]:
    """Cuentas de ahorro del cliente uniendo el snapshot más reciente de fcuentaahorro."""
    sql = text(
        """
        SELECT a.codcuentaahorro,
               tca.destipocuentaahorro            AS tipo,
               f.montosaldocapitaltotal           AS saldo,
               ec.desestadocuenta                 AS estado,
               m.desmoneda                        AS moneda,
               f.tasaefectivaanual                AS tea
        FROM dcuentaahorro a
        JOIN fcuentaahorro f
          ON f.pkcuentaahorro = a.pkcuentaahorro
         AND f.periododia = (
               SELECT MAX(f2.periododia) FROM fcuentaahorro f2
               WHERE f2.pkcuentaahorro = a.pkcuentaahorro)
        JOIN dtipocuentaahorro tca ON tca.pktipocuentaahorro = f.pktipocuentaahorro
        JOIN destadocuenta ec      ON ec.pkestadocuenta      = f.pkestadocuenta
        JOIN dmoneda m             ON m.pkmoneda             = f.pkmoneda
        WHERE a.pkcliente = :pk
        ORDER BY a.codcuentaahorro
        """
    )
    return [dict(r) for r in conn.execute(sql, {"pk": pkcliente}).mappings().all()]


def buscar_cuenta_ahorro(conn: Connection, codcuentaahorro: str) -> dict | None:
    """Datos base de una cuenta de ahorro (pk, cliente, agencia, moneda, saldo)."""
    sql = text(
        """
        SELECT a.pkcuentaahorro, a.pkcliente, a.codcuentaahorro,
               f.pkagencia, f.pkmoneda, f.pkproductoahorro,
               f.montosaldocapitaltotal AS saldo
        FROM dcuentaahorro a
        JOIN fcuentaahorro f
          ON f.pkcuentaahorro = a.pkcuentaahorro
         AND f.periododia = (
               SELECT MAX(f2.periododia) FROM fcuentaahorro f2
               WHERE f2.pkcuentaahorro = a.pkcuentaahorro)
        WHERE TRIM(a.codcuentaahorro) = :cod
        """
    )
    row = conn.execute(sql, {"cod": codcuentaahorro}).mappings().first()
    return dict(row) if row else None


def listar_movimientos(conn: Connection, pkcuentaahorro: int, limit: int) -> list[dict]:
    """Movimientos de una cuenta de ahorro desde foperaciones."""
    sql = text(
        """
        SELECT o.fechahoraoperacion::date     AS fecha,
               co.desconceptooperacion        AS concepto,
               ct.descanaltransaccional       AS canal,
               mp.desmediopago                AS medio,
               o.montooperacion               AS monto,
               o.codtipoegresoingreso         AS signo
        FROM foperaciones o
        JOIN dconceptooperacion co  ON co.pkconceptooperacion = o.pkconceptooperacion
        LEFT JOIN dcanaltransaccional ct ON ct.pkcanaltransaccional = o.pkcanaltransaccional
        LEFT JOIN dmediopago mp     ON mp.pkmediopago = o.pkmediopago
        WHERE o.pkcuentaahorro = :pk
        ORDER BY o.fechahoraoperacion DESC, o.pkoperacion DESC
        LIMIT :lim
        """
    )
    return [dict(r) for r in conn.execute(sql, {"pk": pkcuentaahorro, "lim": limit}).mappings().all()]


def listar_creditos(conn: Connection, pkcliente: int) -> list[dict]:
    """Créditos del cliente en el periodo de cartera (fagcuentacredito).

    'pago_pendiente' = montosaldocliente (saldo total que el cliente adeuda).
    """
    sql = text(
        """
        SELECT cr.codcuentacredito,
               fa.fechadesembolsocredito  AS fecha_desembolso,
               p.codtipocredito           AS cod_tipo_credito,
               CASE p.codtipocredito
                   WHEN '01' THEN 'Microempresa'
                   WHEN '02' THEN 'Pequeña Empresa'
                   WHEN '03' THEN 'Consumo'
                   ELSE COALESCE(NULLIF(TRIM(p.destipocredito), ''), 'Crédito')
               END                         AS tipo_credito,
               p.desproducto               AS producto,
               fa.montoaprobadocredito     AS monto_aprobado,
               COALESCE(fa.nrocuotas, stats.total_cronograma, 0) AS total_cuotas,
               CASE
                 WHEN (
                   COALESCE(fa.montosaldocapital, 0)
                   + COALESCE(fa.montosaldointeres, 0)
                   + COALESCE(fa.montosaldomoratorio, 0)
                   + COALESCE(fa.montosaldogasto, 0)
                 ) <= :tolerancia
                 THEN COALESCE(fa.nrocuotas, stats.total_cronograma, 0)
                 ELSE GREATEST(
                   COALESCE(fa.nrocuotas, stats.total_cronograma, 0) - COALESCE(stats.cuotas_pendientes, 0),
                   0
                 )
               END                         AS cuotas_pagadas,
               CASE
                 WHEN (
                   COALESCE(fa.montosaldocapital, 0)
                   + COALESCE(fa.montosaldointeres, 0)
                   + COALESCE(fa.montosaldomoratorio, 0)
                   + COALESCE(fa.montosaldogasto, 0)
                 ) <= :tolerancia
                 THEN 0
                 ELSE COALESCE(stats.cuotas_pendientes, 0)
               END                         AS cuotas_pendientes,
               fa.tasainterescompensatoria AS tasa_compensatoria,
               fa.tasainteresmoratoria     AS tasa_moratoria,
               fa.montosaldocapital       AS saldo_capital,
               fa.montosaldointeres        AS saldo_interes,
               fa.montosaldomoratorio      AS saldo_moratorio,
               fa.montosaldogasto          AS saldo_gasto,
               (
                 COALESCE(fa.montosaldocapital, 0)
                 + COALESCE(fa.montosaldointeres, 0)
                 + COALESCE(fa.montosaldomoratorio, 0)
                 + COALESCE(fa.montosaldogasto, 0)
               ) AS pago_pendiente,
               fa.diasatrasocredito       AS dias_atraso,
               CASE p.codtipocredito
                   WHEN '01' THEN 'Microfinanzas: tasa segun riesgo y garantia del negocio.'
                   WHEN '02' THEN 'PYME: tasa segun perfil, antiguedad y garantia.'
                   WHEN '03' THEN 'Consumo: TEA referencial 50.00% a 259.40% segun evaluacion.'
                   ELSE 'Tasa segun evaluacion crediticia.'
               END                         AS rango_tea_referencial,
               'Si te atrasas, se aplica interes moratorio diario, interes compensatorio adicional y posible penalidad segun dias de atraso.' AS recomendacion_mora,
               cal.descalificacioncrediticia AS calificacion
        FROM dcuentacredito cr
        JOIN fagcuentacredito fa
          ON fa.pkcuentacredito = cr.pkcuentacredito AND fa.periodomes = :periodo
        JOIN dproducto p
          ON p.pkproducto = fa.pkproducto
        LEFT JOIN dcalificacioncrediticia cal
          ON cal.pkcalificacioncrediticia = fa.pkcalificacioncrediticiainterna
        LEFT JOIN LATERAL (
          SELECT
            COUNT(*) AS total_cronograma,
            COUNT(*) FILTER (WHERE x.fechapagocuota IS NOT NULL) AS cuotas_con_fecha,
            COUNT(*) FILTER (WHERE x.fechapagocuota IS NULL) AS cuotas_pendientes,
            MAX(x.nrocuota) FILTER (
              WHERE x.capital_acumulado <= (COALESCE(fa.montoaprobadocredito, 0) - COALESCE(fa.montosaldocapital, 0) + :tolerancia)
            ) AS cuotas_por_capital
          FROM (
            SELECT
              pp.nrocuota,
              pp.fechapagocuota,
              SUM(COALESCE(pp.montocapitalpagado, pp.montocapitalprogramado, pp.montocuota, 0))
                OVER (ORDER BY pp.nrocuota) AS capital_acumulado
            FROM fplanpagomes pp
            WHERE pp.pkcuentacredito = cr.pkcuentacredito
              AND pp.periodomes = :periodo
          ) x
        ) stats ON TRUE
        WHERE cr.pkcliente = :pk
        ORDER BY cr.codcuentacredito
        """
    )
    rows = []
    params = {"pk": pkcliente, "periodo": PERIODO_CARTERA, "tolerancia": TOLERANCIA_CANCELACION}
    for row in conn.execute(sql, params).mappings().all():
        item = dict(row)
        if money(item["pago_pendiente"]) <= TOLERANCIA_CANCELACION:
            item["saldo_capital"] = money(0)
            item["saldo_interes"] = money(0)
            item["saldo_moratorio"] = money(0)
            item["saldo_gasto"] = money(0)
            item["pago_pendiente"] = money(0)
            item["dias_atraso"] = 0
            item["cuotas_pagadas"] = item["total_cuotas"]
            item["cuotas_pendientes"] = 0
        itf = ITFEngine.calculate(item["pago_pendiente"])
        item["itf_estimado_cancelacion"] = itf
        item["total_estimado_cancelacion"] = money(item["pago_pendiente"] + itf)
        rows.append(item)
    return rows


def buscar_cuenta_credito(conn: Connection, codcuentacredito: str) -> dict | None:
    """Datos base de un crédito + agencia/moneda/producto/asesor del periodo de cartera."""
    sql = text(
        """
        SELECT cr.pkcuentacredito, cr.pkcliente, cr.codcuentacredito,
               fa.pkagencia, fa.pkmoneda, fa.pkproducto, fa.pkasesor
        FROM dcuentacredito cr
        LEFT JOIN fagcuentacredito fa
          ON fa.pkcuentacredito = cr.pkcuentacredito AND fa.periodomes = :periodo
        WHERE TRIM(cr.codcuentacredito) = :cod
        """
    )
    row = conn.execute(
        sql, {"cod": codcuentacredito, "periodo": PERIODO_CARTERA}
    ).mappings().first()
    return dict(row) if row else None


def detalle_subproducto_ahorro(conn: Connection, codcuentaahorro: str) -> dict | None:
    """Trae el snapshot más reciente de fcuentaahorro con el código de tipo y los
    campos específicos de cada subproducto (PF / CTS / AP). Incluye pkcliente para
    validar pertenencia y pkcuentaahorro para el cronograma del Ahorro Programado.
    """
    sql = text(
        """
        SELECT a.pkcuentaahorro, a.pkcliente, a.codcuentaahorro,
               t.codtipocuentaahorro, t.destipocuentaahorro,
               f.fechavigencia_pf, f.nrodiasplazofijo_pf, f.montosaldocapital_pf,
               f.montointerespactado_pf, f.montointeresdevengado_pf,
               f.montointerespagado_pf, f.tasapagada_pf, f.numerorenovacion_pf,
               f.montocapital_cts, f.montointeres_cts,
               f.montocapitalintangible_cts, f.montointeresintangible_cts,
               f.montocapital_ap, f.montocuota_ap, f.nrocuota_ap,
               f.tasaincentivo_ap, f.fechavigencia_ap
        FROM dcuentaahorro a
        JOIN fcuentaahorro f
          ON f.pkcuentaahorro = a.pkcuentaahorro
         AND f.periododia = (
               SELECT MAX(f2.periododia) FROM fcuentaahorro f2
               WHERE f2.pkcuentaahorro = a.pkcuentaahorro)
        JOIN dtipocuentaahorro t ON t.pktipocuentaahorro = f.pktipocuentaahorro
        WHERE TRIM(a.codcuentaahorro) = :cod
        """
    )
    row = conn.execute(sql, {"cod": codcuentaahorro}).mappings().first()
    return dict(row) if row else None


def cronograma_ahorro_programado(conn: Connection, pkcuentaahorro: int) -> list[dict]:
    """Calendario de depósitos del Ahorro Programado desde fcuentaahorroprogramado."""
    sql = text(
        """
        SELECT TRIM(coddeposito)        AS coddeposito,
               fechadepositocuota       AS fecha_programada,
               fechaefectuadocuota      AS fecha_efectuada,
               montocuota               AS monto_cuota,
               montoamortizado          AS monto_amortizado,
               nrodiasretrazo           AS dias_retraso,
               codestadocuota           AS estado,
               (fechaefectuadocuota IS NOT NULL) AS depositada
        FROM fcuentaahorroprogramado
        WHERE pkcuentaahorro = :pk
        ORDER BY coddeposito
        """
    )
    return [dict(r) for r in conn.execute(sql, {"pk": pkcuentaahorro}).mappings().all()]


def listar_cuotas(conn: Connection, pkcuentacredito: int) -> list[dict]:
    """Cronograma completo.

    En la BD del proyecto las filas de fplanpagomes representan las cuotas que
    faltan pagar cuando el credito sigue con deuda. Las cuotas ya pagadas pueden
    no estar cargadas; por eso se reconstruyen como cuotas historicas virtuales.
    """
    meta_sql = text(
        """
        SELECT
            fa.nrocuotas AS total_cuotas,
            fa.fechadesembolsocredito AS fecha_desembolso,
            COALESCE(fa.montoaprobadocredito, 0) AS monto_aprobado,
            (
              COALESCE(fa.montosaldocapital, 0)
              + COALESCE(fa.montosaldointeres, 0)
              + COALESCE(fa.montosaldomoratorio, 0)
              + COALESCE(fa.montosaldogasto, 0)
            ) AS pago_pendiente
        FROM fagcuentacredito fa
        WHERE fa.pkcuentacredito = :pk AND fa.periodomes = :periodo
        """
    )
    rows_sql = text(
        """
        SELECT p.nrocuota,
               p.fechavencimientopagocuota AS fecha_vencimiento,
               p.montocuota                AS monto_cuota,
               p.montosaldo                AS monto_saldo,
               p.montocapitalprogramado    AS capital_programado,
               p.montointeresprogramado    AS interes_programado,
               p.diasatrasocuota           AS dias_atraso,
               p.codestadocuota            AS estado,
               p.fechapagocuota
        FROM fplanpagomes p
        WHERE p.pkcuentacredito = :pk
          AND p.periodomes = :periodo
        ORDER BY p.nrocuota
        """
    )
    params = {"pk": pkcuentacredito, "periodo": PERIODO_CARTERA}
    meta = conn.execute(meta_sql, params).mappings().first()
    db_rows = [dict(r) for r in conn.execute(rows_sql, params).mappings().all()]
    if not meta and not db_rows:
        return []

    total_cuotas = int((meta or {}).get("total_cuotas") or len(db_rows) or 0)
    monto_aprobado = money((meta or {}).get("monto_aprobado") or 0)
    pago_pendiente = money((meta or {}).get("pago_pendiente") or 0)
    fecha_desembolso = (meta or {}).get("fecha_desembolso")
    deuda_real = pago_pendiente > TOLERANCIA_CANCELACION

    paid_real = [r for r in db_rows if r.get("fechapagocuota") is not None]
    pending_real = [r for r in db_rows if r.get("fechapagocuota") is None] if deuda_real else []
    if deuda_real:
        virtual_paid_count = max(total_cuotas - len(pending_real) - len(paid_real), 0)
    else:
        virtual_paid_count = max(total_cuotas - len(paid_real), 0)

    rows = []
    template = db_rows[0] if db_rows else {}
    cuota_ref = money(template.get("monto_cuota") or (monto_aprobado / Decimal(total_cuotas) if total_cuotas else 0))
    capital_ref = money(template.get("capital_programado") or (monto_aprobado / Decimal(total_cuotas) if total_cuotas else cuota_ref))
    interes_ref = money(max(Decimal("0"), cuota_ref - capital_ref))

    for nro in range(1, virtual_paid_count + 1):
        saldo = money(max(Decimal("0"), monto_aprobado - (capital_ref * Decimal(nro))))
        rows.append(_cuota_con_costos({
            "nrocuota": nro,
            "total_cuotas": total_cuotas,
            "fecha_vencimiento": _add_months(fecha_desembolso, nro),
            "monto_cuota": cuota_ref,
            "monto_saldo": saldo,
            "capital_programado": capital_ref,
            "interes_programado": interes_ref,
            "dias_atraso": 0,
            "estado": "PAGADA",
            "pagada": True,
            "monto_aprobado": monto_aprobado,
        }))

    for row in paid_real:
        rows.append(_cuota_con_costos(_normalizar_cuota_real(row, total_cuotas, monto_aprobado, True)))

    next_nro = len(rows) + 1
    for row in pending_real:
        item = _normalizar_cuota_real(row, total_cuotas, monto_aprobado, False)
        item["nrocuota"] = next_nro
        next_nro += 1
        rows.append(_cuota_con_costos(item))

    rows.sort(key=lambda item: item["nrocuota"])
    return rows


def _normalizar_cuota_real(row: dict, total_cuotas: int, monto_aprobado: Decimal, pagada: bool) -> dict:
    return {
        "nrocuota": int(row.get("nrocuota") or 0),
        "total_cuotas": total_cuotas,
        "fecha_vencimiento": row.get("fecha_vencimiento"),
        "monto_cuota": money(row.get("monto_cuota") or 0),
        "monto_saldo": money(row.get("monto_saldo") or 0),
        "capital_programado": money(row.get("capital_programado") or row.get("monto_cuota") or 0),
        "interes_programado": money(row.get("interes_programado") or 0),
        "dias_atraso": int(row.get("dias_atraso") or 0),
        "estado": "PAGADA" if pagada else row.get("estado"),
        "pagada": pagada,
        "monto_aprobado": monto_aprobado,
    }


def _cuota_con_costos(item: dict) -> dict:
    seguro = InstallmentService.insurance(item.get("monto_aprobado") or item.get("monto_saldo") or 0)
    base = money((item.get("capital_programado") or 0) + (item.get("interes_programado") or 0) + seguro)
    itf = ITFEngine.calculate(base)
    item["seguro_desgravamen"] = seguro
    item["itf_estimado"] = itf
    item["total_informativo"] = money(base + itf)
    item.pop("monto_aprobado", None)
    return item


def _add_months(start: date | None, months: int) -> date | None:
    if start is None:
        start = date.today()
    month_index = start.month - 1 + months
    year = start.year + month_index // 12
    month = month_index % 12 + 1
    day = min(start.day, _days_in_month(year, month))
    return date(year, month, day)


def _days_in_month(year: int, month: int) -> int:
    if month == 12:
        next_month = date(year + 1, 1, 1)
    else:
        next_month = date(year, month + 1, 1)
    return (next_month - date(year, month, 1)).days
