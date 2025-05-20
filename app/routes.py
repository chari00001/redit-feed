from fastapi import APIRouter, HTTPException, Depends, Query
from app.db import database
from app.models import Post, PostCreate, UserTagInteractionCreate
from typing import List
import json

router = APIRouter()

@router.post("/interact")
async def interact(interaction: UserTagInteractionCreate):
    query = """
        INSERT INTO User_Tag_Interactions (user_id, tag, interaction_type, interaction_count)
        VALUES (:user_id, :tag, :interaction_type, :interaction_count)
        RETURNING id, user_id, tag, interaction_type, interaction_count, last_interacted_at
    """
    result = await database.fetch_one(query, interaction.dict())
    return result

@router.get("/feed", response_model=List[Post])
async def feed(user_id: int = Query(...)):
    # Kullanıcıya önerilen gönderileri getir
    query = """
        SELECT *
        FROM posts
        WHERE visibility = 'public' OR 
              (visibility = 'private' AND user_id = :user_id)
        ORDER BY created_at DESC
        LIMIT 10
    """
    rows = await database.fetch_all(query, {"user_id": user_id})
    
    # JSON tags'i listye dönüştür
    results = []
    for row in rows:
        row_dict = dict(row)
        if "tags" in row_dict and isinstance(row_dict["tags"], str):
            try:
                row_dict["tags"] = json.loads(row_dict["tags"])
            except:
                row_dict["tags"] = []
        results.append(row_dict)
    
    return results 