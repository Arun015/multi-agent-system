"""Main orchestrator for multi-agent system."""
from typing import Dict, Any, Optional
import logging
import os
from .user_resolver import UserResolver
from .agents import GitHubAgent, LinearAgent

logger = logging.getLogger(__name__)


class Orchestrator:
    """Main orchestrator that coordinates agents and routing."""
    
    def __init__(self):
        """Initialize the orchestrator with LLM-powered components."""
        from .llm_router import LLMRouter
        self.router = LLMRouter()
        logger.info("Initialized with LLM-powered routing")
        
        self.user_resolver = UserResolver()
        
        from .agents.langchain_github_agent import LangChainGitHubAgent
        self.github_agent = LangChainGitHubAgent()
        logger.info("Initialized LangChain GitHub agent")
        
        self.linear_agent = LinearAgent()
        logger.info("Initialized Linear agent")
        
        self.pending_clarification = None
    
    def process_query(self, query: str) -> str:
        """Process a user query through the multi-agent system."""
        if self.pending_clarification:
            return self._handle_clarification_response(query)
        
        routing_result = self.router.route(query)
        agent_type = routing_result['agent']
        
        logger.info(f"Routing result: {routing_result}")
        
        if agent_type is None:
            return "I cannot answer this question"
        
        if routing_result.get('ambiguous'):
            self.pending_clarification = {
                'agent_type': None,
                'original_query': query,
                'routing_result': routing_result,
                'ambiguous_agent': True
            }
            return "Which platform? GitHub or Linear?"
        
        user_result = self.user_resolver.resolve(query)
        user_id = user_result.get('user_id')
        
        logger.info(f"User resolution result: {user_result}")
        
        if user_id is None or user_result.get('clarification_needed'):
            self.pending_clarification = {
                'agent_type': agent_type,
                'original_query': query,
                'routing_result': routing_result
            }
            
            agent_name = 'GitHub' if agent_type == 'github' else 'Linear'
            return self.user_resolver.get_clarification_message(agent_name)
        
        return self._execute_agent(agent_type, query, user_id, routing_result)
    
    def _handle_clarification_response(self, response: str) -> str:
        """Handle a user's response to a clarification request."""
        if not self.pending_clarification:
            return "I cannot answer this question"
        
        if self.pending_clarification.get('ambiguous_agent'):
            response_lower = response.lower()
            if 'github' in response_lower:
                agent_type = 'github'
            elif 'linear' in response_lower:
                agent_type = 'linear'
            else:
                return "I can help with that! Are you asking about GitHub or Linear?"
            
            self.pending_clarification['agent_type'] = agent_type
            self.pending_clarification['ambiguous_agent'] = False
            
            original_query = self.pending_clarification['original_query']
            user_result = self.user_resolver.resolve(original_query)
            user_id = user_result.get('user_id')
            
            if user_id is None or user_result.get('clarification_needed'):
                agent_name = 'GitHub' if agent_type == 'github' else 'Linear'
                return self.user_resolver.get_clarification_message(agent_name)
            else:
                self.pending_clarification = None
                routing_result = {'agent': agent_type}
                return self._execute_agent(agent_type, original_query, user_id, routing_result)
        
        user_id = self.user_resolver.resolve_clarification_response(response)
        
        if user_id is None:
            agent_name = 'GitHub' if self.pending_clarification['agent_type'] == 'github' else 'Linear'
            return self.user_resolver.get_clarification_message(agent_name)
        
        original_query = self.pending_clarification['original_query']
        agent_type = self.pending_clarification['agent_type']
        routing_result = self.pending_clarification['routing_result']
        
        self.pending_clarification = None
        
        return self._execute_agent(agent_type, original_query, user_id, routing_result)
    
    def _execute_agent(self, agent_type: str, query: str, user_id: str, routing_result: Dict[str, Any]) -> str:
        """Execute a query with the appropriate agent."""
        context = {
            'action': 'query',
            'routing_result': routing_result
        }
        
        try:
            if agent_type == 'github':
                logger.info(f"Executing GitHub agent for user {user_id}")
                return self.github_agent.execute(query, user_id, context)
            elif agent_type == 'linear':
                logger.info(f"Executing Linear agent for user {user_id}")
                return self.linear_agent.execute(query, user_id, context)
            else:
                return "I cannot answer this question"
        except Exception as e:
            logger.error(f"Error executing agent: {e}")
            return f"An error occurred while processing your request: {str(e)}"
    
    def reset_state(self):
        """Reset orchestrator state (useful for testing or new sessions)."""
        self.pending_clarification = None

