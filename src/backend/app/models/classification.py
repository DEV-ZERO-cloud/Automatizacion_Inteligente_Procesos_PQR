from typing import Optional
from pydantic import BaseModel


from datetime import datetime

# ── Modelos de Categoría ──────────────────────────────────────────────────────
class CategoryCreate(BaseModel):
    __entity_name__ = "categorias"

    id: int
    nombre: str

    def to_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre}

    @classmethod
    def from_dict(cls, data: dict) -> "CategoryCreate":
        return cls(**data)


class CategoryOut(BaseModel):
    __entity_name__ = "categorias"

    id: int
    nombre: str

    def to_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre}

    @classmethod
    def from_dict(cls, data: dict) -> "CategoryOut":
        return cls(**data)


class CategoryUpdate(BaseModel):
    id: int
    nombre: str


# ── Modelos de Prioridad ──────────────────────────────────────────────────────
class PriorityCreate(BaseModel):
    __entity_name__ = "prioridades"

    id: int
    nombre: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PriorityCreate":
        return cls(**data)


class PriorityOut(BaseModel):
    __entity_name__ = "prioridades"

    id: int
    nombre: str

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "nombre": self.nombre,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PriorityOut":
        return cls(**data)


class PriorityUpdate(BaseModel):
    id: int
    nombre: str


# ── Modelos de Clasificación ──────────────────────────────────────────────────
class ClassificationCreate(BaseModel):
    __entity_name__ = "clasificaciones"

    id: Optional[int] = None
    pqr_id: int
    modelo_version: str
    categoria_id: int
    prioridad_id: int
    confianza: float
    origen: str
    fue_corregida: bool
    validado_por: Optional[int] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pqr_id": self.pqr_id,
            "modelo_version": self.modelo_version,
            "categoria_id": self.categoria_id,
            "prioridad_id": self.prioridad_id,
            "confianza": self.confianza,
            "origen": self.origen,
            "fue_corregida": self.fue_corregida,
            "validado_por": self.validado_por,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ClassificationCreate":
        return cls(**data)


class ClassificationOut(BaseModel):
    __entity_name__ = "clasificaciones"

    id: int
    pqr_id: int
    modelo_version: str
    categoria_id: int
    prioridad_id: int
    confianza: float
    origen: str
    fue_corregida: bool
    validado_por: Optional[int] = None
    created_at: Optional[datetime] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "pqr_id": self.pqr_id,
            "modelo_version": self.modelo_version,
            "categoria_id": self.categoria_id,
            "prioridad_id": self.prioridad_id,
            "confianza": self.confianza,
            "origen": self.origen,
            "fue_corregida": self.fue_corregida,
            "validado_por": self.validado_por,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ClassificationOut":
        return cls(**data)


class ClassificationUpdate(BaseModel):
    id: int
    pqr_id: int
    modelo_version: str
    categoria_id: int
    prioridad_id: int
    confianza: float
    origen: str
    fue_corregida: bool
    validado_por: Optional[int] = None
    created_at: Optional[datetime] = None
