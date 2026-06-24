"""Consultas/escrituras SQL de operaciones: pago de cuota y transferencia.

Inserción en foperaciones respetando TODAS las columnas NOT NULL verificadas:
codtipkar, codkardex (único), codtipoegresoingreso, periododia (FK a dtiempo),
pkconceptooperacion, pktipooperacion, pkmoneda, pkagenciaorigen,
montooperacion, montopagoconcepto, fechahoraoperacion.
"""
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.repositories import repo_catalogos as cat
from app.services.financial import InstallmentService, PaymentService, PenaltyEngine
from app.services.financial.engines import money

PERIODO_CARTERA = 202512
TOLERANCIA_CANCELACION = money("1.00")


def periododia_hoy(conn: Connection) -> int:
    """periododia (yyyymmdd) de hoy según el reloj de la BD. Debe existir en dtiempo."""
    return conn.execute(
        text("SELECT CAST(to_char(CURRENT_DATE, 'YYYYMMDD') AS integer)")
    ).scalar()


def _siguiente_pkoperacion(conn: Connection) -> int:
    return conn.execute(text("SELECT nextval('foperaciones_pkoperacion_seq')")).scalar()


def mover_saldo_ahorro(conn: Connection, pkcuentaahorro: int, delta: Decimal) -> None:
    """Aplica un delta al saldo de la cuenta de ahorro (negativo=débito, positivo=abono).

    Actualiza el snapshot más reciente de fcuentaahorro (montosaldocapitaltotal, que es el
    campo que devuelve la consulta de cuentas). Así el saldo refleja las operaciones del
    homebanking y la validación de fondos es real entre llamadas.
    """
    conn.execute(
        text(
            """
            UPDATE fcuentaahorro
            SET montosaldocapitaltotal = montosaldocapitaltotal + :delta,
                fecultactualizacion = now()
            WHERE pkcuentaahorro = :pk
              AND periododia = (SELECT MAX(periododia) FROM fcuentaahorro
                                WHERE pkcuentaahorro = :pk)
            """
        ),
        {"delta": delta, "pk": pkcuentaahorro},
    )


def insertar_operacion(
    conn: Connection,
    *,
    pkoperacion: int,
    codtipkar: str,            # 'CR' abono / 'DB' cargo
    codkardex: str,            # único por movimiento (<=20 chars)
    cod_concepto: str,         # ej. PCAP, TRAN
    cod_tipooperacion: str,    # ej. DEB, CRE, TRF
    cod_canal: str,            # ej. APP
    cod_mediopago: str,        # ej. APP
    signo: str,                # 'I' ingreso / 'E' egreso
    periododia: int,
    pkmoneda: int,
    pkagenciaorigen: int,
    monto: Decimal,
    pkcuentaahorro: int | None = None,
    pkcuentacredito: int | None = None,
    nrocuota: int | None = None,
) -> None:
    """Inserta una fila en foperaciones resolviendo los PKs de catálogo por código."""
    params = {
        "pkoperacion": pkoperacion,
        "codtipkar": codtipkar,
        "codkardex": codkardex,
        "pkconcepto": cat.pk_concepto(conn, cod_concepto),
        "pktipooperacion": cat.pk_tipooperacion(conn, cod_tipooperacion),
        "pkcanal": cat.pk_canal(conn, cod_canal),
        "pkmediopago": cat.pk_mediopago(conn, cod_mediopago),
        "pkcondicion": cat.pk_condicioncontable(conn, "01"),  # Vigente Normal
        "signo": signo,
        "periododia": periododia,
        "pkmoneda": pkmoneda,
        "pkagenciaorigen": pkagenciaorigen,
        "monto": monto,
        "pkcuentaahorro": pkcuentaahorro,
        "pkcuentacredito": pkcuentacredito,
        "nrocuota": nrocuota,
    }
    conn.execute(
        text(
            """
            INSERT INTO foperaciones (
                pkoperacion, codtipkar, codkardex,
                pkconceptooperacion, pktipooperacion, pkcanaltransaccional,
                pkmediopago, pkcondicioncontable, codtipoegresoingreso,
                periododia, fechahoraoperacion, pkmoneda, pkagenciaorigen,
                montooperacion, montopagoconcepto,
                pkcuentaahorro, pkcuentacredito, nrocuotaplazo,
                codusuope, fecultactualizacion
            ) VALUES (
                :pkoperacion, :codtipkar, :codkardex,
                :pkconcepto, :pktipooperacion, :pkcanal,
                :pkmediopago, :pkcondicion, :signo,
                :periododia, now(), :pkmoneda, :pkagenciaorigen,
                :monto, :monto,
                :pkcuentaahorro, :pkcuentacredito, :nrocuota,
                'HB', now()
            )
            """
        ),
        params,
    )


