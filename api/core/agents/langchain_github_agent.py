"""LangChain-powered GitHub agent with tool use."""
from typing import Dict, Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
import os
import logging
from .github_agent import GitHubAgent as BaseGitHubAgent

logger = logging.getLogger(__name__)


class LangChainGitHubAgent:
    """LangChain-powered GitHub agent using function calling."""
    
    def __init__(self):
        """Initialize the LangChain GitHub agent."""
        self.base_agent = BaseGitHubAgent()
        
        # Check for Azure OpenAI configuration
        azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        
        if not all([azure_api_key, azure_endpoint, azure_deployment]):
            raise ValueError(
                "Azure OpenAI configuration required for LangChain agents. "
                "Please set in your .env file."
            )
        
        # Initialize Azure OpenAI LLM
        from langchain_openai import AzureChatOpenAI
        
        self.llm = AzureChatOpenAI(
            azure_deployment=azure_deployment,
            azure_endpoint=azure_endpoint,
            api_key=azure_api_key,
            api_version=os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview'),
            temperature=0,
        )
        
        # Create tools
        self.tools = self._create_tools()
        
        # Create prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", self._get_system_prompt()),
            ("user", "{input}"),
            ("assistant", "{agent_scratchpad}")
        ])
        
        # Create agent
        try:
            agent = create_openai_functions_agent(
                llm=self.llm,
                tools=self.tools,
                prompt=prompt
            )
            
            self.agent_executor = AgentExecutor(
                agent=agent,
                tools=self.tools,
                verbose=True,
                max_iterations=3
            )
        except Exception as e:
            logger.error(f"Failed to create LangChain agent: {e}")
            self.agent_executor = None
    
    def _get_system_prompt(self) -> str:
        """Get the system prompt for the agent."""
        return """You are a GitHub assistant that can fetch information about repositories, pull requests, issues, and starred repositories.

Use the available tools to answer user queries about GitHub data.

Guidelines:
- Always use the appropriate tool for the task
- Provide clear, formatted responses
- If data is not found, explain clearly
- Format lists with numbers for readability
- For starred repositories, use the get_user_starred_repos tool
"""
    
    def _create_tools(self):
        """Create LangChain tools for GitHub operations."""
        
        @tool
        def get_user_repositories(user_id: str, username: str) -> str:
            """
            Get list of repositories for a GitHub user.
            
            Args:
                user_id: The user ID (user1 or user2)
                username: The GitHub username
            """
            try:
                from config import config
                user_config = config.get_user_config(user_id)
                return self.base_agent._get_repositories(
                    user_config.github_token,
                    username
                )
            except Exception as e:
                return f"Error fetching repositories: {str(e)}"
        
        @tool
        def get_user_pull_requests(user_id: str, username: str, state: str = "open") -> str:
            """
            Get pull requests for a GitHub user.
            
            Args:
                user_id: The user ID (user1 or user2)
                username: The GitHub username
                state: PR state (open, closed, all)
            """
            try:
                from config import config
                user_config = config.get_user_config(user_id)
                query = f"{state} pull requests"
                return self.base_agent._get_pull_requests(
                    user_config.github_token,
                    username,
                    query
                )
            except Exception as e:
                return f"Error fetching pull requests: {str(e)}"
        
        @tool
        def get_user_issues(user_id: str, username: str, state: str = "open") -> str:
            """
            Get issues for a GitHub user.
            
            Args:
                user_id: The user ID (user1 or user2)
                username: The GitHub username
                state: Issue state (open, closed, all)
            """
            try:
                from config import config
                user_config = config.get_user_config(user_id)
                query = f"{state} issues"
                return self.base_agent._get_issues(
                    user_config.github_token,
                    username,
                    query
                )
            except Exception as e:
                return f"Error fetching issues: {str(e)}"
        
        @tool
        def get_user_starred_repos(user_id: str, username: str) -> str:
            """
            Get starred repositories for a GitHub user.
            
            Args:
                user_id: The user ID (user1 or user2)
                username: The GitHub username
            """
            try:
                from config import config
                user_config = config.get_user_config(user_id)
                return self.base_agent._get_starred_repos(
                    user_config.github_token,
                    username
                )
            except Exception as e:
                return f"Error fetching starred repositories: {str(e)}"
        
        return [get_user_repositories, get_user_pull_requests, get_user_issues, get_user_starred_repos]
    
    def execute(self, query: str, user_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a query using LangChain agent.
        
        Args:
            query: The user's query
            user_id: The user identifier
            context: Additional context
            
        Returns:
            Agent response
        """
        try:
            from config import config
            user_config = config.get_user_config(user_id)
            
            # Enhance query with user context
            enhanced_query = f"""User: {user_config.display_name} (username: {user_config.username})
User ID: {user_id}
Query: {query}

Please fetch the requested GitHub information for this user."""
            
            # Execute agent
            result = self.agent_executor.invoke({"input": enhanced_query})
            
            return result.get('output', 'No response generated')
            
        except Exception as e:
            logger.error(f"LangChain agent execution error: {e}")
            raise RuntimeError(f"LangChain agent failed to execute query: {str(e)}") from e

