from supabase import create_client, Client
from typing import Dict, List, Optional
import requests
import json

from app.core.config import settings

# Initialize Supabase client
supabase: Client = create_client(
    settings.SUPABASE_URL,
    settings.SUPABASE_KEY
)

async def initialize_database():
    """Initialize the database schema using Supabase SQL API"""
    try:
        # For Supabase, we can use the SQL API directly
        sql_api_url = f"{settings.SUPABASE_URL}/rest/v1/sql"
        headers = {
            "apikey": settings.SUPABASE_KEY,
            "Authorization": f"Bearer {settings.SUPABASE_KEY}",
            "Content-Type": "application/json",
            "Prefer": "resolution=merge-duplicates"
        }
        
        # Enable pgvector extension
        print("Enabling pgvector extension...")
        enable_vector_query = {
            "query": "CREATE EXTENSION IF NOT EXISTS vector;"
        }
        
        response = requests.post(sql_api_url, headers=headers, json=enable_vector_query)
        if response.status_code != 200:
            print(f"Error enabling pgvector: {response.text}")
            return False
        
        # Create sources table
        print("Creating sources table...")
        create_sources_query = {
            "query": """
            CREATE TABLE IF NOT EXISTS sources (
                id SERIAL PRIMARY KEY,
                name VARCHAR(255) NOT NULL,
                tradition VARCHAR(50) NOT NULL,
                description TEXT,
                compiler VARCHAR(255),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE
            );
            """
        }
        
        response = requests.post(sql_api_url, headers=headers, json=create_sources_query)
        if response.status_code != 200:
            print(f"Error creating sources table: {response.text}")
            return False
        
        # Create hadiths table
        print("Creating hadiths table...")
        create_hadiths_query = {
            "query": """
            CREATE TABLE IF NOT EXISTS hadiths (
                id SERIAL PRIMARY KEY,
                source_id INTEGER NOT NULL REFERENCES sources(id),
                volume INTEGER,
                book INTEGER,
                chapter INTEGER,
                number INTEGER,
                arabic_text TEXT NOT NULL,
                english_text TEXT,
                narrator_chain TEXT,
                topics TEXT[],
                vector_embedding vector(768),
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP WITH TIME ZONE,
                UNIQUE(source_id, volume, book, chapter, number)
            );
            """
        }
        
        response = requests.post(sql_api_url, headers=headers, json=create_hadiths_query)
        if response.status_code != 200:
            print(f"Error creating hadiths table: {response.text}")
            return False
        
        # Create vector index
        print("Creating vector index...")
        create_index_query = {
            "query": """
            CREATE INDEX IF NOT EXISTS hadiths_vector_embedding_idx ON hadiths
            USING hnsw (vector_embedding vector_cosine_ops)
            WITH (m = 16, ef_construction = 64);
            """
        }
        
        response = requests.post(sql_api_url, headers=headers, json=create_index_query)
        if response.status_code != 200:
            print(f"Error creating vector index: {response.text}")
            return False
        
        print("Database initialized successfully")
        return True
    except Exception as e:
        print(f"Error initializing database: {e}")
        return False

# Helper functions for working with the database
async def get_all_sources():
    """Get all sources from the database"""
    return supabase.table("sources").select("*").execute()

async def get_source_by_id(source_id: int):
    """Get a source by its ID"""
    return supabase.table("sources").select("*").eq("id", source_id).execute()

async def create_source(source_data: Dict):
    """Create a new source"""
    return supabase.table("sources").insert(source_data).execute()

async def create_hadith(hadith_data: Dict):
    """Create a new hadith"""
    return supabase.table("hadiths").insert(hadith_data).execute()

async def get_hadiths_by_source(source_id: int, limit: int = 100, offset: int = 0):
    """Get hadiths by source ID with pagination"""
    return supabase.table("hadiths") \
        .select("*") \
        .eq("source_id", source_id) \
        .range(offset, offset + limit - 1) \
        .execute()
