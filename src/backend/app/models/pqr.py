from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PQRCreate(BaseModel):
    __entity_name__ = "PQR"

    ID: Optional[int] = None
    titulo: str
    descripcion: str
    tipo: str
    categoria: Optional[str] = None
    prioridad: Optional[str] = None
    estado: str = "pendiente"
    area_id: Optional[int] = None
    usuario_id: Optional[int] = None
    operador_id: Optional[int] = None
    supervisor_id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "ID": self.ID,
            "titulo": self.titulo,
            "descripcion": self.descripcion,
            "tipo": self.tipo,
            "categoria": self.categoria,
            "prioridad": self.prioridad,
            "estado": self.estado,
            "area_id": self.area_id,
            "usuario_id": self.usuario_id,
            "operador_id": self.operador_id,
            "supervisor_id": self.supervisor_id,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PQRCreate":
        return cls(
            ID=data.get("ID", data.get("id")),
            titulo=data.get("titulo", ""),
            descripcion=data.get("descripcion", ""),
            tipo=data.get("tipo", "peticion"),
            categoria=data.get("categoria"),
            prioridad=data.get("prioridad"),
            estado=data.get("estado", "pendiente"),
            area_id=data.get("area_id"),
            usuario_id=data.get("usuario_id"),
            operador_id=data.get("operador_id"),
            supervisor_id=data.get("supervisor_id"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )


class PQROut(PQRCreate):
    pass


class PQRUpdate(BaseModel):
    titulo: Optional[str] = None
    descripcion: Optional[str] = None
    tipo: Optional[str] = None
    categoria: Optional[str] = None
    prioridad: Optional[str] = None
    estado: Optional[str] = None
    area_id: Optional[int] = None
    usuario_id: Optional[int] = None
    operador_id: Optional[int] = None
    supervisor_id: Optional[int] = None
