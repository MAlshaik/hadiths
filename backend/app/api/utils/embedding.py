"""
Utility functions for generating text embeddings
"""
import os
from typing import List, Dict, Any
from functools import lru_cache
import numpy as np
from sentence_transformers import SentenceTransformer
from pyarabic import araby

@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """
    Get the embedding model (with caching to avoid loading multiple times)
    """
    # Use a sentence transformer version of AraBERT
    model_name = "UBC-NLP/ARBERT"  # Alternative: "aubmindlab/bert-base-arabertv02"
    model = SentenceTransformer(model_name)
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

def generate_embedding(model: SentenceTransformer, text: str) -> List[float]:
    """Generate an embedding for the given text"""
    # Normalize the text first
    normalized_text = normalize_arabic_text(text)
    
    if not normalized_text:
        # If we're left with empty text after normalization, use the original
        # This is a fallback to handle cases where normalization might strip everything
        normalized_text = text
    
    # Generate embedding
    embedding = model.encode(normalized_text)
    
    # Convert numpy array to Python list for database storage
    return embedding.tolist()
