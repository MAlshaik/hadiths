from supabase import create_client, Client
from drizzle_orm import PostgresDatabase
from drizzle_orm.pg import *
from drizzle_orm.pg.vector import Vector
from drizzle_orm.schema import create_table, index
from datetime import datetime
from typing import Optional, List

from app.core.config import settings

# Initialize Supabase client
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

# Initialize Drizzle ORM with Supabase connection
# Note: We'll need to use the Supabase client's underlying PostgreSQL connection
# This is a simplified example - in a real implementation, you'd get the actual connection
db = PostgresDatabase(supabase)

# Define Sources table schema
class SourcesTable(Table):
    __tablename__ = "sources"
    
    id = serial("id").primary_key()
    name = varchar("name", length=255).not_null()
    tradition = varchar("tradition", length=50).not_null()
    description = text("description")
    compiler = varchar("compiler", length=255)
    created_at = timestamp("created_at").default(sql_fn.now())
    updated_at = timestamp("updated_at")

# Define Hadiths table schema
class HadithsTable(Table):
    __tablename__ = "hadiths"
    
    id = serial("id").primary_key()
    source_id = int("source_id").not_null().references(SourcesTable.id)
    volume = int("volume")
    book = int("book")
    chapter = int("chapter")
    number = int("number")
    arabic_text = text("arabic_text").not_null()
    english_text = text("english_text")
    narrator_chain = text("narrator_chain")
    topics = array("topics").of(text)
    vector_embedding = Vector("vector_embedding", 768)  # 768-dimensional vector for embedding
    created_at = timestamp("created_at").default(sql_fn.now())
    updated_at = timestamp("updated_at")
    
    # Define a unique constraint on source_id + volume + book + chapter + number
    __constraints__ = [
        UniqueConstraint("source_id", "volume", "book", "chapter", "number", name="unique_hadith_identifier")
    ]

# Create vector index on hadiths.vector_embedding
vector_index = index("hadiths_vector_idx").on(
    HadithsTable.vector_embedding.hnsw(
        m=16,  # max connections per element during indexing
        ef_construction=64  # size of dynamic candidate list for indexing
    )
)

async def initialize_database():
    """Initialize the database schema if it doesn't exist"""
    try:
        # Enable pgvector extension
        await supabase.postgrest.rpc("exec", {
            "query": "CREATE EXTENSION IF NOT EXISTS vector;"
        }).execute()
        
        # Use Drizzle to create tables
        db.create_tables([SourcesTable, HadithsTable])
        
        # Create vector index
        db.execute(vector_index)
        
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

# Helper functions for working with the database
def get_all_sources():
    """Get all sources from the database"""
    return db.select(SourcesTable).execute()

def get_source_by_id(source_id: int):
    """Get a source by its ID"""
    return db.select(SourcesTable).where(SourcesTable.id == source_id).first()

def create_source(source_data: dict):
    """Create a new source"""
    return db.insert(SourcesTable).values(**source_data).returning().execute()

def create_hadith(hadith_data: dict):
    """Create a new hadith"""
    return db.insert(HadithsTable).values(**hadith_data).returning().execute()

def get_hadiths_by_source(source_id: int, limit: int = 100, offset: int = 0):
    """Get hadiths by source ID with pagination"""
    return db.select(HadithsTable).where(
        HadithsTable.source_id == source_id
    ).limit(limit).offset(offset).execute()
