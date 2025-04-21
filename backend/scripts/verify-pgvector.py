"""
Script to verify pgvector is properly set up in the database
"""
import os
import sys
import asyncio

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import supabase

async def verify_pgvector():
    """
    Verify that pgvector extension is enabled and the hadiths table has
    the vector_embedding column
    """
    try:
        # Check if pgvector extension is enabled
        print("Checking pgvector extension...")
        result = supabase.rpc(
            "sql", 
            { "query": "SELECT * FROM pg_extension WHERE extname = 'vector';" }
        ).execute()
        
        if not result.data or len(result.data) == 0:
            print("ERROR: pgvector extension is not enabled!")
            return False
        else:
            print("✅ pgvector extension is enabled")
        
        # Check if hadiths table has vector_embedding column
        print("Checking vector_embedding column...")
        result = supabase.rpc(
            "sql",
            { "query": """
              SELECT column_name, data_type 
              FROM information_schema.columns 
              WHERE table_name = 'hadiths' AND column_name = 'vector_embedding';
              """
            }
        ).execute()
        
        if not result.data or len(result.data) == 0:
            print("ERROR: vector_embedding column not found in hadiths table!")
            return False
        else:
            print("✅ vector_embedding column exists in hadiths table")
        
        # Check if vector index exists
        print("Checking vector index...")
        result = supabase.rpc(
            "sql",
            { "query": """
              SELECT indexname FROM pg_indexes 
              WHERE tablename = 'hadiths' AND indexname = 'hadiths_vector_embedding_idx';
              """
            }
        ).execute()
        
        if not result.data or len(result.data) == 0:
            print("WARNING: vector index not found. Vector searches will be slow.")
            print("Run the following SQL to create the index:")
            print("""
            CREATE INDEX hadiths_vector_embedding_idx ON hadiths
            USING hnsw (vector_embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            """)
        else:
            print("✅ vector index exists")
        
        # Test a simple vector operation
        print("Testing a simple vector operation...")
        test_vector = [0.1] * 768  # Create a sample 768-dimensional vector
        
        # Try to perform a simple vector operation
        result = supabase.rpc(
            "sql",
            { "query": """
              SELECT '[0.1, 0.1, 0.1]'::vector(3) <-> '[0.2, 0.2, 0.2]'::vector(3) as distance;
              """
            }
        ).execute()
        
        if result.data and len(result.data) > 0:
            print(f"✅ Vector operations working. Sample distance: {result.data[0]['distance']}")
        else:
            print("ERROR: Vector operations test failed")
            return False
        
        print("All pgvector checks passed! Your database is ready for vector similarity search.")
        return True
        
    except Exception as e:
        print(f"Error verifying pgvector: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(verify_pgvector())