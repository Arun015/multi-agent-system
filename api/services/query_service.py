"""Service layer for query processing business logic."""
import logging
from typing import Dict
from api.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class QueryService:
    """
    Service layer for query processing.
    Handles business logic and orchestration.
    """
    
    def __init__(self):
        """Initialize the query service with orchestrator."""
        self.orchestrator = Orchestrator()
        logger.info("QueryService initialized")
    
    def process_query(self, query: str) -> str:
        """
        Process a user query through the multi-agent system.
        
        Args:
            query: User's query text
            
        Returns:
            Response string from the appropriate agent
            
        Raises:
            ValueError: If query is invalid
            RuntimeError: If processing fails
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            logger.info(f"Processing query: {query}")
            response = self.orchestrator.process_query(query)
            logger.info(f"Query processed successfully")
            return response
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise RuntimeError(f"Failed to process query: {str(e)}") from e

