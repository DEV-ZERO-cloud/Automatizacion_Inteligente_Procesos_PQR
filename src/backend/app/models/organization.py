from typing import Optional
from pydantic import BaseModel


class AreaCreate(BaseModel):
    """Modelo para crear un área nueva."""

    __entity_name__ = "AREAS"

    id: int
    nombre: str
    descripcion: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AreaCreate":
        return cls(**data)

    @classmethod
    def get_fields(cls) -> dict:
        return {
            "id": "INTEGER PRIMARY KEY",
            "nombre": "VARCHAR(150) NOT NULL",
            "descripcion": "VARCHAR(255)",
        }


class AreaOut(BaseModel):
    """Modelo de salida para área."""

    __entity_name__ = "AREAS"

    id: int
    nombre: str
    descripcion: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "AreaOut":
        return cls(**data)


class AreaUpdate(BaseModel):
    """Modelo para actualizar datos de un área."""

    id: int
    nombre: str
    descripcion: str
