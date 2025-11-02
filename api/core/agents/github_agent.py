"""GitHub Agent implementation."""
from typing import Dict, Any, Optional
import requests
from .base_agent import BaseAgent
from config import config


class GitHubAgent(BaseAgent):
    """Agent for handling GitHub-related queries."""
    
    def __init__(self):
        super().__init__("GitHub")
        self.api_base = "https://api.github.com"
    
    def execute(self, query: str, user_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a GitHub query for a specific user.
        
        Args:
            query: The user's query
            user_id: The user identifier ("user1" or "user2")
            context: Additional context including action type
            
        Returns:
            Formatted response string
        """
        user_config = config.get_user_config(user_id)
        
        if not user_config.github_token:
            return f"GitHub token not configured for {user_config.display_name}"
        
        # Extract action from context
        action = context.get('action', 'unknown') if context else 'unknown'
        
        try:
            if 'pull request' in query.lower() or 'pr' in query.lower():
                result = self._get_pull_requests(user_config.github_token, user_config.username, query)
            elif 'repositor' in query.lower() or 'repo' in query.lower():
                result = self._get_repositories(user_config.github_token, user_config.username)
            elif 'issue' in query.lower():
                result = self._get_issues(user_config.github_token, user_config.username, query)
            elif 'star' in query.lower():
                result = self._get_starred_repos(user_config.github_token, user_config.username)
            else:
                result = self._get_repositories(user_config.github_token, user_config.username)
            
            self.log_execution(user_id, action, result)
            return result
            
        except Exception as e:
            error_msg = f"Error fetching GitHub data: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
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
    
    def get_capabilities(self) -> list[str]:
        """Get list of capabilities this agent supports."""
        return [
            'github', 'repository', 'repositories', 'repo', 'repos',
            'pull request', 'pull requests', 'pr', 'prs',
            'issue', 'issues', 'star', 'stars', 'starred'
        ]

