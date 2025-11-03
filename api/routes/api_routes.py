"""API routes for all endpoints."""
import os
import logging
from fastapi import APIRouter, HTTPException, Depends
from api.dto import QueryRequest, QueryResponse, HealthResponse
from api.services import QueryService

logger = logging.getLogger(__name__)

router = APIRouter()

_query_service = None


def get_query_service() -> QueryService:
    """Dependency injection for QueryService."""
    global _query_service
    if _query_service is None:
        _query_service = QueryService()
    return _query_service


@router.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """Health check endpoint."""
    try:
        llm_enabled = bool(
            os.getenv('AZURE_OPENAI_API_KEY') and 
            os.getenv('AZURE_OPENAI_ENDPOINT') and 
            os.getenv('AZURE_OPENAI_DEPLOYMENT')
        )
        
        return HealthResponse(
            status="healthy",
            message="System is operational",
            llm_enabled=llm_enabled
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Health check failed")


@router.post("/query", response_model=QueryResponse, tags=["Query"])
async def process_query(
    request: QueryRequest,
    service: QueryService = Depends(get_query_service)
):
    """Process a user query through the multi-agent system."""
    try:
        response = service.process_query(query=request.query)
        return QueryResponse(response=response)
    except ValueError as e:
        logger.warning(f"Invalid query: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

