from fastapi import APIRouter, Query, HTTPException, Body, Depends
from typing import List, Optional, Dict, Any
from datetime import datetime
import logging
import json
from sentence_transformers import SentenceTransformer
import numpy as np

from app.db.database import supabase
from app.api.models.search import (
    SearchQuery, 
    SearchResults, 
    HadithWithSimilarity,
    SimilaritySearchParams,
    SourceInfo
)
from app.api.utils.embedding import get_embedding_model, generate_embedding

# Initialize router
router = APIRouter()

# Setup logging
logger = logging.getLogger(__name__)

def _build_vector_search_sql(
    query_embedding: List[float],
    query_text: str,
    source_id: Optional[int] = None,
    book: Optional[int] = None,
    limit: int = 10,
    offset: int = 0
) -> str:
    """
    Build the SQL query for hybrid search combining vector similarity with full-text search
    """
    # Convert the embedding to a PostgreSQL vector literal
    # Don't use json.dumps as it adds extra quotes
    embedding_str = str(query_embedding).replace('[', '').replace(']', '')
    
    # Prepare the text search query - escape special characters
    safe_query = query_text.replace("'", "''")
    
    # For phrase searches, we need to be more flexible
    # Extract individual words for partial matching
    words = safe_query.split()
    word_conditions = []
    
    # Create conditions for individual words (for words longer than 3 characters)
    for word in words:
        if len(word) > 3:
            word_conditions.append(f"h.english_text ILIKE '%{word}%'")
    
    # Join the word conditions with OR
    word_search_clause = " OR ".join(word_conditions) if word_conditions else "FALSE"
    
    # Build the SQL query with hybrid similarity and filters
    sql = f"""
    SELECT
        h.id,
        h.source_id,
        h.volume,
        h.book,
        h.chapter,
        h.number,
        h.arabic_text,
        h.english_text,
        h.narrator_chain,
        h.topics,
        h.created_at,
        h.updated_at,
        s.name AS source_name,
        s.tradition,
        s.compiler,
        (
            0.8 * (1 - (h.vector_embedding <=> '[{embedding_str}]'::vector)) + 
            0.2 * CASE WHEN h.english_text ILIKE '%{safe_query}%' THEN 1.0 ELSE 0.0 END
        ) AS similarity
    FROM
        hadiths h
        JOIN sources s ON h.source_id = s.id
    WHERE
        h.vector_embedding IS NOT NULL
        AND (
            (1 - (h.vector_embedding <=> '[{embedding_str}]'::vector)) > 0.4
            OR h.english_text ILIKE '%{safe_query}%'
            OR ({word_search_clause})
        )
    """
    
    # Add filters
    conditions = []
    
    # Source filter
    if source_id is not None:
        conditions.append(f"h.source_id = {source_id}")
    
    # Book filter
    if book is not None:
        conditions.append(f"h.book = {book}")
    
    # Add WHERE clause if conditions exist
    if conditions:
        sql += " AND " + " AND ".join(conditions)
    
    # Complete the query with ordering and limit
    sql += f"""
    ORDER BY similarity DESC
    LIMIT {limit} OFFSET {offset}
    """
    
    return sql

def _count_search_results(
    query_embedding: List[float],
    query_text: str,
    source_id: Optional[int] = None,
    book: Optional[int] = None
) -> int:
    """
    Get the total count of matching results for pagination
    """
    # Convert the embedding to a PostgreSQL vector literal
    # Don't use json.dumps as it adds extra quotes
    embedding_str = str(query_embedding).replace('[', '').replace(']', '')
    
    # Prepare the text search query
    safe_query = query_text.replace("'", "''")
    
    # For phrase searches, we need to be more flexible
    # Extract individual words for partial matching
    words = safe_query.split()
    word_conditions = []
    
    # Create conditions for individual words (for words longer than 3 characters)
    for word in words:
        if len(word) > 3:
            word_conditions.append(f"h.english_text ILIKE '%{word}%'")
    
    # Join the word conditions with OR
    word_search_clause = " OR ".join(word_conditions) if word_conditions else "FALSE"
    
    # Build the count SQL query
    sql = f"""
    SELECT
        COUNT(*) AS total_count
    FROM
        hadiths h
        JOIN sources s ON h.source_id = s.id
    WHERE
        h.vector_embedding IS NOT NULL
        AND (
            (1 - (h.vector_embedding <=> '[{embedding_str}]'::vector)) > 0.4
            OR h.english_text ILIKE '%{safe_query}%'
            OR ({word_search_clause})
        )
    """
    
    # Add filters
    conditions = []
    
    # Source filter
    if source_id is not None:
        conditions.append(f"h.source_id = {source_id}")
    
    # Book filter
    if book is not None:
        conditions.append(f"h.book = {book}")
    
    # Add WHERE clause if conditions exist
    if conditions:
        sql += " AND " + " AND ".join(conditions)
    
    try:
        # Execute the count query
        result = supabase.rpc("execute_sql", {"sql_query": sql}).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('total_count', 0)
        return 0
    except Exception as e:
        logger.error(f"Error counting search results: {e}")
        return 0