# --------------------------------------------------------------------------
# PAGO DE CUOTA
# --------------------------------------------------------------------------
def proxima_cuota_pendiente(conn: Connection, pkcuentacredito: int) -> dict | None:
    """Próxima cuota pendiente = menor nrocuota con fechapagocuota IS NULL.

    Nota verificada en la BD: montocapitalpagado NO sirve como flag de pago
    (trae el capital amortizado del cronograma, siempre > 0). El marcador real
    de pago es fechapagocuota.
    """
    sql = text(
        """
        WITH cuotas AS (
          SELECT p.periodomes,
                 p.nrocuota,
                 p.montocuota,
                 p.montosaldo,
                 p.montocapitalprogramado,
                 p.montointeresprogramado,
                 p.diasatrasocuota,
                 p.fechapagocuota,
                 fa.montoaprobadocredito,
                 (
                   COALESCE(fa.montosaldocapital, 0)
                   + COALESCE(fa.montosaldointeres, 0)
                   + COALESCE(fa.montosaldomoratorio, 0)
                   + COALESCE(fa.montosaldogasto, 0)
                 ) AS pago_pendiente
          FROM fplanpagomes p
          LEFT JOIN fagcuentacredito fa
            ON fa.pkcuentacredito = p.pkcuentacredito AND fa.periodomes = :periodo
          WHERE p.pkcuentacredito = :pk
            AND p.periodomes = :periodo
        )
        SELECT periodomes,
               nrocuota,
               montocuota,
               montosaldo,
               montocapitalprogramado,
               montointeresprogramado,
               diasatrasocuota,
               montoaprobadocredito
        FROM cuotas
        WHERE fechapagocuota IS NULL
          AND pago_pendiente > :tolerancia
        ORDER BY nrocuota
        LIMIT 1
        """
    )
    row = conn.execute(
        sql,
        {
            "pk": pkcuentacredito,
            "periodo": PERIODO_CARTERA,
            "tolerancia": TOLERANCIA_CANCELACION,
        },
    ).mappings().first()
    return dict(row) if row else None


def marcar_cuota_pagada(
    conn: Connection, periodomes: int, pkcuentacredito: int, nrocuota: int, capital: Decimal
) -> None:
    """Registra el pago de la cuota: solo el capital amortiza saldo."""
    conn.execute(
        text(
            """
            UPDATE fplanpagomes
            SET montocapitalpagado = :capital,
                fechapagocuota = CURRENT_DATE,
                fecultactualizacion = now()
            WHERE periodomes = :pm AND pkcuentacredito = :pk AND nrocuota = :nro
            """
        ),
        {"capital": capital, "pm": periodomes, "pk": pkcuentacredito, "nro": nrocuota},
    )


def actualizar_saldo_credito(conn: Connection, pkcuentacredito: int, capital: Decimal) -> None:
    conn.execute(
        text(
            """
            UPDATE fagcuentacredito
            SET montosaldocapital = GREATEST(0, COALESCE(montosaldocapital, 0) - :capital),
                montosaldocliente = GREATEST(0, COALESCE(montosaldocliente, 0) - :capital),
                fecultactualizacion = now()
            WHERE pkcuentacredito = :pk AND periodomes = :periodo
            """
        ),
        {"capital": capital, "pk": pkcuentacredito, "periodo": PERIODO_CARTERA},
    )


