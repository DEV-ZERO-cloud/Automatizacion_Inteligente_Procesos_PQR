from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class HistoryCreate(BaseModel):
    """Modelo para crear un registro de historial de PQR."""

    __entity_name__ = "historial"

    id: Optional[int] = None
    pqr_id: int
    usuario_id: Optional[int] = None
    accion: str
    detalle: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pqr_id": self.pqr_id,
            "usuario_id": self.usuario_id,
            "accion": self.accion,
            "detalle": self.detalle,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryCreate":
        return cls(
            id=data.get("id"),
            pqr_id=data.get("pqr_id"),
            usuario_id=data.get("usuario_id"),
            accion=data.get("accion", ""),
            detalle=data.get("detalle"),
            created_at=data.get("created_at"),
        )


class HistoryOut(BaseModel):
    """Modelo de salida para historial."""

    __entity_name__ = "historial"

    id: int
    pqr_id: int
    usuario_id: Optional[int] = None
    accion: str
    detalle: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pqr_id": self.pqr_id,
            "usuario_id": self.usuario_id,
            "accion": self.accion,
            "detalle": self.detalle,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "HistoryOut":
        return cls(
            id=data.get("id"),
            pqr_id=data.get("pqr_id"),
            usuario_id=data.get("usuario_id"),
            accion=data.get("accion", ""),
            detalle=data.get("detalle"),
            created_at=data.get("created_at"),
        )


class HistoryUpdate(BaseModel):
    """Modelo para actualizar registro de historial."""

    id: int
    accion: Optional[str] = None
    detalle: Optional[str] = None

