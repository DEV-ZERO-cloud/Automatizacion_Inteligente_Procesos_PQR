from pydantic import BaseModel
from typing import List, Optional

class ClassifyResponseIn(BaseModel):
    id: Optional[int]
    category: str  # Petición / Queja / Reclamo
    tags: List[str]  # Etiquetas asignadas
    priority: str  # baja / media / alta / crítica
    rules_matched: List[str]  # IDs de reglas aplicadas
    source: str  # Fuente de clasificación: rules / ml / hybrid
    confidence: float

    def to_dict(self):
        return self.model_dump()


class ClassifyResponseOut(ClassifyResponseIn):
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)