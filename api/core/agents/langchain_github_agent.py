"""LangChain-powered GitHub agent with tool use."""
from typing import Dict, Any, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import AzureChatOpenAI
import os
import logging
import requests
from config import config

logger = logging.getLogger(__name__)


class LangChainGitHubAgent:
    """LangChain-powered GitHub agent using function calling."""
    
    def __init__(self):
        """Initialize the LangChain GitHub agent."""
        self.api_base = "https://api.github.com"
        
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
                user_config = config.get_user_config(user_id)
                return self._get_repositories(
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
                user_config = config.get_user_config(user_id)
                query = f"{state} pull requests"
                return self._get_pull_requests(
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
                user_config = config.get_user_config(user_id)
                query = f"{state} issues"
                return self._get_issues(
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
                user_config = config.get_user_config(user_id)
                return self._get_starred_repos(
                    user_config.github_token,
                    username
                )
            except Exception as e:
                return f"Error fetching starred repositories: {str(e)}"
        
        return [get_user_repositories, get_user_pull_requests, get_user_issues, get_user_starred_repos]
    
    def _get_repositories(self, token: str, username: str) -> str:
        """Get repositories for the user."""
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"{self.api_base}/users/{username}/repos"
        params = {
            'sort': 'updated',
            'per_page': 20
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        repos = response.json()
        
        if not repos:
            user_config = config.get_user_config('user1' if username == config.user1.username else 'user2')
            return f"{user_config.display_name} has no repositories."
        
        user_config = config.get_user_config('user1' if username == config.user1.username else 'user2')
        result = f"{user_config.display_name} has {len(repos)} repositor{'y' if len(repos) == 1 else 'ies'}:\n\n"
        
        for idx, repo in enumerate(repos, 1):
            name = repo['name']
            description = repo.get('description', 'No description')
            stars = repo.get('stargazers_count', 0)
            result += f"{idx}. {name} - {description} (⭐ {stars})\n"
        
        return result.strip()
    
    def _get_pull_requests(self, token: str, username: str, query: str) -> str:
        """Get pull requests for the user."""
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Determine state (open, closed, all)
        state = 'open'
        if 'closed' in query.lower():
            state = 'closed'
        elif 'all' in query.lower():
            state = 'all'
        
        # Search for PRs created by the user
        search_url = f"{self.api_base}/search/issues"
        params = {
            'q': f'type:pr author:{username} state:{state}',
            'sort': 'created',
            'order': 'desc',
            'per_page': 10
        }
        
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            user_config = config.get_user_config('user1' if username == config.user1.username else 'user2')
            return f"{user_config.display_name} has no {state} pull requests."
        
        user_config = config.get_user_config('user1' if username == config.user1.username else 'user2')
        result = f"{user_config.display_name} has {len(items)} {state} pull request(s):\n\n"
        
        for idx, item in enumerate(items, 1):
            pr_number = item['number']
            title = item['title']
            repo_name = item['repository_url'].split('/')[-1]
            result += f"{idx}. {title} in {repo_name} (#{pr_number})\n"
        
        return result.strip()
    
    def _get_issues(self, token: str, username: str, query: str) -> str:
        """Get issues for the user."""
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        # Determine state
        state = 'open'
        if 'closed' in query.lower():
            state = 'closed'
        elif 'all' in query.lower():
            state = 'all'
        
        # Search for issues assigned to or created by the user
        search_url = f"{self.api_base}/search/issues"
        params = {
            'q': f'type:issue involves:{username} state:{state}',
            'sort': 'created',
            'order': 'desc',
            'per_page': 10
        }
        
        response = requests.get(search_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            user_config = config.get_user_config('user1' if username == config.user1.username else 'user2')
            return f"{user_config.display_name} has no {state} issues."
        
        user_config = config.get_user_config('user1' if username == config.user1.username else 'user2')
        result = f"{user_config.display_name} has {len(items)} {state} issue(s):\n\n"
        
        for idx, item in enumerate(items, 1):
            issue_number = item['number']
            title = item['title']
            repo_name = item['repository_url'].split('/')[-1]
            result += f"{idx}. {title} in {repo_name} (#{issue_number})\n"
        
        return result.strip()
    
    def _get_starred_repos(self, token: str, username: str) -> str:
        """Get starred repositories for the user."""
        headers = {
            'Authorization': f'token {token}',
            'Accept': 'application/vnd.github.v3+json'
        }
        
        url = f"{self.api_base}/users/{username}/starred"
        params = {
            'per_page': 15
        }
        
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        repos = response.json()
        
        if not repos:
            user_config = config.get_user_config('user1' if username == config.user1.username else 'user2')
            return f"{user_config.display_name} has not starred any repositories."
        
        user_config = config.get_user_config('user1' if username == config.user1.username else 'user2')
        result = f"{user_config.display_name} has starred {len(repos)} repositor{'y' if len(repos) == 1 else 'ies'}:\n\n"
        
        for idx, repo in enumerate(repos, 1):
            name = repo['full_name']
            description = repo.get('description', 'No description')
            result += f"{idx}. {name} - {description}\n"
        
        return result.strip()
    
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

