"""Data Transfer Objects for query operations."""
from pydantic import BaseModel, Field
from typing import Optional


class QueryRequest(BaseModel):
    """Request DTO for query endpoint."""
    query: str = Field(..., description="User query to process", min_length=1)
    
    class Config:
        json_schema_extra = {
            "example": {
                "query": "Show me Alice's repositories"
            }
        }


class QueryResponse(BaseModel):
    """Response DTO for query endpoint."""
    response: str = Field(..., description="Agent response to the query")
    
    class Config:
        json_schema_extra = {
            "example": {
                "response": "Alice has 5 repositories..."
            }
        }


class HealthResponse(BaseModel):
    """Response DTO for health check."""
    status: str = Field(..., description="System health status")
    message: str = Field(..., description="Health status message")
    llm_enabled: bool = Field(..., description="Whether LLM features are available")
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "message": "System is operational",
                "llm_enabled": True
            }
        }


class ErrorResponse(BaseModel):
    """Response DTO for errors."""
    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    
    class Config:
        json_schema_extra = {
            "example": {
                "error": "ValidationError",
                "message": "Query cannot be empty",
                "detail": "The query field must contain at least 1 character"
            }
        }

