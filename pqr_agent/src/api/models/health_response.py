from pydantic import BaseModel
class HealthResponseIn(BaseModel):
    status: str
    model_loaded: bool
    rules_count: int
    version: str = "0.1.0"

    def to_dict(self):
        return self.model_dump()