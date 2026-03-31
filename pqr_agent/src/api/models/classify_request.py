from pydantic import BaseModel, Field
from typing import Optional


class ClassifyRequestIn(BaseModel):
    id: Optional[int] = None
    pqr_id: int
    text: str

    def to_dict(self):
        return self.model_dump()
    
# Modelo de salida
class ClassifyRequestOut(ClassifyRequestIn):

    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)