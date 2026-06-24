"""Schemas pydantic para solicitud de crédito."""
from decimal import Decimal
from datetime import date
from typing import Literal

from pydantic import BaseModel, Field


class SolicitudCreditoRequest(BaseModel):
    montosolicitud: Decimal = Field(..., gt=0)
    plazo: int = Field(..., gt=0, description="Número de cuotas / meses")
    codtipocredito: Literal["ME", "CO"] = Field(..., description="ME=Microempresa, CO=Consumo")
    codactividadeconomica: str
    montoingresoneto: Decimal = Field(..., ge=0)


class SolicitudCreditoResponse(BaseModel):
    mensaje: str
    pksolicitud: int
    codsolicitud: str
    estado: str
    montosolicitud: Decimal
    plazo: int


class HistorialPrestamoOut(BaseModel):
    tipo_registro: str
    codigo: str
    fecha: date | None = None
    tipo_credito: str | None = None
    monto: Decimal | None = None
    plazo: int | None = None
    cuotas_pagadas: int | None = None
    cuotas_pendientes: int | None = None
    total_cuotas: int | None = None
    pago_pendiente: Decimal | None = None
    estado: str
    detalle: str | None = None
