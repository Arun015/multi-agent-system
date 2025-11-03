"""Main FastAPI application with layered architecture."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from api.routes import router

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Agent System API",
    description="""
    Multi-agent orchestration system for GitHub and Linear.
    
    ## Architecture
    
    - **Routes**: HTTP endpoints
    - **Services**: Business logic
    - **DTOs**: Data contracts
    - **Core**: Domain logic (Orchestrator, Agents)
    
    ## Features
    
    - Azure OpenAI GPT-4 routing
    - LangChain agents with function calling
    - Multi-turn clarification handling
    - Structured outputs with Pydantic
    """,
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Starting Multi-Agent System API v2.0")
    logger.info("Architecture: Routes → Services → Core (Orchestrator → Agents)")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down Multi-Agent System API")


app.include_router(router)

