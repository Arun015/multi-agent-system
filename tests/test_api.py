"""Integration tests for the multi-agent system API."""
import unittest
from fastapi.testclient import TestClient
from parameterized import parameterized
from api.main import app


class TestMultiAgentAPI(unittest.TestCase):
    """Test cases for multi-agent system API endpoints."""
    
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "healthy")
        self.assertTrue(data["llm_enabled"])
    
    @parameterized.expand([
        ("GitHub repositories", "Show me Alice's repositories", "Alice", "repositories"),
        ("GitHub pull requests", "Show me Bob's pull requests", "Bob", "pull request"),
        ("GitHub issues", "What GitHub issues does Alice have?", "Alice", None),
    ])
    def test_github_queries(self, name, query, expected_user, expected_keyword):
        """Test various GitHub queries with different users."""
        response = self.client.post("/query", json={"query": query})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        self.assertIn(expected_user, data["response"])
        if expected_keyword:
            self.assertIn(expected_keyword.lower(), data["response"].lower())
    
    @parameterized.expand([
        ("Linear issues", "What Linear issues are assigned to Alice?", "Alice"),
        ("Linear projects", "Show me Bob's Linear projects", "Bob"),
        ("Linear teams", "What teams is Alice on?", "Alice"),
    ])
    def test_linear_queries(self, name, query, expected_user):
        """Test various Linear queries with different users."""
        response = self.client.post("/query", json={"query": query})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        response_lower = data["response"].lower()
        self.assertTrue(
            expected_user in data["response"] or 
            "issue" in response_lower or
            "project" in response_lower or
            "team" in response_lower or
            "linear" in response_lower or
            "?" in data["response"]
        )
    
    @parameterized.expand([
        ("Ambiguous repositories", "Show me repositories", ["Alice", "Bob"], "?"),
        ("Ambiguous pull requests", "List pull requests", ["Alice", "Bob"], "?"),
        ("Ambiguous issues", "Show me issues", ["Alice", "Bob"], "?"),
    ])
    def test_clarification_queries(self, name, query, expected_users, expected_symbol):
        """Test queries that require clarification."""
        response = self.client.post("/query", json={"query": query})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        response_text = data["response"]
        self.assertIn(expected_symbol, response_text)
        has_users = any(user in response_text for user in expected_users)
        self.assertTrue(has_users)
    
    @parameterized.expand([
        ("Weather query", "What's the weather today?"),
        ("General question", "Tell me a joke"),
        ("Cooking query", "How do I cook pasta?"),
    ])
    def test_out_of_scope_queries(self, name, query):
        """Test out-of-scope queries."""
        response = self.client.post("/query", json={"query": query})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("response", data)
        response_lower = data["response"].lower()
        has_rejection_or_clarification = (
            "cannot answer" in response_lower or
            "cannot help" in response_lower or
            "github or linear" in response_lower or
            "?" in data["response"]
        )
        self.assertTrue(has_rejection_or_clarification)
    
    def test_empty_query(self):
        """Test empty query validation."""
        response = self.client.post("/query", json={"query": ""})
        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main(verbosity=2)

