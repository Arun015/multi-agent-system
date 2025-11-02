# Multi-Agent System for GitHub and Linear

A multi-agent orchestration system that routes user queries to specialized agents (GitHub and Linear) with automatic user integration selection and clarification handling.

## Overview

This system demonstrates a production-ready multi-agent architecture that:
- **Intelligently routes** queries to the appropriate agent (GitHub or Linear)
- **Automatically selects** the correct user integration based on query context
- **Handles ambiguity** by asking for clarification when user identity is unclear
- **Integrates with real APIs** to fetch actual data from GitHub and Linear
- **Provides meaningful responses** with properly formatted data

## Architecture

### System Flow

![System Flow Diagram](flow.png)

The diagram shows the complete query processing flow:

1. **User Query** - User sends a natural language query
2. **LLM Router** - Azure GPT-4 analyzes intent and extracts user identity
3. **Route Decision** - Determines which agent to use (GitHub/Linear) or asks for clarification
4. **Agent Execution** - Selected agent calls the appropriate API
5. **Format Response** - Response is formatted in natural language and returned

### Core Components

1. **Orchestrator**: Coordinates the entire system, manages state, and handles clarification flows
2. **Router**: Analyzes queries to determine which agent should handle them (GitHub, Linear, or out-of-scope)
3. **User Resolver**: Identifies which user (Alice/Bob) the query refers to, requests clarification if ambiguous
4. **GitHub Agent**: Handles GitHub-related queries (repos, PRs, issues, stars) using REST API
5. **Linear Agent**: Handles Linear-related queries (issues, projects, teams) using GraphQL API

## Features

### Core Requirements ✓

- ✅ **Intelligent Routing**: Automatically routes queries to GitHub or Linear agents
- ✅ **Integration Selection**: Selects correct user (User 1 or User 2) based on query
- ✅ **Clarification Handling**: Asks for user clarification when identity is ambiguous
- ✅ **Out-of-Scope Handling**: Returns "I cannot answer this question" for unrelated queries
- ✅ **Real API Integration**: Fetches actual data from GitHub and Linear APIs

### Bonus Features ✓

- ✅ **Logging**: Comprehensive logging of agent/user selection with reasoning
- ✅ **Extensibility**: Easy configuration for adding new users or agents
- ✅ **Layered Architecture**: Organized code with clear separation of concerns

## Setup Instructions

### Prerequisites

- Python 3.8 or higher
- **Azure OpenAI** account with deployed model (GPT-4 recommended)
- GitHub accounts (2 users for testing)
- Linear accounts (2 users for testing, can be in same organization)
- GitHub Personal Access Tokens
- Linear API Keys

### Installation

1. **Clone the repository**
   ```bash
   cd /path/to/github_agent
   ```

2. **Create a virtual environment**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables**
   
   Edit the `.env` file and replace placeholder values with your real API keys:
   
   **Note:** `.env` file is in `.gitignore` - your secrets are safe!
   
   Required credentials:
   
   **Azure OpenAI** (required for LLM routing):
   - `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
   - `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI endpoint (e.g., https://your-resource.openai.azure.com/)
   - `AZURE_OPENAI_DEPLOYMENT` - Your deployment name (e.g., gpt-4)
   - `AZURE_OPENAI_API_VERSION` - API version (optional, defaults to 2024-02-15-preview)
   
   **GitHub** (for GitHub integration):
   - `GITHUB_TOKEN_USER1` - GitHub Personal Access Token for User 1
   - `GITHUB_USERNAME_USER1` - GitHub username for User 1
   - `GITHUB_TOKEN_USER2` - GitHub Personal Access Token for User 2
   - `GITHUB_USERNAME_USER2` - GitHub username for User 2
   
   **Linear** (for Linear integration):
   - `LINEAR_API_KEY_USER1` - Linear API key for User 1
   - `LINEAR_USERNAME_USER1` - Linear username for User 1
   - `LINEAR_API_KEY_USER2` - Linear API key for User 2
   - `LINEAR_USERNAME_USER2` - Linear username for User 2
   
   **User Display Names** (optional):
   - `USER1_DISPLAY_NAME` - Display name for User 1 (e.g., "Alice")
   - `USER2_DISPLAY_NAME` - Display name for User 2 (e.g., "Bob")

### Getting API Credentials

#### Azure OpenAI
1. Create an Azure OpenAI resource in Azure Portal
2. Deploy a model (e.g., GPT-4)
3. Get your API key from Keys and Endpoint section
4. Note your endpoint URL and deployment name

#### GitHub Personal Access Token
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic)
3. Select scopes: `repo`, `user`, `read:org`
4. Copy the token

#### Linear API Key
1. Go to Linear Settings → API
2. Create a new Personal API Key
3. Copy the key

## Usage

### Running the System

#### Option 1: REST API (Recommended)
```bash
# Start the API server
python run_server.py

# Or with uvicorn directly:
uvicorn api.main:app --reload

# Access interactive docs at:
# http://localhost:8000/docs

# Test with curl:
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Show me Alices repositories"}'
```

**Architecture**: Routes → Services → Core

#### Option 2: Running Tests

```bash
# Run all tests (no server needed, uses TestClient)
python -m unittest tests/test_api.py -v

# Run with coverage (71% coverage)
pytest tests/test_api.py --cov=api --cov-report=term-missing --no-cov-on-fail -v
```

**Note**: Tests use FastAPI's TestClient for in-process testing. No separate server needed.

#### Option 3: Using Docker
```bash
# Build and run
docker build -t multi-agent-api .
docker run -p 8000:8000 --env-file .env multi-agent-api
```

### Example Interactions

