"""Escrituras SQL para solicitar un crédito (registro en dsolicitud).

Alcance: solo Microempresa (ME) y Consumo (CO).
"""
from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.engine import Connection

from app.repositories.repo_cuentas import PERIODO_CARTERA, TOLERANCIA_CANCELACION

# codtipocredito del portal -> codtipocredito en dproducto
MAPA_TIPO_CREDITO = {"ME": "01", "CO": "03"}  # ME=Microempresa, CO=Consumo
ESTADO_EN_EVALUACION = "01"  # dsolicitudestado.codsolicitudestado


def _pk_producto_por_tipo(conn: Connection, cod_tipo_producto: str) -> int | None:
    return conn.execute(
        text(
            """
            SELECT MIN(pkproducto) FROM dproducto
            WHERE TRIM(codtipocredito) = :cod AND flagactivo = '1'
            """
        ),
        {"cod": cod_tipo_producto},
    ).scalar()


def _pk_estado_solicitud(conn: Connection, cod: str) -> int | None:
    return conn.execute(
        text("SELECT pksolicitudestado FROM dsolicitudestado WHERE TRIM(codsolicitudestado) = :c"),
        {"c": cod},
    ).scalar()


def _pk_actividad(conn: Connection, cod: str) -> int | None:
    return conn.execute(
        text("SELECT pkactividadeconomica FROM dactividadeconomica WHERE TRIM(codactividadeconomica) = :c"),
        {"c": cod},
    ).scalar()


def _agencia_asesor_del_cliente(conn: Connection, pkcliente: int) -> tuple[int, int]:
    """Toma agencia/asesor del crédito vigente del cliente; si no tiene, usa valores por defecto."""
    row = conn.execute(
        text(
            """
            SELECT pkagencia, pkasesor FROM fagcuentacredito
            WHERE pkcliente = :pk AND periodomes = :periodo
            ORDER BY pkcuentacredito DESC LIMIT 1
            """
        ),
        {"pk": pkcliente, "periodo": PERIODO_CARTERA},
    ).first()
    if row:
        return row[0], row[1]
    # Fallback: primera agencia activa y primer asesor existentes
    pkag = conn.execute(text("SELECT MIN(pkagencia) FROM dagencia")).scalar()
    pkas = conn.execute(text("SELECT MIN(pkasesor) FROM dasesor")).scalar()
    return pkag, pkas


def upsert_fuente_ingreso(
    conn: Connection, pkcliente: int, montoingresoneto: Decimal, pkactividad: int | None
) -> None:
    """Registra el ingreso del cliente (PK compuesta pkcliente+periodomes) de forma idempotente."""
    conn.execute(
        text(
            """
            INSERT INTO fclientefuenteingreso (pkcliente, periodomes, montofuenteingreso,
                                               pkactividadeconomicacliente, fecultactualizacion)
            VALUES (:pk, :periodo, :monto, :act, now())
            ON CONFLICT (pkcliente, periodomes)
            DO UPDATE SET montofuenteingreso = EXCLUDED.montofuenteingreso,
                          pkactividadeconomicacliente = EXCLUDED.pkactividadeconomicacliente,
                          fecultactualizacion = now()
            """
        ),
        {"pk": pkcliente, "periodo": PERIODO_CARTERA, "monto": montoingresoneto, "act": pkactividad},
    )


