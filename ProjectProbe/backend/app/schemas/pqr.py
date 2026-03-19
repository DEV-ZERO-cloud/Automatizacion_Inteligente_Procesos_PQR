from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from enum import Enum


class TipoPQREnum(str, Enum):
    PETICION = "peticion"
    QUEJA = "queja"
    RECLAMO = "reclamo"


class EstadoPQREnum(str, Enum):
    CREADO = "creado"
    EN_PROCESO = "en_proceso"
    RESUELTO = "resuelto"


class ArchivoResponse(BaseModel):
    id: int
    filename: str
    filepath: str
    mimetype: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class HistorialResponse(BaseModel):
    id: int
    accion: str
    comentario: Optional[str]
    created_at: datetime
    usuario_nombre: Optional[str] = None

    class Config:
        from_attributes = True


class PQRBase(BaseModel):
    titulo: str
    descripcion: str
    tipo: TipoPQREnum = TipoPQREnum.PETICION


class PQRCreate(PQRBase):
    pass


class PQRUpdateEstado(BaseModel):
    estado: EstadoPQREnum
    comentario: Optional[str] = None


class PQRAsignar(BaseModel):
    supervisor_id: int


class PQRResponse(BaseModel):
    id: int
    titulo: str
    descripcion: str
    tipo: TipoPQREnum
    estado: EstadoPQREnum
    usuario_id: int
    supervisor_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    usuario_nombre: Optional[str] = None
    supervisor_nombre: Optional[str] = None
    archivos: List[ArchivoResponse] = []

    class Config:
        from_attributes = True


class PQRListResponse(BaseModel):
    id: int
    titulo: str
    tipo: TipoPQREnum
    estado: EstadoPQREnum
    created_at: datetime
    usuario_nombre: Optional[str] = None
    supervisor_nombre: Optional[str] = None

    class Config:
        from_attributes = True


class PQRDetalleResponse(PQRBase):
    id: int
    estado: EstadoPQREnum
    usuario_id: int
    supervisor_id: Optional[int]
    created_at: datetime
    updated_at: datetime
    usuario_nombre: Optional[str] = None
    supervisor_nombre: Optional[str] = None
    archivos: List[ArchivoResponse] = []
    historial: List[HistorialResponse] = []

    class Config:
        from_attributes = True


class EstadisticaResponse(BaseModel):
    total: int
    creados: int
    en_proceso: int
    resueltos: int
    por_tipo: dict
