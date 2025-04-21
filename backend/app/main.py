from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.core.config import settings
from app.api.endpoints import hadiths, search, compare

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Hadith Similarity Search API",
    description="API for cross-tradition hadith similarity search",
    version="0.1.0",
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Welcome to Hadith Similarity Search API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# Import and include API routers - use the imported modules
app.include_router(hadiths.router, prefix=f"/api/{settings.API_VERSION}/hadiths", tags=["hadiths"])
app.include_router(search.router, prefix=f"/api/{settings.API_VERSION}/search", tags=["search"])
app.include_router(compare.router, prefix=f"/api/{settings.API_VERSION}/compare", tags=["compare"])

@app.on_event("startup")
async def startup_event():
    logger.info("Starting Hadith Similarity Search API...")
    logger.info(f"API Version: {settings.API_VERSION}")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug Mode: {settings.DEBUG}")