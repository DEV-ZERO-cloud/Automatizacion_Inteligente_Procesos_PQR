from pydantic import BaseModel
from typing import Dict, Optional

class HealthResponseIn(BaseModel):
    status: str
    model_loaded: bool
    rules_count: int
    version: str = "0.1.0"
    ml_status: Optional[Dict[str, bool]] = None

    def to_dict(self):
        return self.model_dump()