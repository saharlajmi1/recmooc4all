from pydantic import BaseModel, model_validator
from typing import Optional
from fastapi import UploadFile

class TextQuerySchema(BaseModel):
    """Schema for text query parameters."""
    conversation_id: Optional[str] = None
    user_id: str
    query: str  # Text query, required

    @model_validator(mode="before")
    def validate_input(cls, values):
        """Validate the input parameters."""
        if not values.get("query"):
            raise ValueError("Text query is required")
        if not values.get("user_id"):
            raise ValueError("User ID is required")
        return values

class VoiceQuerySchema(BaseModel):
    """Schema for voice query parameters."""
    conversation_id: Optional[str] = None
    user_id: str
    audio_file: UploadFile  # Audio file, required

    class Config:
        arbitrary_types_allowed = True  # Allow UploadFile type

    @model_validator(mode="before")
    def validate_input(cls, values):
        """Validate the input parameters."""
        if not values.get("audio_file"):
            raise ValueError("Audio file is required")
        if not values.get("user_id"):
            raise ValueError("User ID is required")
        return values

class UnifiedQuerySchema(BaseModel):
    """Unified schema for text and voice query parameters."""
    conversation_id: Optional[str] = None
    user_id: str
    query: Optional[str] = None
    audio_file: Optional[UploadFile] = None

    class Config:
        arbitrary_types_allowed = True  # Allow UploadFile type

    @model_validator(mode="before")
    def validate_input(cls, values):
        """Validate the input parameters."""
        if not values.get("query") and not values.get("audio_file"):
            raise ValueError("Either text query or audio file must be provided")
        if not values.get("user_id"):
            raise ValueError("User ID is required")
        return values

class QueryResponseSchema(BaseModel):
    """Schema for query response."""
    query: str
    response: Optional[str] = None
    intent: Optional[str] = None
    conversation_id: str
    user_id: str
    refined_query: Optional[str] = None
    topic: Optional[str] = None
    level: Optional[str] = None
    num_courses: Optional[int] = None
