"""LLM-based query routing using OpenAI and LangChain."""
from typing import Optional, Dict, Any, Literal
import logging
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
import os

logger = logging.getLogger(__name__)


class RoutingDecision(BaseModel):
    """Structured output for routing decisions."""
    agent: Literal["github", "linear", "out_of_scope"] = Field(
        description="Which agent should handle this query"
    )
    confidence: float = Field(
        description="Confidence score between 0 and 1",
        ge=0.0,
        le=1.0
    )
    reasoning: str = Field(
        description="Brief explanation of why this agent was chosen"
    )
    requires_clarification: bool = Field(
        default=False,
        description="Whether the query is ambiguous and needs clarification"
    )
    clarification_type: Optional[Literal["agent", "user"]] = Field(
        default=None,
        description="What type of clarification is needed"
    )


class LLMRouter:
    """LLM-powered router using OpenAI and LangChain."""
    
    def __init__(self):
        """Initialize the LLM router with Azure OpenAI."""
        # Check for Azure OpenAI configuration
        azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        if not all([azure_api_key, azure_endpoint, azure_deployment]):
            raise ValueError(
                "Azure OpenAI configuration required. Please set in .env:\n"
                "- AZURE_OPENAI_API_KEY\n"
                "- AZURE_OPENAI_ENDPOINT\n"
                "- AZURE_OPENAI_DEPLOYMENT\n"
                "- AZURE_OPENAI_API_VERSION (optional, defaults to 2024-02-15-preview)"
            )
        
        # Initialize Azure OpenAI with LangChain
        from langchain_openai import AzureChatOpenAI
        
        self.llm = AzureChatOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            temperature=0,  # Deterministic for routing
        )
        
        # Set up structured output parser
        self.parser = PydanticOutputParser(pydantic_object=RoutingDecision)
        
        # Create the routing prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "{query}")
        ])
        
        # Create the chain
        self.chain = self.prompt | self.llm | self.parser
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for routing."""
        return """You are an intelligent routing agent for a multi-agent system.

Your job is to analyze user queries and determine which specialized agent should handle them.

Available agents:
1. **github**: Handles GitHub-related queries
   - Repositories, pull requests, issues, stars, forks
   - Commits, branches, code reviews
   - GitHub-specific operations
   
2. **linear**: Handles Linear project management queries
   - Issues, tasks, projects
   - Teams, sprints, cycles
   - Linear-specific operations
   
3. **out_of_scope**: For queries unrelated to GitHub or Linear
   - Weather, general questions, unrelated topics

Guidelines:
- If the query mentions "GitHub", "repository", "pull request", "PR" → github
- If the query mentions "Linear", "issue", "task", "project", "sprint" → linear
- If both GitHub and Linear are equally possible → set requires_clarification=true
- If the query is about weather, general chat, etc → out_of_scope
- Be confident in your routing decisions
- Provide clear reasoning for your choice

Important:
- "issues" can mean GitHub issues OR Linear issues → check context
- If user doesn't specify which platform, mark as ambiguous

{format_instructions}"""
    
    def route(self, query: str) -> Dict[str, Any]:
        """
        Route a query using LLM reasoning.
        
        Args:
            query: The user's query
            
        Returns:
            Dictionary with routing decision
        """
        try:
            # Get format instructions for structured output
            format_instructions = self.parser.get_format_instructions()
            
            # Invoke the chain
            result: RoutingDecision = self.chain.invoke({
                "query": query,
                "format_instructions": format_instructions
            })
            
            logger.info(f"LLM Routing - Agent: {result.agent}, "
                       f"Confidence: {result.confidence}, "
                       f"Reasoning: {result.reasoning}")
            
            # Convert to dict for consistency
            return {
                'agent': result.agent if result.agent != 'out_of_scope' else None,
                'confidence': result.confidence,
                'reason': result.reasoning,
                'ambiguous': result.requires_clarification,
                'clarification_type': result.clarification_type
            }
            
        except Exception as e:
            logger.error(f"LLM routing error: {e}")
            raise RuntimeError(f"LLM routing failed: {str(e)}") from e



