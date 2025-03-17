"""
Main FastAPI application entry point.
Combines chatbot and RCA system endpoints.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict

# Import chatbot endpoints
from src.chatbot.api.endpoints.main import app as chatbot_app

# Import RCA endpoints
from src.rca.api.endpoints import router as rca_router
from src.rca.api.tracking_endpoints import router as tracking_router
from src.rca.api.visualization import router as visualization_router

# Import version information
from src import __version__ as src_version
from src.rca import __version__ as rca_version

# Create the main FastAPI app
app = FastAPI(
    title="Azure DevOps Tools",
    description="Combined API for Azure DevOps CLI Chatbot and Root Cause Analysis System",
    version=src_version,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the chatbot routes
# We're not using app.include_router here because the chatbot app is a FastAPI instance,
# not a router. Instead, we'll recreate the endpoints.
# In a production system, we would refactor the chatbot to use a router.

# Include the RCA routes
app.include_router(rca_router)
app.include_router(tracking_router)
app.include_router(visualization_router)


@app.get("/", tags=["status"])
async def root():
    """
    Root endpoint that returns service information.
    """
    return {
        "service": "Azure DevOps Tools",
        "status": "online",
        "versions": {
            "api": src_version,
            "rca": rca_version
        }
    }


@app.get("/health", tags=["status"])
async def health():
    """
    Health check endpoint.
    """
    return {"status": "healthy"}


# Import chatbot endpoints to include in the main app
# Note: This is a temporary solution until chatbot is refactored to use routers
from src.chatbot.api.endpoints.main import chat as chatbot_chat
app.post("/chat")(chatbot_chat) 