from pydantic import BaseModel, Field
from typing import Optional, List, Any, Union
from datetime import datetime
import json

# JSON string'i List'e dönüştürmek için yardımcı fonksiyon
def parse_json_tags(v: Any) -> List[str]:
    if isinstance(v, list):
        return v
    if isinstance(v, str):
        try:
            return json.loads(v)
        except:
            return []
    return []

# Pydantic modelleri (istek/yanıt için)
class Post(BaseModel):
    id: int
    user_id: int
    title: Optional[str] = None
    content: str
    media_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    likes_count: Optional[int] = 0
    comments_count: Optional[int] = 0
    shares_count: Optional[int] = 0
    views_count: Optional[int] = 0
    visibility: Optional[str] = "public"
    tags: Optional[List[str]] = Field(default=None, description="Post etiketleri")
    allow_comments: Optional[bool] = True
    is_pinned: Optional[bool] = False
    community_id: Optional[int] = None
    
    # Tags için özel işleme yapıyoruz
    model_config = {
        "json_encoders": {
            List[str]: lambda v: json.dumps(v)
        }
    }
    
    @classmethod
    def model_validate(cls, obj, *args, **kwargs):
        if isinstance(obj, dict) and "tags" in obj and obj["tags"] is not None:
            obj["tags"] = parse_json_tags(obj["tags"])
        return super().model_validate(obj, *args, **kwargs)

class PostCreate(BaseModel):
    user_id: int
    title: Optional[str] = None
    content: str
    media_url: Optional[str] = None
    visibility: Optional[str] = "public"
    tags: Optional[List[str]] = None
    allow_comments: Optional[bool] = True
    community_id: Optional[int] = None

class UserTagInteraction(BaseModel):
    id: int
    user_id: int
    tag: str
    interaction_type: str
    interaction_count: int
    last_interacted_at: datetime

class UserTagInteractionCreate(BaseModel):
    user_id: int
    tag: str
    interaction_type: str
    interaction_count: Optional[int] = 1