def crear_solicitud(
    conn: Connection,
    pkcliente: int,
    montosolicitud: Decimal,
    plazo: int,
    codtipocredito: str,
    codactividadeconomica: str,
    montoingresoneto: Decimal,
) -> dict:
    """Registra una solicitud en dsolicitud (estado inicial 'En Evaluación').

    pksolicitud proviene de dsolicitud_pksolicitud_seq y codsolicitud se deriva
    con 'SOL' || LPAD(currval(...)::text, 7, '0').
    """
    cod_tipo_producto = MAPA_TIPO_CREDITO[codtipocredito]
    pkproducto = _pk_producto_por_tipo(conn, cod_tipo_producto)
    if pkproducto is None:
        raise ValueError(f"No hay producto activo para el tipo de crédito '{codtipocredito}'")

    pkestado = _pk_estado_solicitud(conn, ESTADO_EN_EVALUACION)
    if pkestado is None:
        raise ValueError("No existe el estado 'En Evaluación' en dsolicitudestado")

    pkactividad = _pk_actividad(conn, codactividadeconomica)
    if pkactividad is None:
        raise ValueError(f"Actividad económica '{codactividadeconomica}' no encontrada")

    pkmoneda = conn.execute(
        text("SELECT pkmoneda FROM dmoneda WHERE TRIM(codmoneda) = 'SO'")
    ).scalar()
    pkagencia, pkasesor = _agencia_asesor_del_cliente(conn, pkcliente)

    # Registra/actualiza la fuente de ingreso (idempotente) antes de la solicitud.
    upsert_fuente_ingreso(conn, pkcliente, montoingresoneto, pkactividad)

    row = conn.execute(
        text(
            """
            INSERT INTO dsolicitud (
                pksolicitud, codsolicitud, pkcliente, codlineacredito,
                pksolicitudestado, pkmoneda, pkproducto,
                codtiposolicitud, destiposolicitud,
                montosolicitudcredito, nrocuotasolicitud, plazosolicitudcredito,
                fechasolicitudcredito, codususol,
                flaglibreamortizacioncredito, nrodiasgracia,
                pkactividadeconomicasolicitud, pkagencia, pkasesor,
                fechahoracreacion, fechahoraultmodificacion, fecultactualizacion
            ) VALUES (
                nextval('dsolicitud_pksolicitud_seq'),
                'SOL' || LPAD(currval('dsolicitud_pksolicitud_seq')::text, 7, '0'),
                :pkcliente, 'CR',
                :pkestado, :pkmoneda, :pkproducto,
                '01', 'Credito Nuevo',
                :monto, :plazo, :plazo,
                CURRENT_DATE, 'HB',
                'N', 0,
                :pkactividad, :pkagencia, :pkasesor,
                now(), now(), now()
            )
            RETURNING pksolicitud, codsolicitud
            """
        ),
        {
            "pkcliente": pkcliente,
            "pkestado": pkestado,
            "pkmoneda": pkmoneda,
            "pkproducto": pkproducto,
            "monto": montosolicitud,
            "plazo": plazo,
            "pkactividad": pkactividad,
            "pkagencia": pkagencia,
            "pkasesor": pkasesor,
        },
    ).mappings().first()
    conn.commit()
    return {"pksolicitud": row["pksolicitud"], "codsolicitud": row["codsolicitud"].strip()}


