from typing import Optional
from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """Modelo para crear un usuario nuevo."""

    __entity_name__ = "Usuario"

    ID: int
    identificacion: int
    nombre: str
    correo: str
    telefono: str
    contrasena: str
    rol_id: int
    area_id: int
    activo: Optional[int] = 1

    def to_dict(self) -> dict:
        return {
            "ID": self.ID,
            "identificacion": self.identificacion,
            "nombre": self.nombre,
            "correo": self.correo,
            "telefono": self.telefono,
            "contrasena": self.contrasena,
            "rol_id": self.rol_id,
            "area_id": self.area_id,
            "activo": self.activo,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserCreate":
        return cls(**data)

    @classmethod
    def get_fields(cls) -> dict:
        return {
            "ID": "INTEGER PRIMARY KEY",
            "identificacion": "INTEGER NOT NULL",
            "nombre": "VARCHAR(150) NOT NULL",
            "correo": "VARCHAR(200) NOT NULL",
            "telefono": "VARCHAR(20)",
            "contrasena": "VARCHAR(255) NOT NULL",
            "rol_id": "INTEGER NOT NULL",
            "area_id": "INTEGER NOT NULL",
            "activo": "TINYINT DEFAULT 1",
        }


class UserOut(BaseModel):
    """Modelo de salida para usuarios (sin contraseña)."""

    __entity_name__ = "Usuario"

    ID: int
    identificacion: int
    nombre: str
    correo: str
    telefono: Optional[str] = None
    rol_id: int
    area_id: int
    activo: Optional[int] = 1
    contrasena: Optional[str] = None  # Se incluye solo para autenticación interna

    def to_dict(self) -> dict:
        return {
            "ID": self.ID,
            "identificacion": self.identificacion,
            "nombre": self.nombre,
            "correo": self.correo,
            "telefono": self.telefono,
            "rol_id": self.rol_id,
            "area_id": self.area_id,
            "activo": self.activo,
            "contrasena": self.contrasena,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserOut":
        return cls(**data)


class UserUpdate(BaseModel):
    """Modelo para actualizar datos de un usuario."""

    ID: int
    nombre: str
    correo: str
    telefono: Optional[str] = None
    rol_id: int
    area_id: int
