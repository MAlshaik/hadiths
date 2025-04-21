"""
Script to collect Al-Kafi hadiths from Thaqalayn.net using respectful scraping

Usage:
    python collect-kafi.py [--dry-run] [--volume N] [--debug]

Options:
    --dry-run    Run without saving to database
    --volume N   Only scrape volume N
    --debug      Enable debug logging
"""
import os
import sys
import time
import random
import json
import argparse
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# Scraping Constants
BASE_URL = "https://thaqalayn.net"
KAFI_URL = f"{BASE_URL}/book"  # Base URL for Al-Kafi books
SOURCE_ID = 2  # Assuming Al-Kafi has ID 2 in our sources table

# Default User Agent
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
DEFAULT_SCRAPER_DELAY = 2  # seconds

# Configure command line arguments
parser = argparse.ArgumentParser(description='Scrape Al-Kafi hadiths from Thaqalayn.net')
parser.add_argument('--dry-run', action='store_true', help='Run without saving to database')
parser.add_argument('--volume', type=int, help='Only scrape a specific volume')
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

# Only import database modules if not in dry run mode
supabase = None
if not args.dry_run:
    try:
        # Add the parent directory to the path so we can import from app
        sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
        from app.core.config import settings
        from app.db.database import supabase
        logger.info("Database connection initialized")
    except ImportError as e:
        logger.error(f"Error importing database modules: {e}")
        logger.warning("Falling back to dry run mode")
        args.dry_run = True
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        logger.warning("Falling back to dry run mode")
        args.dry_run = True

