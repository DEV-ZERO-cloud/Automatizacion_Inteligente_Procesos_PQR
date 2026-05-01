from pydantic import BaseModel
from typing import List, Optional

class ClassifyResponseIn(BaseModel):
    id: Optional[int] = None
    categoria: Optional[str] = None
    tags: List[str] = []
    prioridad: Optional[str] = None
    rules_matched: List[str] = []
    area: Optional[str] = None
    source: str = "rules"
    confianza: Optional[float] = None
    requiere_revision: Optional[bool] = True
    model: str 

    def to_dict(self):
        return self.model_dump()


class ClassifyResponseOut(ClassifyResponseIn):
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)