def _monto_cuota_base(cuota: dict) -> Decimal:
    capital = money(cuota.get("montocapitalprogramado") or cuota.get("montocuota") or 0)
    interest = money(cuota.get("montointeresprogramado") or 0)
    insurance = InstallmentService.insurance(cuota.get("montoaprobadocredito") or cuota.get("montosaldo") or 0)
    penalty = PenaltyEngine.lookup_penalty(capital + interest + insurance, int(cuota.get("diasatrasocuota") or 0))
    return money(capital + interest + insurance + penalty)


def pagar_cuota(
    conn: Connection, credito: dict, monto: Decimal | None, origen: dict | None = None
) -> dict:
    """Paga la próxima cuota pendiente del crédito.

    Si `origen` (cuenta de ahorro propia) se entrega, el dinero se DEBITA de esa cuenta:
    se registra un cargo 'E' en foperaciones sobre el ahorro y se reduce su saldo, además
    del registro del pago al crédito. Si no se entrega, mantiene el comportamiento previo
    (solo registra el pago del crédito). Hace commit al final.
    """
    cuota = proxima_cuota_pendiente(conn, credito["pkcuentacredito"])
    if cuota is None:
        raise ValueError("El crédito no tiene cuotas pendientes")

    monto_pago = money(monto if monto is not None else _monto_cuota_base(cuota))
    pago_info = PaymentService.payment_summary(monto_pago)
    capital_pagado = money(min(monto_pago, cuota.get("montocapitalprogramado") or cuota["montocuota"]))

    # Si se debita de un ahorro, validar saldo contra el monto real de la cuota.
    if origen is not None and (
        origen.get("saldo") is None or origen["saldo"] < pago_info["total_debited"]
    ):
        raise ValueError("Saldo insuficiente en la cuenta de ahorro origen")

    periododia = periododia_hoy(conn)
    pkop = _siguiente_pkoperacion(conn)
    codkardex = f"PAG-{credito['pkcuentacredito']}-{cuota['nrocuota']}-{periododia}"[:20]

    # 1) marca la cuota como pagada
    marcar_cuota_pagada(
        conn, cuota["periodomes"], credito["pkcuentacredito"], cuota["nrocuota"], capital_pagado
    )
    actualizar_saldo_credito(conn, credito["pkcuentacredito"], capital_pagado)
    # 2) registra el pago al crédito (concepto PCAP, tipo DEB, canal APP, egreso)
    insertar_operacion(
        conn,
        pkoperacion=pkop,
        codtipkar="DB",
        codkardex=codkardex,
        cod_concepto="PCAP",
        cod_tipooperacion="DEB",
        cod_canal="APP",
        cod_mediopago="APP",
        signo="E",
        periododia=periododia,
        pkmoneda=credito["pkmoneda"],
        pkagenciaorigen=credito["pkagencia"],
        monto=monto_pago,
        pkcuentacredito=credito["pkcuentacredito"],
        nrocuota=cuota["nrocuota"],
    )

    pk_deb_ahorro = None
    if origen is not None:
        # 3) débito real desde la cuenta de ahorro (retiro para pagar el crédito)
        pk_deb_ahorro = _siguiente_pkoperacion(conn)
        insertar_operacion(
            conn,
            pkoperacion=pk_deb_ahorro,
            codtipkar="DB",
            codkardex=f"PCA-{pk_deb_ahorro}"[:20],
            cod_concepto="RAHO",   # Retiro Ahorro (sale de la cuenta para pagar el crédito)
            cod_tipooperacion="DEB",
            cod_canal="APP",
            cod_mediopago="APP",
            signo="E",
            periododia=periododia,
            pkmoneda=origen["pkmoneda"],
            pkagenciaorigen=origen["pkagencia"],
            monto=pago_info["total_debited"],
            pkcuentaahorro=origen["pkcuentaahorro"],
        )
        mover_saldo_ahorro(conn, origen["pkcuentaahorro"], -pago_info["total_debited"])

    conn.commit()
    return {
        "nrocuota": cuota["nrocuota"],
        "monto_pagado": monto_pago,
        "itf_estimado": pago_info["itf"],
        "total_debitado_estimado": pago_info["total_debited"],
        "pkoperacion": pkop,
        "pkoperacion_debito_ahorro": pk_deb_ahorro,
        "codkardex": codkardex,
    }


