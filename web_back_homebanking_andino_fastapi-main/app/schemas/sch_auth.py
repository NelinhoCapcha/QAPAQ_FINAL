"""Schemas pydantic para autenticación."""
from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    username: str = Field(..., examples=["usuario_cliente"])
    dni: str = Field(..., min_length=8, max_length=8, examples=["00000000"])
    password: str = Field(..., examples=["clave_cliente"])


class ClienteInfo(BaseModel):
    codcliente: str
    nombre: str
    pkcliente: int
    sexo: str | None = None


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in_min: int
    cliente: ClienteInfo
