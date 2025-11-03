"""Service layer for query processing business logic."""
import logging
from api.core.orchestrator import Orchestrator

logger = logging.getLogger(__name__)


class QueryService:
    """Service layer for query processing."""
    
    def __init__(self):
        self.orchestrator = Orchestrator()
        logger.info("QueryService initialized")
    
    def process_query(self, query: str) -> str:
        """Process a user query through the multi-agent system."""
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")
        
        try:
            logger.info(f"Processing query: {query}")
            response = self.orchestrator.process_query(query)
            logger.info("Query processed successfully")
            return response
        except Exception as e:
            logger.error(f"Query processing failed: {e}")
            raise RuntimeError(f"Failed to process query: {str(e)}") from e