def get_request_headers() -> Dict[str, str]:
    """Get request headers for respectful scraping"""
    user_agent = DEFAULT_USER_AGENT
    if not args.dry_run and 'settings' in globals():
        user_agent = getattr(settings, 'USER_AGENT', DEFAULT_USER_AGENT)
    
    return {
        "User-Agent": user_agent,
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
        logger.debug(f"Fetching URL: {url}")
        response = requests.get(url, headers=get_request_headers(), timeout=30)
        response.raise_for_status()
        return BeautifulSoup(response.content, "html.parser")
    except requests.exceptions.RequestException as e:
        logger.error(f"Error fetching {url}: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error fetching {url}: {e}")
        return None

def get_volume_urls() -> List[Tuple[int, str]]:
    """Get the URLs for each volume of Al-Kafi"""
    # Al-Kafi has 8 volumes on thaqalayn.net
    volume_links = []
    for volume_num in range(1, 9):  # Volumes 1-8
        volume_links.append((volume_num, f"{KAFI_URL}/{volume_num}"))
    
    return volume_links

def get_book_urls(volume_url: str) -> List[Tuple[int, str, str]]:
    """Get the URLs for each book and chapter within a volume
    
    Returns a list of tuples containing:
    - book_num: The book number
    - book_title: The title of the book
    - chapter_url: URL to the chapter
    """
    soup = fetch_page(volume_url)
    if not soup:
        return []
    
    book_chapter_links = []
    
    # Find all links that match chapter patterns
    # The format is typically: /chapter/{volume}/{book}/{chapter}
    chapter_links = soup.find_all('a', href=lambda href: href and '/chapter/' in href)
    
    for link in chapter_links:
        href = link.get('href')
        if not href:
            continue
            
        # Extract volume, book, and chapter from URL
        parts = href.split('/')
        if len(parts) >= 4 and parts[1] == 'chapter':
            try:
                volume_num = int(parts[2])
                book_num = int(parts[3])
                chapter_num = int(parts[4]) if len(parts) > 4 else 0
                
                # Get the text which contains the chapter title
                chapter_text = link.text.strip()
                
                book_chapter_links.append((book_num, chapter_text, f"{BASE_URL}{href}"))
            except (ValueError, IndexError):
                continue
    
    return book_chapter_links

def get_hadith_urls(chapter_url: str) -> List[str]:
    """Get the hadiths from a chapter page
    
    On thaqalayn.net, hadiths are displayed directly on the chapter page,
    so we'll extract them from there.
    """
    soup = fetch_page(chapter_url)
    if not soup:
        return []
    
    # The chapter page contains the hadiths directly
    # We'll return the chapter URL itself as it contains all hadiths
    return [chapter_url]

def parse_hadith_page(url: str, volume: int, book: int) -> List[Dict]:
    """Parse a chapter page and extract all hadiths
    
    Returns a list of dictionaries, each representing a hadith
    """
    soup = fetch_page(url)
    if not soup:
        return []
    
    hadiths = []
    
    try:
        # Extract chapter information from URL
        # URL format is: /chapter/{volume}/{book}/{chapter}
        # Example: https://thaqalayn.net/chapter/1/1/0 (Volume 1, Book 1, Chapter 0)
        parts = url.split('/')
        
        # Debug the URL parts
        logger.debug(f"URL parts: {parts}")
        
        # For URL like https://thaqalayn.net/chapter/1/1/0
        # parts = ['https:', '', 'thaqalayn.net', 'chapter', '1', '1', '0']
        # volume is at index 4, book at index 5, chapter at index 6
        if len(parts) >= 7 and parts[3] == 'chapter':
            url_volume = int(parts[4])
            url_book = int(parts[5])
            url_chapter = int(parts[6])
            
            # Verify that volume and book match what was passed in
            if volume != url_volume:
                logger.warning(f"Volume mismatch: expected {volume}, found {url_volume} in URL {url}")
            
            if book != url_book:
                logger.warning(f"Book mismatch: expected {book}, found {url_book} in URL {url}")
                # Use the book from the URL as it's more likely to be correct
                book = url_book
            
            chapter_number = url_chapter
        else:
            # Fallback if URL doesn't match expected format
            logger.warning(f"URL doesn't match expected format: {url}")
            chapter_number = 0
        
        logger.debug(f"Processing volume {volume}, book {book}, chapter {chapter_number} from URL: {url}")
        
        # Find the Next.js data script that contains the hadiths JSON
        next_data_script = soup.find('script', {'id': '__NEXT_DATA__'})
        
        if not next_data_script:
            logger.error(f"No __NEXT_DATA__ script found on {url}")
            with open("debug_page.html", "w", encoding="utf-8") as f:
                f.write(str(soup))
            logger.debug("Saved HTML to debug_page.html for inspection")
            return []
        
        # Extract and parse the JSON data
        try:
            json_data = json.loads(next_data_script.string)
            logger.debug("Successfully parsed JSON data from __NEXT_DATA__ script")
            
            # Extract hadiths from the JSON structure
            page_props = json_data.get('props', {}).get('pageProps', {})
            json_hadiths = page_props.get('hadiths', [])
            
            if not json_hadiths:
                logger.warning(f"No hadiths found in JSON data for {url}")
                return []
            
            logger.info(f"Found {len(json_hadiths)} hadiths in JSON data")
            
            # Process each hadith
            for idx, hadith_data in enumerate(json_hadiths, 1):
                hadith_number = hadith_data.get('number', idx)
                
                # Extract Arabic and English content
                # The JSON typically has separate entries for Arabic and English versions
                # We need to find matching pairs
                if hadith_data.get('language') == 'AR':
                    arabic_text = hadith_data.get('content', '')
                    
                    # Look for the corresponding English translation
                    english_text = ""
                    for eng_hadith in json_hadiths:
                        if eng_hadith.get('language') == 'EN' and eng_hadith.get('number') == hadith_number:
                            english_text = eng_hadith.get('content', '')
                            break
                    
                    # Extract narrator chain (usually at the beginning of the Arabic text)
                    narrator_chain = ""
                    if arabic_text:
                        # Try to extract the chain of narrators from the beginning of the text
                        # This is usually the part before the actual hadith content
                        narrator_parts = arabic_text.split('قَالَ', 1)
                        if len(narrator_parts) > 1:
                            narrator_chain = narrator_parts[0].strip()
                    
                    # Extract topics from tags
                    topics = []
                    tags = hadith_data.get('tags', [])
                    for tag in tags:
                        if isinstance(tag, dict) and 'name' in tag:
                            topics.append(tag['name'])
                    
                    # Create hadith object
                    hadith = {
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
                    
                    logger.debug(f"Created hadith object with number {hadith_number}")
                    hadiths.append(hadith)
            
            logger.info(f"Extracted {len(hadiths)} hadiths from {url}")
            return hadiths
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON data: {e}")
            return []
            
    except Exception as e:
        logger.error(f"Error parsing hadiths at {url}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return []

def save_hadith_to_db(hadith: Dict) -> bool:
    """Save a hadith to the database or to a JSON file in dry run mode"""
    if args.dry_run:
        # In dry run mode, just log the hadith
        logger.info(f"[DRY RUN] Would save hadith: {hadith['number']} from volume {hadith['volume']}, book {hadith['book']}")
        return True
    
    try:
        if supabase is None:
            logger.error("Database connection not available")
            return False
        
        # First check if this hadith already exists
        source_id = hadith['source_id']
        volume = hadith['volume']
        book = hadith['book']
        chapter = hadith['chapter']
        number = hadith['number']
        
        logger.debug(f"Checking if hadith {number} already exists in database...")
        
        # Query to check if hadith exists
        existing = supabase.table("hadiths") \
            .select("id") \
            .eq("source_id", source_id) \
            .eq("volume", volume) \
            .eq("book", book) \
            .eq("chapter", chapter) \
            .eq("number", number) \
            .execute()
        
        # If hadith exists, update it instead of inserting
        if existing.data and len(existing.data) > 0:
            hadith_id = existing.data[0]['id']
            logger.info(f"Hadith {number} already exists with ID {hadith_id}, updating instead of inserting")
            
            # Update the existing record
            result = supabase.table("hadiths") \
                .update(hadith) \
                .eq("id", hadith_id) \
                .execute()
                
            logger.debug(f"Update result: {result}")
            return True
        
        # If hadith doesn't exist, insert it
        logger.debug(f"Inserting hadith {hadith['number']} into database...")
        result = supabase.table("hadiths").insert(hadith).execute()
        logger.debug(f"Database insertion result: {result}")
        
        # Verify the insertion was successful by checking the result
        if hasattr(result, 'data') and result.data:
            logger.info(f"Successfully inserted hadith {hadith['number']} into database with ID: {result.data[0].get('id', 'unknown')}")
            return True
        else:
            logger.warning(f"Insertion may have failed for hadith {hadith['number']}. Result: {result}")
            return False
            
    except Exception as e:
        # Handle 409 Conflict errors (duplicate key)
        if hasattr(e, 'response') and e.response and e.response.status_code == 409:
            logger.warning(f"Hadith {hadith['number']} already exists in database (409 Conflict)")
            return True  # Consider this a success since the data is already there
        
        logger.error(f"Error saving hadith: {e}")
        if hasattr(e, 'response') and e.response:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response headers: {e.response.headers}")
            logger.error(f"Response body: {e.response.text}")
        return False

def save_results_to_json(hadiths: List[Dict[str, Any]], filename: str = "kafi_hadiths.json") -> None:
    """Save scraped hadiths to a JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(hadiths, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(hadiths)} hadiths to {filename}")
    except Exception as e:
        logger.error(f"Error saving to JSON file: {e}")

def ensure_source_exists() -> bool:
    """Check if Al-Kafi source exists in database, create if not"""
    if args.dry_run or supabase is None:
        return True
        
    try:
        source_check = supabase.table("sources").select("*").eq("name", "Al-Kafi").execute()
        
        if not source_check.data:
            logger.info("Creating Al-Kafi source entry...")
            source = {
                "name": "Al-Kafi",
                "tradition": "Shia",
                "description": "Al-Kafi is one of the most influential Shia hadith collections compiled by Muhammad ibn Ya'qub al-Kulayni.",
                "compiler": "Muhammad ibn Ya'qub al-Kulayni",
                "created_at": datetime.now().isoformat()
            }
            supabase.table("sources").insert(source).execute()
        return True
    except Exception as e:
        logger.error(f"Error checking/creating source: {e}")
        return False

def main():
    """Main function to collect Al-Kafi hadiths"""
    # Check if source exists, create if not
    if not args.dry_run and not ensure_source_exists():
        logger.error("Failed to ensure source exists. Exiting.")
        return
    
    # Start collection process
    logger.info(f"Starting collection of Al-Kafi hadiths...")
    total_collected = 0
    all_collected_hadiths = []
    
    # Get volume URLs
    volume_urls = get_volume_urls()
    logger.info(f"Found {len(volume_urls)} volumes")
    
    # Filter to specific volume if requested
    if args.volume:
        volume_urls = [(num, url) for num, url in volume_urls if num == args.volume]
        if not volume_urls:
            logger.error(f"Volume {args.volume} not found")
            return
        logger.info(f"Filtered to volume {args.volume}")
    
    # Process all volumes (or just the specified one)
    for volume_num, volume_url in volume_urls:
        logger.info(f"Processing volume {volume_num}...")
        
        try:
            # Get book/chapter URLs for this volume
            book_chapter_urls = get_book_urls(volume_url)
            logger.info(f"Found {len(book_chapter_urls)} book chapters in volume {volume_num}")
            
            # Process all book chapters
            for book_num, chapter_title, chapter_url in book_chapter_urls:
                logger.info(f"Processing book {book_num}, chapter '{chapter_title}' in volume {volume_num}...")
                
                try:
                    # Get chapter URL (which contains the hadiths)
                    chapter_urls = get_hadith_urls(chapter_url)
                    
                    # Process each chapter page
                    for chapter_url in chapter_urls:
                        # Random delay between requests to be respectful
                        delay = DEFAULT_SCRAPER_DELAY
                        if not args.dry_run and 'settings' in globals():
                            delay = getattr(settings, 'SCRAPER_DELAY', DEFAULT_SCRAPER_DELAY)
                        
                        time.sleep(delay + random.uniform(0.5, 2.0))
                        
                        hadiths = parse_hadith_page(chapter_url, volume_num, book_num)
                        for hadith in hadiths:
                            if save_hadith_to_db(hadith):
                                total_collected += 1
                                if args.dry_run:
                                    all_collected_hadiths.append(hadith)
                                logger.info(f"Collected hadith {hadith['number']} from volume {volume_num}, book {hadith['book']}, chapter {hadith['chapter']}")
                    
                    logger.info(f"Completed book {book_num} chapter in volume {volume_num}")
                except Exception as e:
                    logger.error(f"Error processing book {book_num} in volume {volume_num}: {e}")
                    continue
            
            logger.info(f"Completed volume {volume_num}")
        except Exception as e:
            logger.error(f"Error processing volume {volume_num}: {e}")
            continue
    
    logger.info(f"Collection completed. Total hadiths collected: {total_collected}")
    
    # In dry run mode, save results to JSON
    if args.dry_run and all_collected_hadiths:
        save_results_to_json(all_collected_hadiths)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Script interrupted by user")
    except Exception as e:
        logger.error(f"Unhandled exception: {e}", exc_info=True)
