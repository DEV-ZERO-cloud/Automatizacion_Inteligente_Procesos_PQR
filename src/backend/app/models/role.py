from pydantic import BaseModel
from typing import Optional


class RoleCreate(BaseModel):
    """Modelo para crear un rol nuevo."""

    __entity_name__ = "rol"

    id: int
    nombre: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RoleCreate":
        return cls(
            id=data.get("id"),
            nombre=data.get("nombre", ""),
        )


class RoleOut(BaseModel):
    """Modelo de salida para rol."""

    __entity_name__ = "rol"

    id: int
    nombre: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "RoleOut":
        return cls(
            id=data.get("id"),
            nombre=data.get("nombre", ""),
        )


class RoleUpdate(BaseModel):
    """Modelo para actualizar un rol."""

    id: int
    nombre: str
