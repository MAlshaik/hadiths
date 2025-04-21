"""
Script to generate embeddings for hadiths in the database using AraBERT

Usage:
    python generate-embeddings.py [--batch-size N] [--source-id N] [--dry-run] [--debug]

Options:
    --batch-size N    Process N hadiths at a time (default: 32)
    --source-id N     Only process hadiths from a specific source
    --dry-run         Run without updating the database
    --debug           Enable debug logging
"""
import os
import sys
import time
import argparse
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import torch
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from pyarabic import araby

# Configure command line arguments
parser = argparse.ArgumentParser(description='Generate embeddings for hadiths using AraBERT')
parser.add_argument('--batch-size', type=int, default=32, help='Process N hadiths at a time')
parser.add_argument('--source-id', type=int, help='Only process hadiths from a specific source')
parser.add_argument('--dry-run', action='store_true', help='Run without updating the database')
parser.add_argument('--debug', action='store_true', help='Enable debug logging')

# Parse arguments
args = parser.parse_args()

# Setup logging
import logging
logging.basicConfig(
    level=logging.DEBUG if args.debug else logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from app.core.config import settings
from app.db.database import supabase

# Initialize the embedding model
def init_model():
    """Initialize and return the AraBERT model"""
    logger.info("Initializing AraBERT model...")
    # Use a sentence transformer version of AraBERT
    model_name = "UBC-NLP/ARBERT"  # Alternative: "aubmindlab/bert-base-arabertv02"
    model = SentenceTransformer(model_name)
    logger.info(f"Model {model_name} loaded successfully")
    return model

def normalize_arabic_text(text: str) -> str:
    """Normalize Arabic text by removing diacritics and standardizing characters"""
    if not text:
        return ""
    
    # Remove Arabic diacritics (tashkeel)
    text = araby.strip_tashkeel(text)
    # Remove tatweel (stretching character)
    text = araby.strip_tatweel(text)
    # Normalize Alef and Hamza
    text = araby.normalize_alef(text)
    text = araby.normalize_hamza(text)
    
    # Manual normalization for Yeh (since araby.normalize_yeh is missing)
    # Replace Farsi Yeh (ی) with Arabic Yeh (ي)
    text = text.replace('\u06cc', '\u064a')
    # Replace Alef Maksura (ى) with Arabic Yeh (ي)
    text = text.replace('\u0649', '\u064a')
    
    return text

def get_hadiths_without_embeddings(source_id: Optional[int] = None, batch_size: int = 32, offset: int = 0) -> List[Dict]:
    """Get hadiths that don't have embeddings yet"""
    try:
        query = supabase.table("hadiths").select("*").is_("vector_embedding", "null")
        
        # Add source filter if specified
        if source_id is not None:
            query = query.eq("source_id", source_id)
        
        # Add limit and offset for batch processing
        result = query.range(offset, offset + batch_size - 1).execute()
        
        return result.data
    except Exception as e:
        logger.error(f"Error fetching hadiths: {e}")
        return []

def count_hadiths_without_embeddings(source_id: Optional[int] = None) -> int:
    """Count how many hadiths don't have embeddings yet"""
    try:
        query = supabase.table("hadiths").select("id", count="exact").is_("vector_embedding", "null")
        
        # Add source filter if specified
        if source_id is not None:
            query = query.eq("source_id", source_id)
        
        result = query.execute()
        
        # The count is in the response metadata
        return result.count
    except Exception as e:
        logger.error(f"Error counting hadiths: {e}")
        return 0

def generate_embedding(model: SentenceTransformer, text: str) -> List[float]:
    """Generate an embedding for the given text"""
    # Normalize the text first
    normalized_text = normalize_arabic_text(text)
    
    if not normalized_text:
        logger.warning("Empty text after normalization")
        # Return a zero vector as fallback
        return [0.0] * 768
    
    # Generate embedding
    embedding = model.encode(normalized_text)
    
    # Convert numpy array to Python list for database storage
    return embedding.tolist()

def update_hadith_embedding(hadith_id: int, embedding: List[float]) -> bool:
    """Update a hadith with its embedding vector"""
    if args.dry_run:
        logger.info(f"[DRY RUN] Would update hadith {hadith_id} with embedding")
        return True
    
    try:
        # Update the hadith with its embedding
        result = supabase.table("hadiths") \
            .update({"vector_embedding": embedding, "updated_at": datetime.now().isoformat()}) \
            .eq("id", hadith_id) \
            .execute()
        
        return True
    except Exception as e:
        logger.error(f"Error updating hadith {hadith_id}: {e}")
        return False

def save_embeddings_to_json(hadith_embeddings: List[Dict], filename: str = "hadith_embeddings.json") -> None:
    """Save generated embeddings to a JSON file (used in dry run mode)"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            # Don't include the full vector in the output to save space
            simplified_data = []
            for item in hadith_embeddings:
                simplified_item = {
                    "hadith_id": item["hadith_id"],
                    "embedding_length": len(item["embedding"]) if "embedding" in item else 0,
                    "embedding_sample": item["embedding"][:5] if "embedding" in item else [],
                    "text_sample": item["text"][:50] if "text" in item else ""
                }
                simplified_data.append(simplified_item)
            
            json.dump(simplified_data, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(hadith_embeddings)} embedding summaries to {filename}")
    except Exception as e:
        logger.error(f"Error saving to JSON file: {e}")

def process_batch(model: SentenceTransformer, hadiths: List[Dict]) -> List[Dict]:
    """Process a batch of hadiths to generate and update embeddings"""
    results = []
    
    for hadith in hadiths:
        hadith_id = hadith["id"]
        
        # Prefer Arabic text, fall back to English if Arabic is not available
        text_to_embed = hadith.get("arabic_text", "")
        if not text_to_embed:
            text_to_embed = hadith.get("english_text", "")
            logger.warning(f"Using English text for hadith {hadith_id} as Arabic text is empty")
        
        if not text_to_embed:
            logger.error(f"Hadith {hadith_id} has no text to embed, skipping")
            continue
        
        # Generate embedding
        try:
            embedding = generate_embedding(model, text_to_embed)
            
            # Update the hadith in the database
            success = update_hadith_embedding(hadith_id, embedding)
            
            if success:
                results.append({
                    "hadith_id": hadith_id,
                    "text": text_to_embed[:100] + "...",  # Just store a sample of the text
                    "embedding": embedding
                })
                logger.info(f"Successfully generated and updated embedding for hadith {hadith_id}")
            else:
                logger.warning(f"Failed to update embedding for hadith {hadith_id}")
        
        except Exception as e:
            logger.error(f"Error processing hadith {hadith_id}: {e}")
    
    return results

def main():
    """Main function to generate embeddings for hadiths"""
    # Check if we're in dry run mode
    if args.dry_run:
        logger.info("Running in dry run mode (no database updates)")
    
    # Initialize the model
    model = init_model()
    
    # Count how many hadiths need embeddings
    total_count = count_hadiths_without_embeddings(args.source_id)
    logger.info(f"Found {total_count} hadiths without embeddings")
    
    if total_count == 0:
        logger.info("No hadiths need embeddings. Exiting.")
        return
    
    # Process hadiths in batches
    batch_size = args.batch_size
    all_results = []
    
    # Calculate number of batches
    num_batches = (total_count + batch_size - 1) // batch_size
    
    for batch_idx in tqdm(range(num_batches), desc="Processing batches"):
        offset = batch_idx * batch_size
        
        # Get a batch of hadiths
        hadiths = get_hadiths_without_embeddings(args.source_id, batch_size, offset)
        
        if not hadiths:
            logger.info(f"No more hadiths to process at offset {offset}")
            break
        
        logger.info(f"Processing batch {batch_idx+1}/{num_batches} with {len(hadiths)} hadiths")
        
        # Process the batch
        batch_results = process_batch(model, hadiths)
        all_results.extend(batch_results)
        
        # Add a small delay between batches to avoid overloading the database
        if batch_idx < num_batches - 1:
            time.sleep(1)
    
    logger.info(f"Processed {len(all_results)} hadiths")
    
    # In dry run mode, save results to JSON
    if args.dry_run and all_results:
        save_embeddings_to_json(all_results)
    
    logger.info("Embedding generation completed")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
        import traceback
        logger.error(traceback.format_exc())