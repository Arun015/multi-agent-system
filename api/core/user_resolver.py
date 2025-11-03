"""User resolution logic for multi-agent system."""
from typing import Optional, Dict, Any
import logging
import re
from config import config

logger = logging.getLogger(__name__)


class UserResolver:
    """Resolves which user a query is about."""
    
    def __init__(self):
        self.config = config
        self.user_patterns = self._build_user_patterns()
    
    def _build_user_patterns(self) -> Dict[str, list]:
        """Build regex patterns for identifying users."""
        patterns = {
            'user1': [
                re.compile(rf'\b{re.escape(self.config.user1.display_name.lower())}\b'),
                re.compile(rf'\b{re.escape(self.config.user1.display_name.lower())}\'s\b'),
                re.compile(rf'\b{re.escape(self.config.user1.username.lower())}\b'),
                re.compile(rf'\b{re.escape(self.config.user1.username.lower())}\'s\b'),
            ],
            'user2': [
                re.compile(rf'\b{re.escape(self.config.user2.display_name.lower())}\b'),
                re.compile(rf'\b{re.escape(self.config.user2.display_name.lower())}\'s\b'),
                re.compile(rf'\b{re.escape(self.config.user2.username.lower())}\b'),
                re.compile(rf'\b{re.escape(self.config.user2.username.lower())}\'s\b'),
            ]
        }
        return patterns
    
    def resolve(self, query: str) -> Dict[str, Any]:
        """Resolve which user the query is about."""
        query_lower = query.lower()
        
        user1_matches = sum(1 for pattern in self.user_patterns['user1'] if pattern.search(query_lower))
        user2_matches = sum(1 for pattern in self.user_patterns['user2'] if pattern.search(query_lower))
        
        logger.info(f"User resolution - User1: {user1_matches}, User2: {user2_matches}")
        
        if user1_matches > 0 and user2_matches == 0:
            return {
                'user_id': 'user1',
                'user_name': self.config.user1.display_name,
                'confidence': user1_matches,
                'reason': f'Query mentions {self.config.user1.display_name}'
            }
        elif user2_matches > 0 and user1_matches == 0:
            return {
                'user_id': 'user2',
                'user_name': self.config.user2.display_name,
                'confidence': user2_matches,
                'reason': f'Query mentions {self.config.user2.display_name}'
            }
        elif user1_matches > 0 and user2_matches > 0:
            return {
                'user_id': None,
                'user_name': None,
                'confidence': 0,
                'reason': 'Multiple users mentioned',
                'clarification_needed': True
            }
        else:
            return {
                'user_id': None,
                'user_name': None,
                'confidence': 0,
                'reason': 'No user mentioned',
                'clarification_needed': True
            }
    
    def get_clarification_message(self, agent_name: str) -> str:
        """Get a clarification message for ambiguous queries."""
        users = self.config.get_all_users()
        user_names = [user.display_name for user in users.values()]
        
        if len(user_names) == 0:
            return "No users configured in the system."
        elif len(user_names) == 1:
            return f"Only {user_names[0]} is configured."
        elif len(user_names) == 2:
            return f"Whose {agent_name} data? {user_names[0]}'s or {user_names[1]}'s?"
        else:
            names_str = ", ".join(user_names[:-1]) + f", or {user_names[-1]}"
            return f"Whose {agent_name} data? {names_str}?"
    
    def resolve_clarification_response(self, response: str) -> Optional[str]:
        """Resolve a user's clarification response."""
        response_lower = response.lower()
        
        for user_id, user_config in self.config.get_all_users().items():
            if (user_config.display_name.lower() in response_lower or 
                user_config.username.lower() in response_lower):
                return user_id
        
        number_words = {
            '1': 'user1', 'first': 'user1', 'one': 'user1',
            '2': 'user2', 'second': 'user2', 'two': 'user2',
            '3': 'user3', 'third': 'user3', 'three': 'user3',
            '4': 'user4', 'fourth': 'user4', 'four': 'user4',
            '5': 'user5', 'fifth': 'user5', 'five': 'user5',
        }
        
        for number, user_id in number_words.items():
            if number in response_lower and user_id in self.config.users:
                return user_id
        
        return None

