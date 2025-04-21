from fastapi import APIRouter, Query, HTTPException, Body
from typing import List, Optional, Dict, Any
import logging
import numpy as np
import json

from app.db.database import supabase
from app.api.models.search import SourceInfo, HadithWithSimilarity, SearchResults
from app.api.utils.embedding import get_embedding_model, generate_embedding

# Initialize router
router = APIRouter()

# Setup logging
logger = logging.getLogger(__name__)

class HadithComparisonResult(Dict[str, Any]):
    """A dictionary representing hadith comparison results"""
    pass

@router.get("/hadith-to-hadith")
async def compare_hadiths(
    hadith_id_1: int = Query(..., description="ID of the first hadith"),
    hadith_id_2: int = Query(..., description="ID of the second hadith")
):
    """
    Compare two hadiths by their ID and calculate similarity
    """
    try:
        # Get both hadiths with their sources
        hadith1 = await _get_hadith_with_source(hadith_id_1)
        if not hadith1:
            raise HTTPException(status_code=404, detail=f"Hadith with ID {hadith_id_1} not found")
            
        hadith2 = await _get_hadith_with_source(hadith_id_2)
        if not hadith2:
            raise HTTPException(status_code=404, detail=f"Hadith with ID {hadith_id_2} not found")
        
        # Calculate similarity using vector embeddings if available
        similarity = await _calculate_hadith_similarity(hadith1, hadith2)
        
        # Create response
        result = {
            "hadith1": hadith1,
            "hadith2": hadith2,
            "similarity": similarity,
            "similar_segments": _identify_similar_segments(hadith1, hadith2)
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing hadiths: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")

@router.get("/hadith-to-text")
async def compare_hadith_to_text(
    hadith_id: int = Query(..., description="ID of the hadith"),
    text: str = Query(..., min_length=2, description="Text to compare against")
):
    """
    Compare a hadith to arbitrary text and calculate similarity
    """
    try:
        # Get the hadith with its source
        hadith = await _get_hadith_with_source(hadith_id)
        if not hadith:
            raise HTTPException(status_code=404, detail=f"Hadith with ID {hadith_id} not found")
        
        # Generate embedding for the input text
        model = get_embedding_model()
        text_embedding = generate_embedding(model, text)
        
        # Get the hadith's embedding
        hadith_embedding = hadith.get("vector_embedding")
        if not hadith_embedding:
            raise HTTPException(
                status_code=400, 
                detail="Hadith does not have an embedding vector. Please run the embedding generation script."
            )
        
        # Calculate cosine similarity
        similarity = _calculate_cosine_similarity(hadith_embedding, text_embedding)
        
        # Create response
        result = {
            "hadith": hadith,
            "text": text,
            "similarity": similarity
        }
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing hadith to text: {e}")
        raise HTTPException(status_code=500, detail=f"Comparison error: {str(e)}")

@router.get("/similar-hadiths/{hadith_id}")
async def find_similar_hadiths(
    hadith_id: int,
    limit: int = Query(10, ge=1, le=100, description="Number of similar hadiths to return"),
    page: int = Query(1, ge=1, description="Page number"),
):
    """
    Find hadiths similar to the provided hadith ID.
    Returns a list of similar hadiths with similarity scores.
    Uses a hybrid approach combining vector similarity with text matching.
    """
    try:
        # Get the source hadith with its embedding
        hadith = await _get_hadith_with_source(hadith_id)
        if not hadith:
            raise HTTPException(status_code=404, detail=f"Hadith with ID {hadith_id} not found")
        
        # Get the hadith's embedding
        hadith_embedding = hadith.get("vector_embedding")
        if not hadith_embedding:
            raise HTTPException(
                status_code=400, 
                detail="Hadith does not have an embedding vector. Please run the embedding generation script."
            )
        
        # Get the hadith's text for text-based similarity
        hadith_text = hadith.get("english_text", "")
        
        # Calculate offset for pagination
        offset = (page - 1) * limit
        
        # Build the SQL query for finding similar hadiths
        sql_query = _build_similar_hadiths_sql(
            hadith_id=hadith_id,
            query_embedding=hadith_embedding,
            query_text=hadith_text,
            limit=limit,
            offset=offset
        )
        
        # Debug the SQL query
        logger.debug(f"Similar hadiths SQL query: {sql_query}")
        
        # Execute the SQL query
        result = supabase.rpc(
            "execute_sql", 
            {"sql_query": sql_query}
        ).execute()
        
        # Debug the response structure
        logger.debug(f"Similar hadiths result structure: {type(result.data)}")
        if result.data:
            logger.debug(f"Result data: {result.data}")
        
        # Get total count for pagination (use a default of 0 if there's an error)
        try:
            total_count = _count_similar_hadiths(
                hadith_id=hadith_id,
                query_embedding=hadith_embedding,
                query_text=hadith_text
            )
        except Exception as e:
            logger.error(f"Error getting count: {e}")
            total_count = 0
        
        # Process the results
        hadiths = []
        items = []
        
        if result.data:
            # Handle different possible response structures
            if isinstance(result.data, list):
                items = result.data
            elif isinstance(result.data, dict):
                # Check if it's an error response
                if 'error' in result.data:
                    logger.error(f"SQL error: {result.data.get('error')}, details: {result.data.get('details')}")
                    raise HTTPException(status_code=500, detail=f"Database error: {result.data.get('error')}")
                items = [result.data]
        else:
            items = []

        for item in items:
            try:
                # Log the item structure to debug
                logger.debug(f"Processing item: {item}")
                
                # Convert item to HadithWithSimilarity format
                source_info = SourceInfo(
                    id=item.get('source_id'),
                    name=item.get('source_name', ''),
                    tradition=item.get('tradition', ''),
                    compiler=item.get('compiler')
                )

                similar_hadith = HadithWithSimilarity(
                    id=item.get('id'),
                    source_id=item.get('source_id'),
                    volume=item.get('volume'),
                    book=item.get('book'),
                    chapter=item.get('chapter'),
                    number=item.get('number'),
                    arabic_text=item.get('arabic_text'),
                    english_text=item.get('english_text'),
                    narrator_chain=item.get('narrator_chain'),
                    topics=item.get('topics'),
                    source=source_info,
                    similarity=float(item.get('similarity', 0.0)),
                    created_at=item.get('created_at'),
                    updated_at=item.get('updated_at')
                )
                hadiths.append(similar_hadith)
            except Exception as e:
                logger.error(f"Error processing item: {e}, Item: {item}")
                continue

        # Return the search results
        return SearchResults(
            hadiths=hadiths,
            total_count=total_count,
            page=page,
            limit=limit,
            query=f"Similar to hadith #{hadith_id}"
        )
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error finding similar hadiths: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")

async def _get_hadith_with_source(hadith_id: int) -> Optional[Dict[str, Any]]:
    """
    Get a hadith with its source information
    """
    try:
        # Query hadith with join to source
        query = """
        SELECT 
            h.*,
            s.name AS source_name,
            s.tradition,
            s.compiler
        FROM 
            hadiths h
            JOIN sources s ON h.source_id = s.id
        WHERE 
            h.id = :hadith_id
        """
        
        result = supabase.rpc(
            "execute_sql", 
            {"sql_query": query.replace(":hadith_id", str(hadith_id))}
        ).execute()
        
        if not result.data or len(result.data) == 0:
            return None
        
        hadith = result.data[0]
        
        # Add source info
        hadith["source"] = {
            "id": hadith["source_id"],
            "name": hadith["source_name"],
            "tradition": hadith["tradition"],
            "compiler": hadith.get("compiler")
        }
        
        # Remove redundant fields
        hadith.pop("source_name", None)
        
        return hadith
    except Exception as e:
        logger.error(f"Error getting hadith {hadith_id}: {e}")
        return None

async def _calculate_hadith_similarity(hadith1: Dict[str, Any], hadith2: Dict[str, Any]) -> float:
    """
    Calculate similarity between two hadiths
    """
    # Use vector embeddings if available
    if hadith1.get("vector_embedding") and hadith2.get("vector_embedding"):
        return _calculate_cosine_similarity(hadith1["vector_embedding"], hadith2["vector_embedding"])
    
    # Fallback to text comparison if embeddings are not available
    logger.warning("Vector embeddings not available, falling back to text comparison")
    
    # Generate embeddings on the fly
    model = get_embedding_model()
    
    # Prefer Arabic text, fall back to English
    text1 = hadith1.get("arabic_text") or hadith1.get("english_text", "")
    text2 = hadith2.get("arabic_text") or hadith2.get("english_text", "")
    
    if not text1 or not text2:
        return 0.0
    
    embedding1 = generate_embedding(model, text1)
    embedding2 = generate_embedding(model, text2)
    
    return _calculate_cosine_similarity(embedding1, embedding2)

def _calculate_cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """
    Calculate cosine similarity between two vectors
    """
    # Convert to numpy arrays
    a = np.array(vec1)
    b = np.array(vec2)
    
    # Calculate cosine similarity
    cosine_sim = np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))
    
    # Ensure the result is between 0 and 1
    return float(max(0.0, min(1.0, cosine_sim)))

