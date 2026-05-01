from pydantic import BaseModel
from typing import Optional

class AreaCreate(BaseModel):
    """Modelo para crear un área nueva."""

    __entity_name__ = "areas"

    id: Optional[int] = None
    nombre: str
    descripcion: str

    def to_dict(self) -> dict:
        return {
            "ID": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AreaCreate":
        return cls(
            id=data.get("id", data.get("ID")),
            nombre=data.get("nombre", ""),
            descripcion=data.get("descripcion", ""),
        )

    @classmethod
    def get_fields(cls) -> dict:
        return {
            "id": "INTEGER PRIMARY KEY",
            "nombre": "VARCHAR(150) NOT NULL",
            "descripcion": "VARCHAR(255)",
        }


class AreaOut(BaseModel):
    """Modelo de salida para área."""

    __entity_name__ = "areas"

    id: int
    nombre: str
    descripcion: str = ""

    def to_dict(self) -> dict:
        return {
            "ID": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AreaOut":
        return cls(
            id=data.get("id", data.get("ID")),
            nombre=data.get("nombre", ""),
            descripcion=data.get("descripcion", ""),
        )


class AreaUpdate(BaseModel):
    """Modelo para actualizar datos de un área."""

    id: int
    nombre: str
    descripcion: str
