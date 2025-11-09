"""Unit tests for LangChain GitHub Agent with minimal mocking (only network calls)."""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from parameterized import parameterized

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.core.agents.langchain_github_agent import LangChainGitHubAgent, LangChainGitHubAgentConfig


class TestLangChainGitHubAgent(unittest.TestCase):
    """Test cases for LangChain GitHub Agent with minimal mocks (only network calls)."""
    
    def setUp(self):
        """Set up test fixtures with config object."""
        self.config = LangChainGitHubAgentConfig(
            azure_api_key='test-key',
            azure_endpoint='https://test.openai.azure.com',
            azure_deployment='test-deployment',
            azure_api_version='2024-02-15-preview'
        )
        self.config.add_user("user1", "testuser1", "Test User 1", "test-token-1")
        self.config.add_user("user2", "testuser2", "Test User 2", "test-token-2")
    
    @staticmethod
    def _setup_mock_executor(mock_agent_executor, output=None, side_effect=None):
        """Helper: Setup mocked AgentExecutor with specified output or exception."""
        mock_executor_instance = MagicMock()
        if side_effect:
            mock_executor_instance.invoke.side_effect = side_effect
        else:
            mock_executor_instance.invoke.return_value = {"output": output}
        mock_agent_executor.return_value = mock_executor_instance
        return mock_executor_instance
    
    def _create_agent(self):
        """Helper: Create LangChainGitHubAgent instance with test config."""
        return LangChainGitHubAgent(config=self.config)
    
    @parameterized.expand([
        ("user1", "testuser1", "Test User 1"),
        ("user2", "testuser2", "Test User 2"),
    ])
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_repositories_query(self, user_id, username, display_name, _mock_azure_llm, mock_agent_executor):
        """Test executing a repositories query for both users."""
        expected_output = f"{display_name} has 2 repositories:\n\n1. repo1 - Description 1 (5 stars)\n2. repo2 - Description 2 (10 stars)"
        mock_executor_instance = self._setup_mock_executor(mock_agent_executor, expected_output)
        
        agent = self._create_agent()
        result = agent.execute("Show me my repositories", user_id)
        
        self.assertEqual(result, expected_output)
        mock_executor_instance.invoke.assert_called_once()
        call_args = mock_executor_instance.invoke.call_args[0][0]
        self.assertIn(display_name, call_args["input"])
        self.assertIn(username, call_args["input"])
        self.assertIn(user_id, call_args["input"])
    
    @parameterized.expand([
        ("user1", "Test User 1"),
        ("user2", "Test User 2"),
    ])
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_pull_requests_query(self, user_id, display_name, _mock_azure_llm, mock_agent_executor):
        """Test executing a pull requests query for both users."""
        expected_output = f"{display_name} has 1 open pull request(s):\n\n1. Fix bug in repo1 (#123)"
        self._setup_mock_executor(mock_agent_executor, expected_output)
        
        agent = self._create_agent()
        result = agent.execute("Show me my pull requests", user_id)
        
        self.assertEqual(result, expected_output)
    
    @parameterized.expand([
        ("user1", "Test User 1"),
        ("user2", "Test User 2"),
    ])
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_issues_query(self, user_id, display_name, _mock_azure_llm, mock_agent_executor):
        """Test executing an issues query for both users."""
        expected_output = f"{display_name} has 2 open issues:\n\n1. Bug in feature X\n2. Enhancement request"
        self._setup_mock_executor(mock_agent_executor, expected_output)
        
        agent = self._create_agent()
        result = agent.execute("What issues do I have?", user_id)
        
        self.assertEqual(result, expected_output)
    
    @parameterized.expand([
        ("user1", "Test User 1"),
        ("user2", "Test User 2"),
    ])
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_starred_repos_query(self, user_id, display_name, _mock_azure_llm, mock_agent_executor):
        """Test executing a starred repositories query for both users."""
        expected_output = f"{display_name} has starred 3 repositories:\n\n1. awesome-repo - Great project (1000 stars)"
        self._setup_mock_executor(mock_agent_executor, expected_output)
        
        agent = self._create_agent()
        result = agent.execute("Show me my starred repositories", user_id)
        
        self.assertEqual(result, expected_output)
    
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_error_handling(self, _mock_azure_llm, mock_agent_executor):
        """Test error handling when LLM network call fails."""
        self._setup_mock_executor(mock_agent_executor, side_effect=Exception("LLM API network error"))
        
        agent = self._create_agent()
        
        with self.assertRaises(RuntimeError) as context:
            agent.execute("Show me my repositories", "user1")
        
        self.assertIn("LangChain agent failed", str(context.exception))
    
    def test_missing_azure_config(self):
        """Test initialization fails when Azure OpenAI config is missing."""
        # Test that from_env() raises error when env vars are missing
        # This is the only place we mutate os.environ, and it's to test from_env() itself
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                LangChainGitHubAgentConfig.from_env()
            
            self.assertRegex(str(context.exception), r"Azure OpenAI configuration required|missing")
    
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_successful_initialization(self, _mock_azure_llm, mock_agent_executor):
        """Test that agent initializes successfully with proper config."""
        mock_executor_instance = MagicMock()
        mock_agent_executor.return_value = mock_executor_instance
        
        agent = LangChainGitHubAgent(config=self.config)
        
        self.assertIsNotNone(agent.llm)
        self.assertIsNotNone(agent.tools)
        self.assertIsNotNone(agent.agent_executor)
        self.assertEqual(agent.api_base, "https://api.github.com")
    
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_get_tools_contains_expected_functions(self, _mock_azure_llm, mock_agent_executor):
        """Test that _create_tools() returns expected tool functions."""
        mock_executor_instance = MagicMock()
        mock_agent_executor.return_value = mock_executor_instance
        
        agent = LangChainGitHubAgent(config=self.config)
        
        tool_names = [tool.name for tool in agent.tools]
        expected = {"get_user_repositories", "get_user_pull_requests", "get_user_issues", "get_user_starred_repos"}
        
        self.assertTrue(expected.issubset(set(tool_names)))
    
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_empty_response_fallback(self, _mock_azure_llm, mock_agent_executor):
        """Test that execute() handles empty response dict correctly."""
        mock_executor_instance = MagicMock()
        mock_executor_instance.invoke.return_value = {}
        mock_agent_executor.return_value = mock_executor_instance
        
        agent = self._create_agent()
        result = agent.execute("Show me my repositories", "user1")
        
        self.assertEqual(result, "No response generated")
    
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_tool_error_handling(self, _mock_azure_llm, mock_agent_executor):
        """Test that GitHub API errors are handled gracefully."""
        self._setup_mock_executor(mock_agent_executor, "Error fetching repositories: GitHub API error")
        
        agent = self._create_agent()
        result = agent.execute("Show me my repositories", "user1")
        
        self.assertIn("error", result.lower())
    
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_missing_user_config(self, _mock_azure_llm, mock_agent_executor):
        """Test executing a query with a missing user raises ValueError."""
        mock_executor_instance = MagicMock()
        mock_agent_executor.return_value = mock_executor_instance
        
        agent = LangChainGitHubAgent(config=self.config)
        with self.assertRaises(ValueError) as context:
            agent.execute("Show me my repositories", "nonexistent_user")
        self.assertIn("not found", str(context.exception).lower())


if __name__ == "__main__":
    unittest.main()