@router.get("/", response_model=SearchResults)
async def search_text(
    query: str = Query(..., min_length=2, description="Text to search for"),
    limit: int = Query(10, ge=1, le=100, description="Number of results to return"),
    page: int = Query(1, ge=1, description="Page number"),
    source_id: Optional[int] = Query(None, description="Filter by source ID"),
    book: Optional[int] = Query(None, description="Filter by book number"),
):
    """
    Search for hadiths by similarity to the provided query text.
    Uses a hybrid approach combining vector similarity with full-text search.
    """
    try:
        # Log the search query
        logger.info(f"Search request received - Query: '{query}', Page: {page}, Limit: {limit}")
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Generate embedding for the query text
        model = get_embedding_model()
        query_embedding = generate_embedding(model, query)
        logger.debug(f"Generated embedding for query: '{query}'")
        
        # Build the SQL query for hybrid search
        sql_query = _build_vector_search_sql(
            query_embedding=query_embedding,
            query_text=query,
            source_id=source_id,
            book=book,
            limit=limit,
            offset=offset
        )
        
        # Log the SQL query for debugging
        logger.debug(f"SQL Query: {sql_query}")
        
        # Execute the SQL query
        result = supabase.rpc(
            "execute_sql", 
            {"sql_query": sql_query}
        ).execute()
        
        # Log the raw response
        logger.debug(f"Raw response type: {type(result.data)}")
        if result.data:
            logger.debug(f"Result data sample: {str(result.data)[:200]}...")

        # Get total count for pagination
        total_count = _count_search_results(
            query_embedding=query_embedding,
            query_text=query,
            source_id=source_id,
            book=book
        )
        
        logger.info(f"Search found {total_count} total results for query: '{query}'")
        
        # Process the results
        hadiths = []
        items = []
        if result.data:
            # If result.data is a list with a single element which is a list/dict/string
            if isinstance(result.data, list) and len(result.data) == 1:
                if isinstance(result.data[0], list):
                    items = result.data[0]
                elif isinstance(result.data[0], dict):
                    items = [result.data[0]]
                elif isinstance(result.data[0], str):
                    import json
                    items = json.loads(result.data[0])
            elif isinstance(result.data, list):
                items = result.data
            elif isinstance(result.data, dict):
                items = [result.data]
        else:
            items = []

        for item in items:
            # Convert item to HadithWithSimilarity format
            source_info = SourceInfo(
                id=item['source_id'],
                name=item['source_name'],
                tradition=item['tradition'],
                compiler=item.get('compiler')
            )

            hadith = HadithWithSimilarity(
                id=item['id'],
                source_id=item['source_id'],
                volume=item.get('volume'),
                book=item.get('book'),
                chapter=item.get('chapter'),
                number=item.get('number'),
                arabic_text=item.get('arabic_text'),
                english_text=item.get('english_text'),
                narrator_chain=item.get('narrator_chain'),
                topics=item.get('topics'),
                source=source_info,
                similarity=item['similarity'],
                created_at=item['created_at'],
                updated_at=item.get('updated_at')
            )
            hadiths.append(hadith)

        # Return the search results
        logger.info(f"Returning {len(hadiths)} hadiths for page {page} of query: '{query}'")
        return SearchResults(
            hadiths=hadiths,
            total_count=total_count,
            page=page,
            limit=limit,
            query=query
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in search_text: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")
