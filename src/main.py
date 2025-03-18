"""
Main FastAPI application entry point.
RCA system endpoints.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import RCA endpoints
from src.rca.api.endpoints import router as rca_router
from src.rca.api.tracking_endpoints import router as tracking_router
from src.rca.api.visualization import router as visualization_router

# Import version information
from src import __version__ as src_version
from src.rca import __version__ as rca_version

# Create the main FastAPI app
app = FastAPI(
    title="Azure DevOps RCA Tools",
    description="API for Root Cause Analysis System",
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
        "service": "Azure DevOps RCA Tools",
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