from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

class SourceBase(BaseModel):
    """Base model for hadith sources"""
    name: str
    tradition: str
    description: Optional[str] = None
    compiler: Optional[str] = None

class SourceCreate(SourceBase):
    """Model for creating a new source"""
    pass

class Source(SourceBase):
    """Model for a source with database id"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class HadithBase(BaseModel):
    """Base model for hadiths"""
    source_id: int
    volume: Optional[int] = None
    book: Optional[int] = None
    chapter: Optional[int] = None
    number: Optional[int] = None
    arabic_text: str
    english_text: Optional[str] = None
    narrator_chain: Optional[str] = None
    topics: Optional[List[str]] = Field(default_factory=list)
    
class HadithCreate(HadithBase):
    """Model for creating a new hadith"""
    pass

class Hadith(HadithBase):
    """Model for a hadith with database id"""
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    # vector_embedding will be handled separately

    class Config:
        from_attributes = True

class HadithWithSource(Hadith):
    """Model for a hadith with its source information"""
    source: Source
