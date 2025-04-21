from fastapi import APIRouter, Query, HTTPException, Path, Depends
from typing import List, Optional, Dict, Any
import logging

from app.db.database import supabase
from app.api.models.search import SourceInfo

# Initialize router
router = APIRouter()

# Setup logging
logger = logging.getLogger(__name__)

@router.get("/")
async def get_hadiths(
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    book: Optional[int] = Query(None, description="Filter by book number"),
    chapter: Optional[int] = Query(None, description="Filter by chapter number"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    page: int = Query(1, ge=1, description="Page number"),
):
    """
    Get a list of hadiths with optional filtering
    """
    try:
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Build the query
        query = """
        SELECT 
            h.*,
            s.name AS source_name,
            s.tradition,
            s.compiler
        FROM 
            hadiths h
            JOIN sources s ON h.source_id = s.id
        WHERE 1=1
        """
        
        # Add filters
        if source_id is not None:
            query += f" AND h.source_id = {source_id}"
        
        if book is not None:
            query += f" AND h.book = {book}"
        
        if chapter is not None:
            query += f" AND h.chapter = {chapter}"
        
        # Add order by and limit
        query += f"""
        ORDER BY h.source_id, h.book, h.chapter, h.number
        LIMIT {limit} OFFSET {offset}
        """
        
        # Count query
        count_query = """
        SELECT COUNT(*) AS total_count
        FROM hadiths h
        WHERE 1=1
        """
        
        # Add the same filters to count query
        if source_id is not None:
            count_query += f" AND h.source_id = {source_id}"
        
        if book is not None:
            count_query += f" AND h.book = {book}"
        
        if chapter is not None:
            count_query += f" AND h.chapter = {chapter}"
        
        # Execute the queries
        result = supabase.rpc("execute_sql", {"sql_query": query}).execute()
        count_result = supabase.rpc("execute_sql", {"sql_query": count_query}).execute()
        
        # Process results
        hadiths = []
        total_count = 0
        
        if count_result.data and len(count_result.data) > 0:
            total_count = count_result.data[0].get("total_count", 0)
        
        if result.data:
            for item in result.data:
                # Add source info
                source_info = {
                    "id": item["source_id"],
                    "name": item["source_name"],
                    "tradition": item["tradition"],
                    "compiler": item.get("compiler")
                }
                
                # Remove redundant fields
                item.pop("source_name", None)
                item["source"] = source_info
                
                hadiths.append(item)
        
        # Return the results with pagination info
        return {
            "hadiths": hadiths,
            "total_count": total_count,
            "page": page,
            "limit": limit
        }
    except Exception as e:
        logger.error(f"Error getting hadiths: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{hadith_id}")
async def get_hadith_by_id(
    hadith_id: int = Path(..., title="The ID of the hadith to get")
):
    """
    Get a hadith by its ID
    """
    try:
        # Build the query
        query = f"""
        SELECT 
            h.*,
            s.name AS source_name,
            s.tradition,
            s.compiler
        FROM 
            hadiths h
            JOIN sources s ON h.source_id = s.id
        WHERE 
            h.id = {hadith_id}
        """
        
        # Execute the query
        result = supabase.rpc("execute_sql", {"sql_query": query}).execute()
        
        if not result.data or len(result.data) == 0:
            raise HTTPException(status_code=404, detail=f"Hadith with ID {hadith_id} not found")
        
        hadith = result.data[0]
        
        # Add source info
        source_info = {
            "id": hadith["source_id"],
            "name": hadith["source_name"],
            "tradition": hadith["tradition"],
            "compiler": hadith.get("compiler")
        }
        
        # Remove redundant fields
        hadith.pop("source_name", None)
        hadith["source"] = source_info
        
        return hadith
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting hadith {hadith_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/sources")
async def get_sources():
    """
    Get a list of all sources
    """
    try:
        # Build the query
        query = """
        SELECT * FROM sources
        ORDER BY tradition, name
        """
        
        # Execute the query
        result = supabase.rpc("execute_sql", {"sql_query": query}).execute()
        
        sources = result.data if result.data else []
        
        return {
            "sources": sources,
            "count": len(sources)
        }
    except Exception as e:
        logger.error(f"Error getting sources: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/books/{source_id}")
async def get_books(
    source_id: int = Path(..., title="The ID of the source to get books for")
):
    """
    Get a list of books for a source
    """
    try:
        # Build the query
        query = f"""
        SELECT DISTINCT book, COUNT(*) as hadith_count
        FROM hadiths
        WHERE source_id = {source_id}
        GROUP BY book
        ORDER BY book
        """
        
        # Execute the query
        result = supabase.rpc("execute_sql", {"sql_query": query}).execute()
        
        books = result.data if result.data else []
        
        return {
            "books": books,
            "count": len(books)
        }
    except Exception as e:
        logger.error(f"Error getting books for source {source_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/chapters/{source_id}/{book}")
async def get_chapters(
    source_id: int = Path(..., title="The ID of the source"),
    book: int = Path(..., title="The book number")
):
    """
    Get a list of chapters for a book in a source
    """
    try:
        # Build the query
        query = f"""
        SELECT DISTINCT chapter, COUNT(*) as hadith_count
        FROM hadiths
        WHERE source_id = {source_id} AND book = {book}
        GROUP BY chapter
        ORDER BY chapter
        """
        
        # Execute the query
        result = supabase.rpc("execute_sql", {"sql_query": query}).execute()
        
        chapters = result.data if result.data else []
        
        return {
            "chapters": chapters,
            "count": len(chapters)
        }
    except Exception as e:
        logger.error(f"Error getting chapters for source {source_id}, book {book}: {e}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
