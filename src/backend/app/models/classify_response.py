from pydantic import BaseModel
from typing import List, Optional

class ClassifyResponseIn(BaseModel):
    id: Optional[int] = None
    category: Optional[str] = None
    tags: List[str] = []
    priority: Optional[str] = None
    rules_matched: List[str] = []
    source: str = "rules"
    confidence: Optional[float] = None
    model: str 

    def to_dict(self):
        return self.model_dump()


class ClassifyResponseOut(ClassifyResponseIn):
    @classmethod
    def from_dict(cls, data: dict):
        return cls(**data)