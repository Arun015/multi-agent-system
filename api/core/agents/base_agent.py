"""Base agent class for all specialized agents."""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class BaseAgent(ABC):
    """Base class for all agents in the system."""
    
    def __init__(self, name: str):
        """
        Initialize the base agent.
        
        Args:
            name: Name of the agent (e.g., "GitHub", "Linear")
        """
        self.name = name
        self.logger = logging.getLogger(f"{__name__}.{name}")
    
    @abstractmethod
    def execute(self, query: str, user_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a query for a specific user.
        
        Args:
            query: The user's query
            user_id: The user identifier (e.g., "user1", "user2")
            context: Additional context for the query
            
        Returns:
            Formatted response string
        """
        pass
    
    @abstractmethod
    def get_capabilities(self) -> list[str]:
        """
        Get list of capabilities this agent supports.
        
        Returns:
            List of capability keywords
        """
        pass
    
    def log_execution(self, user_id: str, action: str, result: str):
        """Log agent execution details."""
        self.logger.info(
            f"Agent: {self.name} | User: {user_id} | Action: {action} | Result: {result[:100]}..."
        )

