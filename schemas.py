from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class EventCreate(BaseModel):
    category: str = Field(..., min_length=1, max_length=50, examples=["突然想起", "看到相关事物", "听到歌", "梦到"])
    note: Optional[str] = Field(None, max_length=500)
    intensity: int = Field(3, ge=1, le=5, description="想念强度 1-5")


class EventUpdate(BaseModel):
    category: Optional[str] = Field(None, min_length=1, max_length=50)
    note: Optional[str] = Field(None, max_length=500)
    intensity: Optional[int] = Field(None, ge=1, le=5)


class EventResponse(BaseModel):
    id: int
    category: str
    note: Optional[str]
    intensity: int
    created_at: datetime

    model_config = {"from_attributes": True}


class StatsResponse(BaseModel):
    total: int
    today: int
    this_week: int
    by_category: dict[str, int]
    by_intensity: dict[int, int]
    avg_intensity: float