#### Clear User Identification
```
You: Show me Alice's open pull requests
Assistant: Alice has 3 open pull request(s):

1. Fix authentication bug in user-service (#42)
2. Add unit tests for API endpoints (#38)
3. Update documentation for v2 API (#35)
```

#### Ambiguous Query (Triggers Clarification)
```
You: Show me open pull requests
Assistant: I can help with that! Which user's github data would you like to see - Alice's or Bob's?

You: Alice
Assistant: Alice has 3 open pull request(s):
...
```

#### Linear Integration
```
You: What issues are assigned to Bob in Linear?
Assistant: Bob has 5 issue(s):

1. [ENG-123] Implement user authentication (In Progress) - Engineering
   Priority: High
2. [ENG-145] Fix memory leak in worker (Todo) - Engineering
   Priority: Urgent
...
```

#### Out of Scope Query
```
You: What's the weather today?
Assistant: I cannot answer this question
```

## Project Structure

**Layered Architecture**: Routes → Services → Core (Orchestrator → Agents)

```
github_agent/
├── api/                          # Application layer
│   ├── main.py                   # FastAPI application
│   ├── routes/api_routes.py      # API endpoints (health, query)
│   ├── services/query_service.py # Business logic
│   ├── dto/query_dto.py          # Request/Response models
│   └── core/                     # Core domain logic
│       ├── orchestrator.py       # Main coordinator
│       ├── llm_router.py         # LLM routing
│       ├── user_resolver.py      # User identification
│       └── agents/               # Agent implementations
│           ├── langchain_github_agent.py
│           └── linear_agent.py
├── tests/test_api.py             # Integration tests (71% coverage)
├── config.py                     # Configuration
├── run_server.py                 # Server entry point
├── requirements.txt              # Dependencies
├── Dockerfile                    # Docker image
└── flow.png                      # System flow diagram
```

## Extensibility - Adding More Users

The system supports N users through environment variables.

### Adding User 3

Add to your `.env` file:
```bash
GITHUB_TOKEN_USER3=ghp_user3_token_here
GITHUB_USERNAME_USER3=charlie
LINEAR_API_KEY_USER3=lin_api_user3_key_here
LINEAR_USERNAME_USER3=charlie
USER3_DISPLAY_NAME=Charlie
```

The system will load and configure User 3 at startup.

### Adding User 4, 5, 6... N

Continue with the same pattern: `USER4`, `USER5`, etc.

## Design Decisions

### 1. LLM-Powered Routing
Azure OpenAI GPT-4 is used for intelligent query routing:
- **Context Understanding**: Handles nuanced queries better than keyword matching
- **Ambiguity Detection**: Identifies when clarification is needed
- **Structured Outputs**: Returns confidence scores and reasoning
- **Extensibility**: Easy to add new routing logic

### 2. LangChain Framework
LangChain agents with function calling for GitHub operations:
- **Tool-Based Architecture**: GPT-4 decides which API calls to make
- **Dynamic Execution**: Adapts to different query types
- **Maintainability**: Clean separation between tools and logic

### 3. Layered Architecture
Routes → Services → Core (Orchestrator → Agents):
- **Separation of Concerns**: Each layer has clear responsibility
- **Testability**: Easy to test individual layers
- **Scalability**: Can scale different layers independently

### 4. Extensibility
The system supports:
- New users via environment variables (no code changes)
- New agents by extending BaseAgent
- New tools for LangChain agents

## Supported Queries

### GitHub Agent
- List repositories: "Show me Alice's repositories"
- Pull requests: "Show me Bob's open pull requests"
- Issues: "What issues does Alice have?"
- Starred repos: "Show me Bob's starred repositories"

### Linear Agent
- Assigned issues: "What issues are assigned to Alice?"
- Issues by status: "Show me Bob's in progress issues"
- High priority: "What are Alice's high priority issues?"
- Projects: "Show me Bob's Linear projects"
- Teams: "What teams is Alice on?"

## Assumptions & Limitations

### Assumptions
1. User 1 = "Alice" and User 2 = "Bob" by default (configurable)
2. GitHub tokens have appropriate permissions (repo, user access)
3. Linear users are part of the same organization or have appropriate access
4. Queries are in English

### Limitations
1. No persistent conversation history across sessions
2. No caching of API responses
3. No retry logic for failed API calls

## Testing

The system includes comprehensive automated tests with **71% code coverage**.

### Test Suite (14 test cases)

**Coverage:**
- ✅ Health check endpoint
- ✅ GitHub queries (repos, PRs, issues)
- ✅ Linear queries (issues, projects, teams)
- ✅ Clarification handling (ambiguous queries)
- ✅ Out-of-scope queries (weather, jokes, cooking)
- ✅ Error handling (empty query validation)

Uses `@parameterized.expand` for clean, maintainable test code.

### Real Data Required

The system requires real GitHub and Linear accounts with actual data:
1. Create/use 2 GitHub accounts with repos, PRs, or issues
2. Create/use 2 Linear accounts with issues assigned
3. Configure environment variables with real credentials
4. Run tests (see "Option 2: Running Tests" in Usage section)

## Logging

Logs are written to `multi_agent_system.log` and include:
- Query routing decisions with reasoning
- User resolution results
- Agent execution details
- API call outcomes
- Error traces

## Future Enhancements

Potential improvements:
- Persistent conversation history
- Response caching to reduce API calls
- Additional agents (Jira, Slack, Notion, etc.)
- Query history and analytics
- Rate limiting and authentication
- Enhanced error recovery with retry logic

## License

MIT License - Feel free to use and modify as needed.

## Contact

For questions or issues, please refer to the documentation or contact the development team.



