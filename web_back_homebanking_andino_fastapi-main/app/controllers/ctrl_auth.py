"""Controlador de autenticacion: reglas de login y emision de JWT."""
from fastapi import HTTPException, status
from sqlalchemy.engine import Connection

from app.core.cfg_config import settings
from app.core.cfg_security import crear_access_token, verificar_password
from app.repositories import repo_auth


def _rechazar_login_fallido(conn: Connection, pkusuario: int) -> None:
    intentos = repo_auth.registrar_login_fallido(conn, pkusuario)
    restantes = max(0, repo_auth.MAX_INTENTOS - intentos)
    detalle = "Credenciales invalidas"
    if restantes == 0:
        detalle = "Credenciales invalidas. Usuario bloqueado por exceder intentos."
    else:
        detalle = f"Credenciales invalidas. Intentos restantes: {restantes}"
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=detalle)


def login(conn: Connection, username: str, dni: str, password: str) -> dict:
    usuario = repo_auth.buscar_usuario_por_username(conn, username)
    if usuario is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Credenciales invalidas")

    if usuario["activo"] != "S":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Usuario inactivo")
    if usuario["bloqueado"] == "S":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuario bloqueado por intentos fallidos. Contacte a la caja.",
        )

    if dni.strip() != (usuario.get("dni") or "").strip():
        _rechazar_login_fallido(conn, usuario["pkusuario"])

    if not verificar_password(password, usuario["password_hash"]):
        _rechazar_login_fallido(conn, usuario["pkusuario"])

    repo_auth.registrar_login_exitoso(conn, usuario["pkusuario"])

    token = crear_access_token(
        {
            "sub": usuario["codcliente"],
            "tipo": "cliente",
            "pkcliente": usuario["pkcliente"],
            "nombre": usuario["nomcliente"],
            "sexo": (usuario.get("sexo") or "").strip(),
        }
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "expires_in_min": settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        "cliente": {
            "codcliente": usuario["codcliente"],
            "nombre": usuario["nomcliente"],
            "pkcliente": usuario["pkcliente"],
            "sexo": (usuario.get("sexo") or "").strip(),
        },
    }
