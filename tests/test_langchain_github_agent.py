"""Unit tests for LangChain GitHub Agent with minimal mocking (only network calls)."""
import unittest
from unittest.mock import patch, MagicMock
import os
import sys
from parameterized import parameterized

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from api.core.agents.langchain_github_agent import LangChainGitHubAgent


class TestLangChainGitHubAgent(unittest.TestCase):
    """Test cases for LangChain GitHub Agent with minimal mocks (only network calls)."""
    
    def setUp(self):
        """Set up test fixtures with mocked environment variables."""
        self.env_patcher = patch.dict(os.environ, {
            'AZURE_OPENAI_API_KEY': 'test-key',
            'AZURE_OPENAI_ENDPOINT': 'https://test.openai.azure.com',
            'AZURE_OPENAI_DEPLOYMENT': 'test-deployment',
            'AZURE_OPENAI_API_VERSION': '2024-02-15-preview',
            'GITHUB_USERNAME_USER1': 'testuser1',
            'USER1_DISPLAY_NAME': 'Test User 1',
            'GITHUB_TOKEN_USER1': 'test-token-1',
            'GITHUB_USERNAME_USER2': 'testuser2',
            'USER2_DISPLAY_NAME': 'Test User 2',
            'GITHUB_TOKEN_USER2': 'test-token-2'
        })
        self.env_patcher.start()
    
    def tearDown(self):
        """Clean up after tests."""
        self.env_patcher.stop()
    
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
    
    @staticmethod
    def _setup_mock_config(mock_config, user_id, username, display_name):
        """Helper: Setup mocked config with user configuration."""
        mock_user_config = MagicMock()
        mock_user_config.display_name = display_name
        mock_user_config.username = username
        mock_config.get_user_config.return_value = mock_user_config
        return mock_user_config
    
    @staticmethod
    def _create_agent():
        """Helper: Create LangChainGitHubAgent instance."""
        return LangChainGitHubAgent()
    
    @parameterized.expand([
        ("user1", "testuser1", "Test User 1"),
        ("user2", "testuser2", "Test User 2"),
    ])
    @patch('api.core.agents.langchain_github_agent.config')
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_repositories_query(self, user_id, username, display_name, _mock_azure_llm, mock_agent_executor, mock_config):
        """Test executing a repositories query for both users."""
        expected_output = f"{display_name} has 2 repositories:\n\n1. repo1 - Description 1 (5 stars)\n2. repo2 - Description 2 (10 stars)"
        mock_executor_instance = self._setup_mock_executor(mock_agent_executor, expected_output)
        self._setup_mock_config(mock_config, user_id, username, display_name)
        
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
    @patch('api.core.agents.langchain_github_agent.config')
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_pull_requests_query(self, user_id, display_name, _mock_azure_llm, mock_agent_executor, mock_config):
        """Test executing a pull requests query for both users."""
        expected_output = f"{display_name} has 1 open pull request(s):\n\n1. Fix bug in repo1 (#123)"
        self._setup_mock_executor(mock_agent_executor, expected_output)
        self._setup_mock_config(mock_config, user_id, f"test{user_id}", display_name)
        
        agent = self._create_agent()
        result = agent.execute("Show me my pull requests", user_id)
        
        self.assertEqual(result, expected_output)
    
    @parameterized.expand([
        ("user1", "Test User 1"),
        ("user2", "Test User 2"),
    ])
    @patch('api.core.agents.langchain_github_agent.config')
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_issues_query(self, user_id, display_name, _mock_azure_llm, mock_agent_executor, mock_config):
        """Test executing an issues query for both users."""
        expected_output = f"{display_name} has 2 open issues:\n\n1. Bug in feature X\n2. Enhancement request"
        self._setup_mock_executor(mock_agent_executor, expected_output)
        self._setup_mock_config(mock_config, user_id, f"test{user_id}", display_name)
        
        agent = self._create_agent()
        result = agent.execute("What issues do I have?", user_id)
        
        self.assertEqual(result, expected_output)
    
    @parameterized.expand([
        ("user1", "Test User 1"),
        ("user2", "Test User 2"),
    ])
    @patch('api.core.agents.langchain_github_agent.config')
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_starred_repos_query(self, user_id, display_name, _mock_azure_llm, mock_agent_executor, mock_config):
        """Test executing a starred repositories query for both users."""
        expected_output = f"{display_name} has starred 3 repositories:\n\n1. awesome-repo - Great project (1000 stars)"
        self._setup_mock_executor(mock_agent_executor, expected_output)
        self._setup_mock_config(mock_config, user_id, f"test{user_id}", display_name)
        
        agent = self._create_agent()
        result = agent.execute("Show me my starred repositories", user_id)
        
        self.assertEqual(result, expected_output)
    
    @patch('api.core.agents.langchain_github_agent.config')
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_error_handling(self, _mock_azure_llm, mock_agent_executor, mock_config):
        """Test error handling when LLM network call fails."""
        self._setup_mock_executor(mock_agent_executor, side_effect=Exception("LLM API network error"))
        self._setup_mock_config(mock_config, "user1", "testuser", "Test User")
        
        agent = self._create_agent()
        
        with self.assertRaises(RuntimeError) as context:
            agent.execute("Show me my repositories", "user1")
        
        self.assertIn("LangChain agent failed", str(context.exception))
    
    def test_missing_azure_config(self):
        """Test initialization fails when Azure OpenAI config is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError) as context:
                LangChainGitHubAgent()
            
            self.assertRegex(str(context.exception), r"Azure OpenAI configuration required|missing")
    
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_successful_initialization(self, _mock_azure_llm, mock_agent_executor):
        """Test that agent initializes successfully with proper config."""
        mock_executor_instance = MagicMock()
        mock_agent_executor.return_value = mock_executor_instance
        
        agent = LangChainGitHubAgent()
        
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
        
        agent = LangChainGitHubAgent()
        
        tool_names = [tool.name for tool in agent.tools]
        expected = {"get_user_repositories", "get_user_pull_requests", "get_user_issues", "get_user_starred_repos"}
        
        self.assertTrue(expected.issubset(set(tool_names)))
    
    @patch('api.core.agents.langchain_github_agent.config')
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_execute_empty_response_fallback(self, _mock_azure_llm, mock_agent_executor, mock_config):
        """Test that execute() handles empty response dict correctly."""
        mock_executor_instance = MagicMock()
        mock_executor_instance.invoke.return_value = {}
        mock_agent_executor.return_value = mock_executor_instance
        self._setup_mock_config(mock_config, "user1", "testuser", "Test User")
        
        agent = self._create_agent()
        result = agent.execute("Show me my repositories", "user1")
        
        self.assertEqual(result, "No response generated")
    
    @patch('api.core.agents.langchain_github_agent.config')
    @patch('api.core.agents.langchain_github_agent.AgentExecutor')
    @patch('api.core.agents.langchain_github_agent.AzureChatOpenAI')
    def test_tool_error_handling(self, _mock_azure_llm, mock_agent_executor, mock_config):
        """Test that GitHub API errors are handled gracefully."""
        self._setup_mock_executor(mock_agent_executor, "Error fetching repositories: GitHub API error")
        self._setup_mock_config(mock_config, "user1", "testuser", "Test User")
        
        agent = self._create_agent()
        result = agent.execute("Show me my repositories", "user1")
        
        self.assertIn("error", result.lower())


if __name__ == "__main__":
    unittest.main()