def _identify_similar_segments(hadith1: Dict[str, Any], hadith2: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify similar segments between two hadiths (simplified version)
    
    Note: A more advanced implementation would use text segmentation
    and similarity matching between segments.
    """
    # In a real implementation, this would analyze text segments
    # For now, just return a placeholder
    return [{
        "hadith1_segment": "This is a placeholder for similar segment identification",
        "hadith2_segment": "This would highlight matching segments between hadiths",
        "similarity": 0.85
    }]

def _build_similar_hadiths_sql(
    hadith_id: int,
    query_embedding: List[float],
    query_text: str,
    limit: int = 10,
    offset: int = 0
) -> str:
    """
    Build the SQL query for finding similar hadiths using hybrid search
    """
    # Convert the embedding to a PostgreSQL vector literal
    # Don't use json.dumps as it adds extra quotes
    embedding_str = str(query_embedding).replace('[', '').replace(']', '')
    
    # Prepare the text search query - escape special characters and convert to tsquery format
    safe_query = query_text.replace("'", "''")
    
    # Create a simplified version of the query for text search
    # Extract key phrases and words (simplified approach)
    words = safe_query.split()
    simplified_query = " & ".join([word for word in words if len(word) > 3])
    
    # If simplified query is empty, use the original query
    if not simplified_query:
        simplified_query = safe_query.replace(" ", " & ")
    
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
            0.7 * (1 - (h.vector_embedding <=> '[{embedding_str}]'::vector)) + 
            0.3 * CASE 
                WHEN to_tsvector('english', h.english_text) @@ to_tsquery('english', '{simplified_query}') 
                THEN ts_rank_cd(to_tsvector('english', h.english_text), to_tsquery('english', '{simplified_query}'))
                ELSE 0
            END
        ) AS similarity
    FROM
        hadiths h
        JOIN sources s ON h.source_id = s.id
    WHERE
        h.vector_embedding IS NOT NULL
        AND h.id != {hadith_id}  -- Exclude the source hadith
        AND (
            (1 - (h.vector_embedding <=> '[{embedding_str}]'::vector)) > 0.5
            OR h.english_text ILIKE '%{safe_query}%'
            OR to_tsvector('english', h.english_text) @@ to_tsquery('english', '{simplified_query}')
        )
    """
    
    # Complete the query with ordering and limit
    sql += f"""
    ORDER BY similarity DESC
    LIMIT {limit} OFFSET {offset}
    """
    
    return sql

def _count_similar_hadiths(
    hadith_id: int,
    query_embedding: List[float],
    query_text: str
) -> int:
    """
    Get the total count of similar hadiths for pagination
    """
    # Convert the embedding to a PostgreSQL vector literal
    # Don't use json.dumps as it adds extra quotes
    embedding_str = str(query_embedding).replace('[', '').replace(']', '')
    
    # Prepare the text search query
    safe_query = query_text.replace("'", "''")
    
    # Create a simplified version of the query for text search
    words = safe_query.split()
    simplified_query = " & ".join([word for word in words if len(word) > 3])
    
    # If simplified query is empty, use the original query
    if not simplified_query:
        simplified_query = safe_query.replace(" ", " & ")
    
    # Build the count SQL query
    sql = f"""
    SELECT
        COUNT(*) AS total_count
    FROM
        hadiths h
        JOIN sources s ON h.source_id = s.id
    WHERE
        h.vector_embedding IS NOT NULL
        AND h.id != {hadith_id}  -- Exclude the source hadith
        AND (
            (1 - (h.vector_embedding <=> '[{embedding_str}]'::vector)) > 0.5
            OR h.english_text ILIKE '%{safe_query}%'
            OR to_tsvector('english', h.english_text) @@ to_tsquery('english', '{simplified_query}')
        )
    """
    
    try:
        # Execute the count query
        result = supabase.rpc("execute_sql", {"sql_query": sql}).execute()
        if result.data and len(result.data) > 0:
            return result.data[0].get('total_count', 0)
        return 0
    except Exception as e:
        logger.error(f"Error counting similar hadiths: {e}")
        return 0
