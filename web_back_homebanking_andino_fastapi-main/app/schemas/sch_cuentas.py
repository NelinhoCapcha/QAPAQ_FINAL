"""Schemas pydantic para consultas de cuentas (ahorro y crédito)."""
from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class CuentaAhorroOut(BaseModel):
    codcuentaahorro: str
    tipo: str
    saldo: Decimal
    estado: str
    moneda: str
    tea: Decimal | None = None


class MovimientoOut(BaseModel):
    fecha: date
    concepto: str | None = None
    canal: str | None = None
    medio: str | None = None
    monto: Decimal
    signo: str  # 'I' ingreso / 'E' egreso


class CuentaCreditoOut(BaseModel):
    codcuentacredito: str
    fecha_desembolso: date | None = None
    cod_tipo_credito: str | None = None
    tipo_credito: str | None = None
    producto: str | None = None
    monto_aprobado: Decimal | None = None
    total_cuotas: int | None = None
    cuotas_pagadas: int | None = None
    cuotas_pendientes: int | None = None
    tasa_compensatoria: Decimal | None = None
    tasa_moratoria: Decimal | None = None
    saldo_interes: Decimal | None = None
    saldo_moratorio: Decimal | None = None
    saldo_gasto: Decimal | None = None
    itf_estimado_cancelacion: Decimal | None = None
    total_estimado_cancelacion: Decimal | None = None
    rango_tea_referencial: str | None = None
    recomendacion_mora: str | None = None
    saldo_capital: Decimal
    pago_pendiente: Decimal
    dias_atraso: int
    calificacion: str | None = None


class CuotaOut(BaseModel):
    nrocuota: int
    total_cuotas: int | None = None
    fecha_vencimiento: date
    monto_cuota: Decimal
    monto_saldo: Decimal
    capital_programado: Decimal | None = None
    interes_programado: Decimal | None = None
    seguro_desgravamen: Decimal | None = None
    itf_estimado: Decimal | None = None
    total_informativo: Decimal | None = None
    dias_atraso: int
    estado: str
    pagada: bool


# --- Detalle por subproducto de ahorro (PF / CTS / AP) ---
class PlazoFijoDetalle(BaseModel):
    fecha_vigencia: date | None = None
    nro_dias_plazo: int
    saldo_capital: Decimal
    interes_pactado: Decimal
    interes_devengado: Decimal
    interes_pagado: Decimal
    tasa_pagada: Decimal
    nro_renovaciones: int


class CtsDetalle(BaseModel):
    capital: Decimal
    interes: Decimal
    capital_intangible: Decimal
    interes_intangible: Decimal
    # Disponible = total - intangible (lo que el trabajador puede retirar por ley)
    disponible: Decimal


class DepositoProgramadoOut(BaseModel):
    coddeposito: str
    fecha_programada: date
    fecha_efectuada: date | None = None
    monto_cuota: Decimal
    monto_amortizado: Decimal
    dias_retraso: int
    estado: str
    depositada: bool


class AhorroProgramadoDetalle(BaseModel):
    capital: Decimal
    monto_cuota: Decimal
    nro_cuotas: int
    tasa_incentivo: Decimal
    fecha_vigencia: date | None = None
    cronograma: list[DepositoProgramadoOut]


class DetalleAhorroResponse(BaseModel):
    codcuentaahorro: str
    tipo: str                      # descripción del tipo (Plazo Fijo, CTS, ...)
    codtipo: str                   # AC / PF / CT / AP
    plazo_fijo: PlazoFijoDetalle | None = None
    cts: CtsDetalle | None = None
    ahorro_programado: AhorroProgramadoDetalle | None = None
    mensaje: str | None = None     # p.ej. para Ahorro Corriente sin detalle extra
