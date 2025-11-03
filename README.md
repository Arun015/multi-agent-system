# Multi-Agent System for GitHub and Linear

> **Submission for StackGen AI Dev Take-Home Assessment**  
> Python 3.12+ | Automated Testing | Docker Ready

## 🎥 Video Demo

**Watch the system in action:** [Click here to view demo](https://drive.google.com/file/d/1yl0sXtImJ-5NmaowzvE0itwNmmXNsyi3/view?usp=sharing)

![System Flow Diagram](flow.png)

A production-ready multi-agent orchestration system that intelligently routes user queries to specialized agents (GitHub and Linear) using LLM-powered routing with Azure OpenAI GPT-4.

## Overview

This system demonstrates a production-ready multi-agent architecture that:
- **Intelligently routes** queries to the appropriate agent (GitHub or Linear)
- **Automatically selects** the correct user integration based on query context
- **Handles ambiguity** by asking for clarification when user identity is unclear
- **Integrates with real APIs** to fetch actual data from GitHub and Linear
- **Provides meaningful responses** with properly formatted data


### System Flow

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

| Feature | Status | Implementation |
|---------|--------|----------------|
| **Intelligent Routing** | ✅ | Azure OpenAI GPT-4 with LangChain |
| **Integration Selection** | ✅ | Pattern matching with user resolver |
| **Clarification Handling** | ✅ | Multi-turn clarification flow |
| **Out-of-Scope Handling** | ✅ | Returns "I cannot answer this question" |
| **Real API Integration** | ✅ | GitHub REST API and Linear GraphQL API |
| **REST API** | ✅ | FastAPI with Swagger documentation |
| **Testing** | ✅ | 14 automated tests with parameterized cases |
| **Logging** | ✅ | Comprehensive structured logging |
| **Docker Support** | ✅ | Optimized Alpine image |
| **Extensibility** | ✅ | Dynamic user loading, easy to add agents |

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

- **Azure OpenAI**: Create resource in Azure Portal, deploy GPT-4, get API key and endpoint
- **GitHub Token**: Settings → Developer settings → Personal access tokens (scopes: `repo`, `user`, `read:org`)
- **Linear API Key**: Linear Settings → API → Create Personal API Key

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

# Run with coverage report
pytest tests/test_api.py --cov=api --cov-report=term-missing -v
```

**Note**: Tests use FastAPI's TestClient for in-process testing. No separate server needed.

#### Option 3: Using Docker
```bash
# Build and run
docker build -t multi-agent-api .
docker run -p 8000:8000 --env-file .env multi-agent-api
```

### Example Interactions

**Clear Query**: "Show me Alice's open pull requests" → Lists Alice's 3 PRs  
**Ambiguous Query**: "Show me open pull requests" → Asks: "Alice's or Bob's?"  
**Linear Query**: "What issues are assigned to Bob?" → Lists Bob's Linear issues with priority  
**Out of Scope**: "What's the weather?" → "I cannot answer this question"

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
├── tests/test_api.py             # Integration tests (14 test cases)
├── config.py                     # Configuration
├── run_server.py                 # Server entry point
├── requirements.txt              # Dependencies
├── Dockerfile                    # Docker image
└── flow.png                      # System flow diagram
```

## Extensibility

**Adding More Users**: System supports N users via environment variables. Add `USER3`, `USER4`, etc. with same pattern:
```bash
GITHUB_TOKEN_USER3=token_here
GITHUB_USERNAME_USER3=charlie
LINEAR_API_KEY_USER3=key_here
LINEAR_USERNAME_USER3=charlie
USER3_DISPLAY_NAME=Charlie
```

**Adding New Agents**: Extend `BaseAgent` class and register in orchestrator.

## Design Decisions

### Why LLM-Powered Routing?
**Decision**: Use Azure OpenAI GPT-4 for intelligent query routing

**Rationale**:
- Handles nuanced queries better than keyword matching
- Understands context and intent (e.g., "issues" could be GitHub or Linear)
- Provides structured outputs with confidence scores
- Extensible for future enhancements

### Why LangChain?
**Decision**: Use LangChain for GitHub agent with function calling

**Rationale**:
- Tool-based architecture where GPT-4 decides which API calls to make
- Dynamic execution that adapts to different query types
- Better handling of complex queries
- Clean separation between tools and logic

### Why Layered Architecture?
**Decision**: Routes → Services → Core (Orchestrator → Agents)

**Rationale**:
- Clear separation of concerns
- Easy to test individual layers
- Scalable and maintainable
- Industry-standard pattern

## Supported Queries

**GitHub**: repositories, pull requests, issues, starred repos  
**Linear**: assigned issues, status filters, priority, projects, teams  
**Example**: "Show me Alice's repositories", "What are Bob's high priority issues?"

## Testing

**14 Automated Test Cases** using `@parameterized.expand`:
- ✅ Health check, GitHub/Linear queries, clarification handling, out-of-scope queries, error handling
- **Requires**: Real GitHub and Linear accounts with actual data
- **Run**: `python -m unittest tests/test_api.py -v`

## Logging

Logs written to `multi_agent_system.log`: routing decisions, user resolution, agent execution, API outcomes, error traces

## Assumptions & Limitations

### Assumptions
1. User 1 = "Alice" and User 2 = "Bob" by default (configurable)
2. GitHub tokens have appropriate permissions (repo, user access)
3. Linear users are part of the same organization or have appropriate access
4. Queries are in English

### Known Limitations
1. **No Response Caching**: Each query hits APIs directly
2. **No Retry Logic**: API failures are not automatically retried
3. **No Persistent State**: Conversation history not stored across restarts

### Production Readiness Enhancements

If deploying to production, consider adding:
- **Caching**: Redis for API response caching
- **Rate Limiting**: Client-side rate limiting per API
- **Monitoring**: Prometheus metrics, Grafana dashboards
- **Database**: Store conversation history and analytics
- **Authentication**: API keys for multi-tenant support
- **CI/CD**: GitHub Actions for automated testing/deployment
- **Error Recovery**: Retry logic with exponential backoff, circuit breakers
- **Secrets Management**: AWS Secrets Manager or HashiCorp Vault

---
## 📋 Submission Information

**Assignment**: StackGen AI Dev Take-Home Assessment | **Time**: ~6 hours | **Language**: Python 3.12+

**Key Achievements**:
- ✅ LLM-powered routing with Azure GPT-4 + LangChain
- ✅ Real API integration (GitHub REST, Linear GraphQL)
- ✅ FastAPI REST API with comprehensive testing
- ✅ Production-ready (Docker, logging, layered architecture)
- ✅ Complete documentation with visual flow diagram