def historial_prestamos(conn: Connection, pkcliente: int) -> list[dict]:
    solicitudes_sql = text(
        """
        SELECT
            'SOLICITUD' AS tipo_registro,
            TRIM(s.codsolicitud) AS codigo,
            s.fechasolicitudcredito AS fecha,
            COALESCE(NULLIF(TRIM(s.destiposolicitud), ''), 'Solicitud de credito') AS tipo_credito,
            s.montosolicitudcredito AS monto,
            COALESCE(s.nrocuotasolicitud, s.plazosolicitudcredito)::integer AS plazo,
            NULL::integer AS cuotas_pagadas,
            NULL::integer AS cuotas_pendientes,
            COALESCE(s.nrocuotasolicitud, s.plazosolicitudcredito)::integer AS total_cuotas,
            NULL::numeric AS pago_pendiente,
            COALESCE(NULLIF(TRIM(e.dessolicitudestado), ''), 'En evaluacion') AS estado,
            COALESCE(NULLIF(TRIM(s.desmotivosolicitud), ''), 'Solicitud registrada') AS detalle
        FROM dsolicitud s
        LEFT JOIN dsolicitudestado e ON e.pksolicitudestado = s.pksolicitudestado
        WHERE s.pkcliente = :pk
        """
    )
    creditos_sql = text(
        """
        WITH cuotas AS (
            SELECT
                p.pkcuentacredito,
                p.nrocuota,
                p.fechapagocuota,
                SUM(COALESCE(p.montocapitalpagado, p.montocapitalprogramado, p.montocuota, 0))
                  OVER (PARTITION BY p.pkcuentacredito ORDER BY p.nrocuota) AS capital_acumulado
            FROM fplanpagomes p
            WHERE p.periodomes = :periodo
        ),
        creditos AS (
            SELECT
                cr.pkcuentacredito,
                TRIM(cr.codcuentacredito) AS codcuentacredito,
                fa.fechadesembolsocredito,
                CASE p.codtipocredito
                    WHEN '01' THEN 'Microempresa'
                    WHEN '02' THEN 'Pequena Empresa'
                    WHEN '03' THEN 'Consumo'
                    ELSE COALESCE(NULLIF(TRIM(p.destipocredito), ''), 'Credito')
                END AS tipo_credito,
                COALESCE(fa.montoaprobadocredito, 0) AS monto_aprobado,
                COALESCE(fa.nrocuotas, 0) AS total_cuotas,
                COALESCE(fa.montoaprobadocredito, 0) - COALESCE(fa.montosaldocapital, 0) AS capital_amortizado,
                (
                    COALESCE(fa.montosaldocapital, 0)
                    + COALESCE(fa.montosaldointeres, 0)
                    + COALESCE(fa.montosaldomoratorio, 0)
                    + COALESCE(fa.montosaldogasto, 0)
                ) AS pago_pendiente,
                COALESCE(cal.descalificacioncrediticia, 'Normal') AS calificacion
            FROM dcuentacredito cr
            JOIN fagcuentacredito fa
              ON fa.pkcuentacredito = cr.pkcuentacredito AND fa.periodomes = :periodo
            LEFT JOIN dproducto p ON p.pkproducto = fa.pkproducto
            LEFT JOIN dcalificacioncrediticia cal
              ON cal.pkcalificacioncrediticia = fa.pkcalificacioncrediticiainterna
            WHERE cr.pkcliente = :pk
        )
        SELECT
            'CREDITO' AS tipo_registro,
            c.codcuentacredito AS codigo,
            c.fechadesembolsocredito AS fecha,
            c.tipo_credito,
            c.monto_aprobado AS monto,
            c.total_cuotas::integer AS plazo,
            CASE
                WHEN c.pago_pendiente <= :tolerancia THEN c.total_cuotas
                ELSE GREATEST(c.total_cuotas - COUNT(q.nrocuota) FILTER (WHERE q.fechapagocuota IS NULL), 0)
            END::integer AS cuotas_pagadas,
            CASE
                WHEN c.pago_pendiente <= :tolerancia THEN 0
                ELSE COUNT(q.nrocuota) FILTER (WHERE q.fechapagocuota IS NULL)
            END::integer AS cuotas_pendientes,
            c.total_cuotas::integer AS total_cuotas,
            CASE WHEN c.pago_pendiente <= :tolerancia THEN 0 ELSE c.pago_pendiente END AS pago_pendiente,
            CASE WHEN c.pago_pendiente <= :tolerancia THEN 'Cancelado' ELSE 'Vigente' END AS estado,
            CASE
                WHEN c.pago_pendiente <= :tolerancia THEN 'Credito pagado completamente.'
                ELSE 'Credito activo. Calificacion: ' || c.calificacion
            END AS detalle
        FROM creditos c
        LEFT JOIN cuotas q ON q.pkcuentacredito = c.pkcuentacredito
        GROUP BY
            c.pkcuentacredito, c.codcuentacredito, c.fechadesembolsocredito,
            c.tipo_credito, c.monto_aprobado, c.total_cuotas,
            c.pago_pendiente, c.capital_amortizado, c.calificacion
        """
    )

    params = {"pk": pkcliente, "periodo": PERIODO_CARTERA, "tolerancia": TOLERANCIA_CANCELACION}
    rows = [dict(r) for r in conn.execute(solicitudes_sql, params).mappings().all()]
    rows.extend(dict(r) for r in conn.execute(creditos_sql, params).mappings().all())
    rows.sort(key=lambda item: (item.get("fecha") is not None, item.get("fecha"), item.get("codigo")), reverse=True)
    return rows
