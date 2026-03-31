from pydantic import BaseModel

class ReloadResponseIn(BaseModel):
    success: bool
    rules_count: int
    message: str
    
    def to_dict(self):
        return self.model_dump()
