from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

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

# Import and include API routers
# from app.api.endpoints import hadiths, search
# app.include_router(hadiths.router, prefix=f"/api/{settings.API_VERSION}/hadiths", tags=["hadiths"])
# app.include_router(search.router, prefix=f"/api/{settings.API_VERSION}/search", tags=["search"])
