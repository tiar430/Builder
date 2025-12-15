from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZIPMiddleware
from backend.config import settings
from backend.database import init_db
from backend.routers import health_router, agent_router
from backend.mcp import mcp_manager
from backend.services.llm_service import llm_service
import logging

logger = logging.getLogger(__name__)

# Initialize database
init_db()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI Agent Multi-Tasking System with MCP Integration",
)

# Middleware
app.add_middleware(GZIPMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health_router)
app.include_router(agent_router)


@app.on_event("startup")
async def startup_event():
    """Initialize services on startup."""
    logger.info("Initializing AI Agent application...")

    # Initialize LLM service
    await llm_service.initialize()
    logger.info("LLM service initialized")

    # Initialize MCP connections
    mcp_status = await mcp_manager.connect_all()
    logger.info(f"MCP clients initialized: {mcp_status}")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    logger.info("Shutting down AI Agent application...")
    await mcp_manager.disconnect_all()


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running",
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
