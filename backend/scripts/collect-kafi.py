#!/usr/bin/env python3
"""
Script to collect Al-Kafi hadiths from Thaqalayn.net using respectful scraping
"""
import os
import sys
import time
import random
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import settings
from app.db.database import supabase

# Scraping Constants
BASE_URL = "https://thaqalayn.net"
KAFI_URL = f"{BASE_URL}/hadith/al-kafi"
SOURCE_ID = 2  # Assuming Al-Kafi has ID 2 in our sources table

def get_request_headers() -> Dict[str, str]:
    """Get request headers for respectful scraping"""
    return {
        "User-Agent": settings.USER_AGENT,
        "Accept": "text/html,application/xhtml+xml,application/xml",
        "Accept-Language": "en-US,en;q=0.9",
        "Connection": "keep-alive",
    }

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(requests.exceptions.RequestException)
)
def fetch_page(url: str) -> Optional[BeautifulSoup]:
    """Fetch a page with exponential backoff retry"""
    try:
        response = requests.get(url, headers=get_request_headers(), timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        print(f"Error fetching {url}: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error fetching {url}: {e}")
        return None

def get_volume_urls() -> List[Tuple[int, str]]:
    """Get the URLs for each volume of Al-Kafi"""
    soup = fetch_page(KAFI_URL)
    if not soup:
        return []
    
    volume_links = []
    # Find volume links - specific implementation will depend on the site structure
    # This is a placeholder based on the expected structure
    for link in soup.select(".volume-links a"):
        volume_num = int(link.text.strip().split()[1])
        href = link.get("href")
        if href:
            volume_links.append((volume_num, f"{BASE_URL}{href}"))
    
    # If the above doesn't work with the actual site structure, a manual approach:
    if not volume_links:
        volume_links = [
            (1, f"{KAFI_URL}/volume-1"),
            (2, f"{KAFI_URL}/volume-2"),
            (3, f"{KAFI_URL}/volume-3"),
            (4, f"{KAFI_URL}/volume-4"),
            (5, f"{KAFI_URL}/volume-5"),
            (6, f"{KAFI_URL}/volume-6"),
            (7, f"{KAFI_URL}/volume-7"),
            (8, f"{KAFI_URL}/volume-8"),
        ]
    
    return volume_links

def get_book_urls(volume_url: str) -> List[Tuple[int, str]]:
    """Get the URLs for each book within a volume"""
    soup = fetch_page(volume_url)
    if not soup:
        return []
    
    book_links = []
    # Find book links - specific implementation will depend on the site structure
    for link in soup.select(".book-links a"):
        book_num = int(link.text.strip().split()[1])
        href = link.get("href")
        if href:
            book_links.append((book_num, f"{BASE_URL}{href}"))
    
    return book_links

def get_hadith_urls(book_url: str) -> List[str]:
    """Get the URLs for each hadith within a book"""
    soup = fetch_page(book_url)
    if not soup:
        return []
    
    hadith_links = []
    # Find hadith links - specific implementation will depend on the site structure
    for link in soup.select(".hadith-links a"):
        href = link.get("href")
        if href:
            hadith_links.append(f"{BASE_URL}{href}")
    
    return hadith_links

def parse_hadith_page(url: str, volume: int, book: int) -> Optional[Dict]:
    """Parse a hadith page and extract the relevant information"""
    soup = fetch_page(url)
    if not soup:
        return None
    
    try:
        # Extract hadith number
        hadith_number = 0
        number_element = soup.select_one(".hadith-number")
        if number_element:
            # Extract number from text like "Hadith #123"
            number_text = number_element.text.strip()
            hadith_number = int(number_text.split("#")[1]) if "#" in number_text else 0
        
        # Extract Arabic text
        arabic_element = soup.select_one(".arabic-text")
        arabic_text = arabic_element.text.strip() if arabic_element else ""
        
        # Extract English translation
        english_element = soup.select_one(".english-text")
        english_text = english_element.text.strip() if english_element else ""
        
        # Extract narrator chain
        narrator_element = soup.select_one(".narrator")
        narrator_chain = narrator_element.text.strip() if narrator_element else ""
        
        # Extract chapter information
        chapter_element = soup.select_one(".chapter-info")
        chapter_number = 0
        if chapter_element:
            chapter_text = chapter_element.text.strip()
            # Extract chapter number if available
            if "Chapter" in chapter_text and ":" in chapter_text:
                chapter_part = chapter_text.split(":")[0]
                chapter_number = int(chapter_part.split()[-1]) if chapter_part.split()[-1].isdigit() else 0
        
        # Extract topics if available
        topics = []
        topics_element = soup.select_one(".topics")
        if topics_element:
            topic_tags = topics_element.select("a")
            topics = [tag.text.strip() for tag in topic_tags]
        
        return {
            "source_id": SOURCE_ID,
            "volume": volume,
            "book": book,
            "chapter": chapter_number,
            "number": hadith_number,
            "arabic_text": arabic_text,
            "english_text": english_text,
            "narrator_chain": narrator_chain,
            "topics": topics,
            "created_at": datetime.now().isoformat()
        }
    except Exception as e:
        print(f"Error parsing hadith at {url}: {e}")
        return None

def save_hadith_to_db(hadith: Dict) -> bool:
    """Save a hadith to the database"""
    try:
        result = supabase.table("hadiths").insert(hadith).execute()
        return True
    except Exception as e:
        print(f"Error saving hadith: {e}")
        return False

def main():
    """Main function to collect Al-Kafi hadiths"""
    # Check if source exists, create if not
    source_check = supabase.table("sources").select("*").eq("name", "Al-Kafi").execute()
    
    if not source_check.data:
        print("Creating Al-Kafi source entry...")
        source = {
            "name": "Al-Kafi",
            "tradition": "Shia",
            "description": "Al-Kafi is one of the most influential Shia hadith collections compiled by Muhammad ibn Ya'qub al-Kulayni.",
            "compiler": "Muhammad ibn Ya'qub al-Kulayni",
            "created_at": datetime.now().isoformat()
        }
        supabase.table("sources").insert(source).execute()
    
    # Start collection process
    print(f"Starting collection of Al-Kafi hadiths...")
    total_collected = 0
    
    # Get volume URLs
    volume_urls = get_volume_urls()
    print(f"Found {len(volume_urls)} volumes")
    
    # For testing purposes, limit to one volume
    # In production, process all volumes
    for volume_num, volume_url in volume_urls[:1]:  # Just first volume for testing
        print(f"Processing volume {volume_num}...")
        
        # Get book URLs for this volume
        book_urls = get_book_urls(volume_url)
        print(f"Found {len(book_urls)} books in volume {volume_num}")
        
        # For testing purposes, limit to one book
        # In production, process all books
        for book_num, book_url in book_urls[:1]:  # Just first book for testing
            print(f"Processing book {book_num} in volume {volume_num}...")
            
            # Get hadith URLs for this book
            hadith_urls = get_hadith_urls(book_url)
            print(f"Found {len(hadith_urls)} hadiths in book {book_num}")
            
            # Process each hadith
            for hadith_url in hadith_urls:
                # Random delay between requests to be respectful
                time.sleep(settings.SCRAPER_DELAY + random.uniform(0.5, 2.0))
                
                hadith = parse_hadith_page(hadith_url, volume_num, book_num)
                if hadith and save_hadith_to_db(hadith):
                    total_collected += 1
                    print(f"Collected hadith {hadith['number']} from volume {volume_num}, book {book_num}")
                
            print(f"Completed book {book_num} in volume {volume_num}")
        
        print(f"Completed volume {volume_num}")
    
    print(f"Collection completed. Total hadiths collected: {total_collected}")

if __name__ == "__main__":
    main()
