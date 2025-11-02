"""Configuration management for multi-agent system."""
import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


@dataclass
class UserConfig:
    """Configuration for a single user."""
    username: str
    display_name: str
    github_token: Optional[str] = None
    linear_api_key: Optional[str] = None


class Config:
    """Main configuration class."""
    
    def __init__(self):
        # Load all configured users
        self.users = {}
        self.display_name_to_user = {}
        
        # Load users from environment variables
        user_index = 1
        while True:
            github_username = os.getenv(f'GITHUB_USERNAME_USER{user_index}')
            if not github_username:
                break
            
            user_id = f'user{user_index}'
            display_name = os.getenv(f'USER{user_index}_DISPLAY_NAME', f'User{user_index}')
            
            self.users[user_id] = UserConfig(
                username=github_username,
                display_name=display_name,
                github_token=os.getenv(f'GITHUB_TOKEN_USER{user_index}'),
                linear_api_key=os.getenv(f'LINEAR_API_KEY_USER{user_index}')
            )
            
            self.display_name_to_user[display_name.lower()] = user_id
            self.display_name_to_user[github_username.lower()] = user_id
            
            user_index += 1
        
        # Set shortcuts for common access patterns
        if 'user1' in self.users:
            self.user1 = self.users['user1']
        if 'user2' in self.users:
            self.user2 = self.users['user2']
    
    def get_user_config(self, user_id: str) -> UserConfig:
        """Get user configuration by user ID."""
        if user_id in self.users:
            return self.users[user_id]
        else:
            raise ValueError(f"Unknown user ID: {user_id}. Available users: {list(self.users.keys())}")
    
    def get_all_users(self) -> dict[str, UserConfig]:
        """Get all configured users."""
        return self.users
    
    def get_user_count(self) -> int:
        """Get the number of configured users."""
        return len(self.users)
    
    def resolve_user_from_name(self, name: str) -> Optional[str]:
        """Resolve user ID from display name or username."""
        return self.display_name_to_user.get(name.lower())
    
    def validate(self) -> list[str]:
        """Validate configuration and return list of errors."""
        errors = []
        
        # Check for Azure OpenAI configuration (required for LLM-powered system)
        if not os.getenv('AZURE_OPENAI_API_KEY'):
            errors.append("AZURE_OPENAI_API_KEY is required for LLM-powered routing and agents")
        if not os.getenv('AZURE_OPENAI_ENDPOINT'):
            errors.append("AZURE_OPENAI_ENDPOINT is required for LLM-powered routing and agents")
        if not os.getenv('AZURE_OPENAI_DEPLOYMENT'):
            errors.append("AZURE_OPENAI_DEPLOYMENT is required for LLM-powered routing and agents")
        
        if not self.users:
            errors.append("No users configured. At least one user is required.")
            return errors
        
        # Validate each user's credentials
        for user_id, user_config in self.users.items():
            if not user_config.github_token:
                errors.append(f"GITHUB_TOKEN_{user_id.upper()} is not set")
            if not user_config.linear_api_key:
                errors.append(f"LINEAR_API_KEY_{user_id.upper()} is not set")
        
        return errors


# Global config instance
config = Config()

