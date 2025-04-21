from pydantic import BaseModel, Field, model_validator
from typing import List, Optional, Dict, Any
from datetime import datetime

class SimilaritySearchParams(BaseModel):
    """Parameters for similarity search"""
    query: str = Field(..., min_length=2, description="Text to search for")
    limit: int = Field(10, ge=1, le=100, description="Number of results to return")
    page: int = Field(1, ge=1, description="Page number")
    source_id: Optional[int] = Field(None, description="Filter by source ID")
    book: Optional[int] = Field(None, description="Filter by book number")

# Rest of the file remains the same...
class SearchQuery(BaseModel):
    """Search query model"""
    query: str
    params: SimilaritySearchParams

class SourceInfo(BaseModel):
    """Source information included with search results"""
    id: int
    name: str
    tradition: str
    compiler: Optional[str] = None

class HadithWithSimilarity(BaseModel):
    """Hadith with similarity score for search results"""
    id: int
    source_id: int
    volume: Optional[int] = None
    book: Optional[int] = None
    chapter: Optional[int] = None
    number: Optional[int] = None
    arabic_text: Optional[str] = None
    english_text: Optional[str] = None
    narrator_chain: Optional[str] = None
    topics: Optional[List[str]] = None
    source: SourceInfo
    similarity: float
    created_at: datetime
    updated_at: Optional[datetime] = None

class SearchResults(BaseModel):
    """Search results with pagination info"""
    hadiths: List[HadithWithSimilarity]
    total_count: int
    page: int
    limit: int
    query: str