"""Router de créditos (solicitar). Exige get_cliente."""
from fastapi import APIRouter, Depends
from sqlalchemy.engine import Connection

from app.controllers import ctrl_creditos
from app.core.cfg_auth import get_cliente
from app.core.cfg_database import get_db
from app.schemas.sch_creditos import (
    HistorialPrestamoOut,
    SolicitudCreditoRequest,
    SolicitudCreditoResponse,
)

router = APIRouter(prefix="/creditos", tags=["creditos"], dependencies=[Depends(get_cliente)])


@router.get("/historial", response_model=list[HistorialPrestamoOut])
def historial(
    conn: Connection = Depends(get_db),
    cliente: dict = Depends(get_cliente),
):
    return ctrl_creditos.historial(conn, cliente["pkcliente"])


@router.post("/solicitar", response_model=SolicitudCreditoResponse)
def solicitar(
    body: SolicitudCreditoRequest,
    conn: Connection = Depends(get_db),
    cliente: dict = Depends(get_cliente),
):
    return ctrl_creditos.solicitar(
        conn,
        cliente["pkcliente"],
        body.montosolicitud,
        body.plazo,
        body.codtipocredito,
        body.codactividadeconomica,
        body.montoingresoneto,
    )
