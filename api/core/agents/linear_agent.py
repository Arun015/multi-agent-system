"""Linear Agent implementation."""
from typing import Dict, Any, Optional
import requests
from .base_agent import BaseAgent
from config import config


class LinearAgent(BaseAgent):
    """Agent for handling Linear-related queries."""
    
    def __init__(self):
        super().__init__("Linear")
        self.api_base = "https://api.linear.app/graphql"
    
    def execute(self, query: str, user_id: str, context: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a Linear query for a specific user.
        
        Args:
            query: The user's query
            user_id: The user identifier ("user1" or "user2")
            context: Additional context including action type
            
        Returns:
            Formatted response string
        """
        user_config = config.get_user_config(user_id)
        
        if not user_config.linear_api_key:
            return f"Linear API key not configured for {user_config.display_name}"
        
        # Extract action from context
        action = context.get('action', 'unknown') if context else 'unknown'
        
        try:
            if 'issue' in query.lower():
                result = self._get_issues(user_config.linear_api_key, user_config.display_name, query)
            elif 'project' in query.lower():
                result = self._get_projects(user_config.linear_api_key)
            elif 'team' in query.lower():
                result = self._get_teams(user_config.linear_api_key)
            else:
                result = self._get_issues(user_config.linear_api_key, user_config.display_name, query)
            
            self.log_execution(user_id, action, result)
            return result
            
        except Exception as e:
            error_msg = f"Error fetching Linear data: {str(e)}"
            self.logger.error(error_msg)
            return error_msg
    
    def _execute_graphql(self, api_key: str, query: str, variables: Optional[Dict] = None) -> Dict:
        """Execute a GraphQL query against Linear API."""
        headers = {
            'Authorization': api_key,
            'Content-Type': 'application/json'
        }
        
        payload = {
            'query': query,
            'variables': variables or {}
        }
        
        response = requests.post(self.api_base, headers=headers, json=payload)
        response.raise_for_status()
        
        data = response.json()
        
        if 'errors' in data:
            raise Exception(f"GraphQL errors: {data['errors']}")
        
        return data.get('data', {})
    
    def _get_issues(self, api_key: str, display_name: str, query: str) -> str:
        """Get issues assigned to the user."""
        # Determine state filter
        state_filter = None
        if 'in progress' in query.lower() or 'progress' in query.lower():
            state_filter = 'started'
        elif 'todo' in query.lower() or 'to do' in query.lower():
            state_filter = 'unstarted'
        elif 'done' in query.lower() or 'completed' in query.lower():
            state_filter = 'completed'
        elif 'high priority' in query.lower() or 'urgent' in query.lower():
            state_filter = None  # We'll handle priority separately
        
        # Build GraphQL query
        gql_query = """
        query GetIssues($filter: IssueFilter) {
            issues(filter: $filter, first: 20) {
                nodes {
                    id
                    identifier
                    title
                    state {
                        name
                        type
                    }
                    priority
                    assignee {
                        name
                        displayName
                    }
                    team {
                        name
                    }
                }
            }
            viewer {
                id
                name
                displayName
            }
        }
        """
        
        # Get viewer info first to filter by assignee
        data = self._execute_graphql(api_key, gql_query, {'filter': {}})
        
        viewer_id = data.get('viewer', {}).get('id')
        viewer_name = data.get('viewer', {}).get('displayName') or data.get('viewer', {}).get('name')
        
        # Now query with assignee filter
        variables = {
            'filter': {
                'assignee': {'id': {'eq': viewer_id}}
            }
        }
        
        if state_filter:
            if state_filter == 'started':
                variables['filter']['state'] = {'type': {'eq': 'started'}}
            elif state_filter == 'unstarted':
                variables['filter']['state'] = {'type': {'eq': 'unstarted'}}
            elif state_filter == 'completed':
                variables['filter']['state'] = {'type': {'eq': 'completed'}}
        
        data = self._execute_graphql(api_key, gql_query, variables)
        
        issues = data.get('issues', {}).get('nodes', [])
        
        # Filter by priority if requested
        if 'high priority' in query.lower() or 'urgent' in query.lower():
            issues = [i for i in issues if i.get('priority', 0) >= 1]  # Priority 1 (Urgent) or higher
        
        if not issues:
            state_desc = state_filter if state_filter else 'assigned'
            priority_desc = ' high priority' if 'high priority' in query.lower() else ''
            return f"{display_name} has no{priority_desc} {state_desc} issues."
        
        state_desc = ''
        if state_filter == 'started':
            state_desc = ' in progress'
        elif state_filter == 'unstarted':
            state_desc = ' todo'
        elif state_filter == 'completed':
            state_desc = ' completed'
        
        priority_desc = ' high priority' if 'high priority' in query.lower() else ''
        
        result = f"{display_name} has {len(issues)}{priority_desc}{state_desc} issue(s):\n\n"
        
        for idx, issue in enumerate(issues, 1):
            identifier = issue.get('identifier', 'N/A')
            title = issue.get('title', 'No title')
            state_name = issue.get('state', {}).get('name', 'Unknown')
            team_name = issue.get('team', {}).get('name', 'No team')
            priority = issue.get('priority', 0)
            priority_label = {0: 'No priority', 1: 'Urgent', 2: 'High', 3: 'Medium', 4: 'Low'}.get(priority, 'Unknown')
            
            result += f"{idx}. [{identifier}] {title} ({state_name}) - {team_name}\n"
            if priority > 0:
                result += f"   Priority: {priority_label}\n"
        
        return result.strip()
    
    def _get_projects(self, api_key: str) -> str:
        """Get projects accessible to the user."""
        gql_query = """
        query GetProjects {
            projects(first: 20) {
                nodes {
                    id
                    name
                    description
                    state
                    progress
                    teams {
                        nodes {
                            name
                        }
                    }
                }
            }
            viewer {
                displayName
                name
            }
        }
        """
        
        data = self._execute_graphql(api_key, gql_query)
        
        projects = data.get('projects', {}).get('nodes', [])
        viewer = data.get('viewer', {})
        display_name = viewer.get('displayName') or viewer.get('name', 'User')
        
        if not projects:
            return f"{display_name} has no accessible projects."
        
        result = f"{display_name} has access to {len(projects)} project(s):\n\n"
        
        for idx, project in enumerate(projects, 1):
            name = project.get('name', 'Unnamed')
            description = project.get('description', 'No description')
            state = project.get('state', 'Unknown')
            progress = project.get('progress', 0)
            teams = project.get('teams', {}).get('nodes', [])
            team_names = ', '.join([t['name'] for t in teams]) if teams else 'No teams'
            
            result += f"{idx}. {name} - {description}\n"
            result += f"   State: {state} | Progress: {progress:.0%} | Teams: {team_names}\n"
        
        return result.strip()
    
    def _get_teams(self, api_key: str) -> str:
        """Get teams accessible to the user."""
        gql_query = """
        query GetTeams {
            teams(first: 20) {
                nodes {
                    id
                    name
                    key
                    description
                    private
                }
            }
            viewer {
                displayName
                name
            }
        }
        """
        
        data = self._execute_graphql(api_key, gql_query)
        
        teams = data.get('teams', {}).get('nodes', [])
        viewer = data.get('viewer', {})
        display_name = viewer.get('displayName') or viewer.get('name', 'User')
        
        if not teams:
            return f"{display_name} has no accessible teams."
        
        result = f"{display_name} has access to {len(teams)} team(s):\n\n"
        
        for idx, team in enumerate(teams, 1):
            name = team.get('name', 'Unnamed')
            key = team.get('key', 'N/A')
            description = team.get('description', 'No description')
            private = team.get('private', False)
            privacy = 'Private' if private else 'Public'
            
            result += f"{idx}. {name} ({key}) - {description}\n"
            result += f"   {privacy}\n"
        
        return result.strip()
    
    def get_capabilities(self) -> list[str]:
        """Get list of capabilities this agent supports."""
        return [
            'linear', 'issue', 'issues', 'project', 'projects',
            'team', 'teams', 'task', 'tasks'
        ]

