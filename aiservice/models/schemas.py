from pydantic import BaseModel
from typing import Optional, List, Any

class VoiceRequest(BaseModel):
    text:    str
    user_id: Optional[str] = "test_user"

    class Config:
        json_schema_extra = {
            "example": {
                "text":    "show me smartphones under 30000 with good camera",
                "user_id": "user_1",
            }
        }

class VoiceResponse(BaseModel):
    query:        str
    intent:       str
    preferences:  Optional[dict]
    reply:        str
    products:     List[Any]
    action_taken: str

class SearchRequest(BaseModel):
    query:    str
    budget:   Optional[float] = None
    category: Optional[str]   = None
    brand:    Optional[str]   = None
    top_k:    Optional[int]   = 5
