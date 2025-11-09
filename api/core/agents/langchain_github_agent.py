"""LangChain-powered GitHub agent with tool use."""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain_openai import AzureChatOpenAI
import os
import logging
import requests
from config import config, UserConfig

logger = logging.getLogger(__name__)


@dataclass
class LangChainGitHubAgentConfig:
    """Configuration for LangChain GitHub Agent."""
    azure_api_key: str
    azure_endpoint: str
    azure_deployment: str
    azure_api_version: str = "2024-02-15-preview"
    temperature: float = 0
    verbose: bool = True
    max_iterations: int = 3
    user_configs: Optional[Dict[str, UserConfig]] = None
    
    def add_user(self, user_id: str, username: str, display_name: str, github_token: str) -> 'LangChainGitHubAgentConfig':
        """
        Add a user configuration. Returns self for method chaining.
        
        Args:
            user_id: The user ID (e.g., "user1", "user2")
            username: The GitHub username
            display_name: The display name
            github_token: The GitHub token
            
        Returns:
            self for method chaining
        """
        if self.user_configs is None:
            self.user_configs = {}
        self.user_configs[user_id] = UserConfig(
            username=username,
            display_name=display_name,
            github_token=github_token
        )
        return self
    
    @classmethod
    def from_env(cls) -> 'LangChainGitHubAgentConfig':
        """Create config from environment variables."""
        azure_api_key = os.getenv('AZURE_OPENAI_API_KEY')
        azure_endpoint = os.getenv('AZURE_OPENAI_ENDPOINT')
        azure_deployment = os.getenv('AZURE_OPENAI_DEPLOYMENT')
        azure_api_version = os.getenv('AZURE_OPENAI_API_VERSION', '2024-02-15-preview')
        
        if not all([azure_api_key, azure_endpoint, azure_deployment]):
            raise ValueError(
                "Azure OpenAI configuration required for LangChain agents. "
                "Please set AZURE_OPENAI_API_KEY, AZURE_OPENAI_ENDPOINT, and "
                "AZURE_OPENAI_DEPLOYMENT in your .env file or pass LangChainGitHubAgentConfig."
            )
        
        return cls(
            azure_api_key=azure_api_key,
            azure_endpoint=azure_endpoint,
            azure_deployment=azure_deployment,
            azure_api_version=azure_api_version
        )


class LangChainGitHubAgent:
    """LangChain-powered GitHub agent using function calling."""
    
    def __init__(self, config: Optional[LangChainGitHubAgentConfig] = None):
        """
        Initialize the LangChain GitHub agent.
        
        Args:
            config: Optional configuration object. If not provided, will load from environment variables.
        """
        self.api_base = "https://api.github.com"
        
        # Use provided config or load from environment
        if config is None:
            config = LangChainGitHubAgentConfig.from_env()
        
        self.config = config
        self.user_configs = config.user_configs
        
        # Initialize Azure OpenAI LLM
        self.llm = AzureChatOpenAI(
            azure_deployment=config.azure_deployment,
            azure_endpoint=config.azure_endpoint,
            api_key=config.azure_api_key,
            api_version=config.azure_api_version,
            temperature=config.temperature,
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
                verbose=config.verbose,
                max_iterations=config.max_iterations
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
    
    def _get_user_config(self, user_id: str) -> UserConfig:
        """Get user config by user_id from injected configs or global config."""
        if self.user_configs is not None:
            if user_id not in self.user_configs:
                raise ValueError(f"User ID '{user_id}' not found in provided config")
            return self.user_configs[user_id]
        # Fallback to global config for backward compatibility
        return config.get_user_config(user_id)
    
    def _get_user_config_by_username(self, username: str) -> UserConfig:
        """Get user config by username from injected configs or global config."""
        if self.user_configs is not None:
            # Only search in provided user_configs
            for user_config in self.user_configs.values():
                if user_config.username == username:
                    return user_config
            raise ValueError(f"User with username '{username}' not found in provided config")
        # Fallback to global config for backward compatibility
        if hasattr(config, 'user1') and config.user1.username == username:
            return config.user1
        if hasattr(config, 'user2') and config.user2.username == username:
            return config.user2
        raise ValueError(f"User with username '{username}' not found")
    
    def _create_tools(self):
        """Create LangChain tools for GitHub operations."""
        
        @tool
        def get_user_repositories(user_id: str) -> str:
            """
            Get list of repositories for a GitHub user.
            
            Args:
                user_id: The user ID (user1 or user2)
            """
            try:
                user_config = self._get_user_config(user_id)
                return self._get_repositories(
                    user_config.github_token,
                    user_config.username
                )
            except Exception as e:
                return f"Error fetching repositories: {str(e)}"
        
        @tool
        def get_user_pull_requests(user_id: str, state: str = "open") -> str:
            """
            Get pull requests for a GitHub user.
            
            Args:
                user_id: The user ID (user1 or user2)
                state: PR state (open, closed, all)
            """
            try:
                user_config = self._get_user_config(user_id)
                query = f"{state} pull requests"
                return self._get_pull_requests(
                    user_config.github_token,
                    user_config.username,
                    query
                )
            except Exception as e:
                return f"Error fetching pull requests: {str(e)}"
        
        @tool
        def get_user_issues(user_id: str, state: str = "open") -> str:
            """
            Get issues for a GitHub user.
            
            Args:
                user_id: The user ID (user1 or user2)
                state: Issue state (open, closed, all)
            """
            try:
                user_config = self._get_user_config(user_id)
                query = f"{state} issues"
                return self._get_issues(
                    user_config.github_token,
                    user_config.username,
                    query
                )
            except Exception as e:
                return f"Error fetching issues: {str(e)}"
        
        @tool
        def get_user_starred_repos(user_id: str) -> str:
            """
            Get starred repositories for a GitHub user.
            
            Args:
                user_id: The user ID (user1 or user2)
            """
            try:
                user_config = self._get_user_config(user_id)
                return self._get_starred_repos(
                    user_config.github_token,
                    user_config.username
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
        user_config = self._get_user_config_by_username(username)
        
        if not repos:
            return f"{user_config.display_name} has no repositories."
        
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
        user_config = self._get_user_config_by_username(username)
        
        if not items:
            return f"{user_config.display_name} has no {state} pull requests."
        
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
        user_config = self._get_user_config_by_username(username)
        
        if not items:
            return f"{user_config.display_name} has no {state} issues."
        
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
        user_config = self._get_user_config_by_username(username)
        
        if not repos:
            return f"{user_config.display_name} has not starred any repositories."
        
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
            if self.agent_executor is None:
                raise RuntimeError("Agent executor not initialized. Check Azure OpenAI configuration.")
            
            user_config = self._get_user_config(user_id)
            
            # Enhance query with user context
            enhanced_query = f"""User: {user_config.display_name} (username: {user_config.username})
User ID: {user_id}
Query: {query}

Please fetch the requested GitHub information for this user."""
            
            # Execute agent
            result = self.agent_executor.invoke({"input": enhanced_query})
            
            # Handle different return types from AgentExecutor
            if isinstance(result, dict):
                return result.get('output', 'No response generated')
            elif hasattr(result, 'return_values') and isinstance(result.return_values, dict):
                return result.return_values.get('output', 'No response generated')
            else:
                return str(result) if result else 'No response generated'
            
        except ValueError:
            # Preserve ValueError for user config errors (invalid user_id, etc.)
            raise
        except Exception as e:
            logger.error(f"LangChain agent execution error: {e}")
            raise RuntimeError(f"LangChain agent failed to execute query: {str(e)}") from e

