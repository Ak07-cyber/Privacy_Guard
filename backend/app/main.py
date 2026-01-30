"""
PassiveGuard API - Main Application
ML-based passive bot detection to replace CAPTCHA
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.api import router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events"""
    # Startup
    print(f"🚀 Starting {settings.PROJECT_NAME} v{settings.VERSION}")
    print(f"📊 Debug mode: {settings.DEBUG}")
    yield
    # Shutdown
    print("👋 Shutting down...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    description="""
    ## PassiveGuard API
    
    ML-based passive bot detection system to replace traditional CAPTCHA.
    
    ### Features
    - **Passive Detection**: No user interaction required
    - **Behavioral Analysis**: Mouse, keyboard, scroll patterns
    - **Environmental Fingerprinting**: Browser and hardware analysis
    - **ML-Powered**: XGBoost classification with rule-based fallback
    - **Privacy-Focused**: No PII collection
    
    ### Endpoints
    - `POST /api/v1/verify` - Verify if user is human
    - `POST /api/v1/validate` - Validate verification token
    - `GET /api/v1/health` - Health check
    """,
    version=settings.VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix=settings.API_V1_PREFIX)


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs": "/docs",
        "health": f"{settings.API_V1_PREFIX}/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