# --------------------------------------------------------------------------
# PAGO DE SERVICIOS (debita una cuenta de ahorro propia)
# --------------------------------------------------------------------------
def pagar_servicio(
    conn: Connection,
    origen: dict,
    desservicio: str,
    codsuministro: str,
    monto: Decimal,
) -> dict:
    """Registra un pago de servicio debitando la cuenta de ahorro: cargo 'E' en
    foperaciones (concepto PSER, tipo PAG, canal APP) + reducción de saldo. Commit al final.
    """
    periododia = periododia_hoy(conn)
    pkop = _siguiente_pkoperacion(conn)
    insertar_operacion(
        conn,
        pkoperacion=pkop,
        codtipkar="DB",
        codkardex=f"SER-{pkop}"[:20],
        cod_concepto="PSER",
        cod_tipooperacion="PAG",
        cod_canal="APP",
        cod_mediopago="APP",
        signo="E",
        periododia=periododia,
        pkmoneda=origen["pkmoneda"],
        pkagenciaorigen=origen["pkagencia"],
        monto=monto,
        pkcuentaahorro=origen["pkcuentaahorro"],
    )
    mover_saldo_ahorro(conn, origen["pkcuentaahorro"], -monto)
    conn.commit()
    return {"pkoperacion": pkop, "codkardex": f"SER-{pkop}"[:20]}


# --------------------------------------------------------------------------
# TRANSFERENCIA ENTRE CUENTAS PROPIAS
# --------------------------------------------------------------------------
def transferir(conn: Connection, origen: dict, destino: dict, monto: Decimal) -> dict:
    """Inserta 2 filas en foperaciones (débito en origen 'E', crédito en destino 'I').
    tipo TRF, concepto TRAN, canal APP. Hace commit al final.
    """
    periododia = periododia_hoy(conn)
    pk_deb = _siguiente_pkoperacion(conn)
    pk_cre = _siguiente_pkoperacion(conn)

    insertar_operacion(
        conn,
        pkoperacion=pk_deb,
        codtipkar="DB",
        codkardex=f"TRF-{pk_deb}"[:20],
        cod_concepto="TRAN",
        cod_tipooperacion="TRF",
        cod_canal="APP",
        cod_mediopago="APP",
        signo="E",
        periododia=periododia,
        pkmoneda=origen["pkmoneda"],
        pkagenciaorigen=origen["pkagencia"],
        monto=monto,
        pkcuentaahorro=origen["pkcuentaahorro"],
    )
    insertar_operacion(
        conn,
        pkoperacion=pk_cre,
        codtipkar="CR",
        codkardex=f"TRF-{pk_cre}"[:20],
        cod_concepto="TRAN",
        cod_tipooperacion="TRF",
        cod_canal="APP",
        cod_mediopago="APP",
        signo="I",
        periododia=periododia,
        pkmoneda=destino["pkmoneda"],
        pkagenciaorigen=destino["pkagencia"],
        monto=monto,
        pkcuentaahorro=destino["pkcuentaahorro"],
    )
    # Mueve los saldos para que la consulta refleje la transferencia (débito/abono reales).
    mover_saldo_ahorro(conn, origen["pkcuentaahorro"], -monto)
    mover_saldo_ahorro(conn, destino["pkcuentaahorro"], monto)
    conn.commit()
    return {"pkoperacion_debito": pk_deb, "pkoperacion_credito": pk_cre}
