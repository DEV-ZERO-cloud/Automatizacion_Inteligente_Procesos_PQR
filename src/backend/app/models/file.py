from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class FileCreate(BaseModel):
    """Modelo para crear un archivo adjunto a una PQR."""

    __entity_name__ = "archivos"

    id: Optional[int] = None
    pqr_id: int
    nombre: str
    ruta: Optional[str] = None
    tipo: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pqr_id": self.pqr_id,
            "nombre": self.nombre,
            "ruta": self.ruta,
            "tipo": self.tipo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileCreate":
        return cls(
            id=data.get("id"),
            pqr_id=data.get("pqr_id"),
            nombre=data.get("nombre", ""),
            ruta=data.get("ruta"),
            tipo=data.get("tipo"),
            created_at=data.get("created_at"),
        )


class FileOut(BaseModel):
    """Modelo de salida para archivo."""

    __entity_name__ = "archivos"

    id: int
    pqr_id: int
    nombre: str
    ruta: Optional[str] = None
    tipo: Optional[str] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pqr_id": self.pqr_id,
            "nombre": self.nombre,
            "ruta": self.ruta,
            "tipo": self.tipo,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "FileOut":
        return cls(
            id=data.get("id"),
            pqr_id=data.get("pqr_id"),
            nombre=data.get("nombre", ""),
            ruta=data.get("ruta"),
            tipo=data.get("tipo"),
            created_at=data.get("created_at"),
        )


class FileUpdate(BaseModel):
    """Modelo para actualizar información de archivo."""

    id: int
    nombre: Optional[str] = None
    ruta: Optional[str] = None
    tipo: Optional[str] = None

