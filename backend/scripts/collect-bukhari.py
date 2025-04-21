"""
Script to collect Sahih al-Bukhari hadiths from sunnah.com using respectful scraping

Usage:
    python collect-bukhari.py [--dry-run] [--book N] [--start-book N] [--debug]

Options:
    --dry-run      Run without saving to database
    --book N       Only scrape a specific book
    --start-book N Start scraping from book N onwards
    --debug        Enable debug logging
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
BASE_URL = "https://sunnah.com"
BUKHARI_URL = f"{BASE_URL}/bukhari"  # Base URL for Bukhari hadiths
SOURCE_ID = 1  # Assuming Bukhari has ID 1 in our sources table

# Default User Agent
DEFAULT_USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.114 Safari/537.36"
DEFAULT_SCRAPER_DELAY = 2  # seconds

# Configure command line arguments
parser = argparse.ArgumentParser(description='Scrape Sahih al-Bukhari hadiths from sunnah.com')
parser.add_argument('--dry-run', action='store_true', help='Run without saving to database')
parser.add_argument('--book', type=int, help='Only scrape a specific book')
parser.add_argument('--start-book', type=int, help='Start scraping from this book onwards')
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

def get_book_urls() -> List[Tuple[int, str, str]]:
    """Get the URLs for each book in Sahih al-Bukhari
    
    Returns a list of tuples containing:
    - book_num: The book number
    - book_title: The title of the book
    - book_url: URL to the book
    """
    soup = fetch_page(BUKHARI_URL)
    if not soup:
        return []
    
    book_links = []
    
    # Find all links to books
    # The format is typically: /bukhari/{book_number}
    book_link_elements = soup.find_all('a', href=lambda href: href and href.startswith('/bukhari/') and href.count('/') == 2)
    
    for link in book_link_elements:
        href = link.get('href', '')
        parts = href.split('/')
        
        if len(parts) >= 3:
            try:
                book_num = int(parts[2])
                book_title = link.text.strip()
                
                # Extract English title (before the Arabic part)
                english_title = book_title.split('كتاب')[0].strip() if 'كتاب' in book_title else book_title
                
                book_links.append((book_num, english_title, f"{BASE_URL}{href}"))
            except (ValueError, IndexError):
                continue
    
    return book_links

def get_hadith_urls(book_url: str, book_num: int) -> List[Tuple[int, str]]:
    """Get the URLs for each hadith in a book
    
    Returns a list of tuples containing:
    - hadith_num: The hadith number
    - hadith_url: URL to the hadith
    """
    soup = fetch_page(book_url)
    if not soup:
        return []
    
    hadith_links = []
    
    # Find all links to individual hadiths
    # The format is typically: /bukhari:{hadith_number}
    hadith_link_elements = soup.find_all('a', href=lambda href: href and href.startswith('/bukhari:'))
    
    for link in hadith_link_elements:
        href = link.get('href', '')
        parts = href.split(':')
        
        if len(parts) >= 2:
            try:
                hadith_num = int(parts[1])
                hadith_links.append((hadith_num, f"{BASE_URL}{href}"))
            except (ValueError, IndexError):
                continue
    
    return hadith_links

def parse_hadith_page(url: str, book_num: int, hadith_num: int) -> Optional[Dict]:
    """Parse a hadith page and extract the hadith content
    
    Returns a dictionary representing the hadith
    """
    soup = fetch_page(url)
    if not soup:
        return None
    
    try:
        # Extract the hadith text (English)
        hadith_text_element = soup.find('div', class_='text_details')
        if not hadith_text_element:
            logger.warning(f"Could not find hadith text element on {url}")
            return None
        
        english_text = hadith_text_element.get_text(strip=True)
        
        # Extract the Arabic text if available
        arabic_text = ""
        arabic_element = soup.find('div', class_='arabic_hadith_full')
        if arabic_element:
            arabic_text = arabic_element.get_text(strip=True)
        
        # Extract the narrator chain
        narrator_chain = ""
        # The narrators are in links that point to /narrator/ URLs
        # Debug the HTML structure to find narrators
        logger.debug(f"Looking for narrator links on {url}")
        
        # Find all narrator links - they appear after the hadith text
        narrator_links = soup.find_all('a', href=lambda href: href and '/narrator/' in href)
        
        if narrator_links:
            # Extract the narrator names and join them
            narrator_names = [link.text.strip() for link in narrator_links]
            logger.debug(f"Found {len(narrator_names)} narrators: {narrator_names}")
            narrator_chain = " → ".join(narrator_names)
        else:
            # Fallback method: try to find narrators in the text
            logger.debug("No narrator links found, trying alternative method")
            narrated_by_text = ""
            narrated_by_element = soup.find('div', class_='hadith_narrated')
            if narrated_by_element:
                narrated_by_text = narrated_by_element.get_text(strip=True)
                if narrated_by_text:
                    narrator_chain = narrated_by_text.replace("Narrated", "").strip()
            
        logger.debug(f"Extracted narrator chain: {narrator_chain}")
        
        # Extract chapter information
        chapter = 0
        chapter_element = soup.find('div', class_='chapter_title')
        if chapter_element:
            chapter_text = chapter_element.get_text(strip=True)
            # Try to extract chapter number from text
            try:
                chapter_parts = chapter_text.split(',')
                if len(chapter_parts) > 0:
                    chapter_num_text = chapter_parts[0].strip().split(' ')[-1]
                    chapter = int(chapter_num_text)
            except (ValueError, IndexError):
                pass
        
        # Create hadith object
        hadith = {
            "source_id": SOURCE_ID,
            "volume": 1,  # Sahih al-Bukhari is considered one volume in this structure
            "book": book_num,
            "chapter": chapter,
            "number": hadith_num,
            "arabic_text": arabic_text,
            "english_text": english_text,
            "narrator_chain": narrator_chain,
            "topics": [],  # No clear topic structure on sunnah.com
            "created_at": datetime.now().isoformat()
        }
        
        logger.debug(f"Created hadith object with number {hadith_num}")
        return hadith
        
    except Exception as e:
        logger.error(f"Error parsing hadith at {url}: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def save_hadith_to_db(hadith: Dict) -> bool:
    """Save a hadith to the database or to a JSON file in dry run mode"""
    if args.dry_run:
        # In dry run mode, just log the hadith
        logger.info(f"[DRY RUN] Would save hadith: {hadith['number']} from book {hadith['book']}")
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

def save_results_to_json(hadiths: List[Dict[str, Any]], filename: str = "bukhari_hadiths.json") -> None:
    """Save scraped hadiths to a JSON file"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(hadiths, f, ensure_ascii=False, indent=2)
        logger.info(f"Saved {len(hadiths)} hadiths to {filename}")
    except Exception as e:
        logger.error(f"Error saving to JSON file: {e}")

def ensure_source_exists() -> bool:
    """Check if Bukhari source exists in database, create if not"""
    if args.dry_run or supabase is None:
        return True
        
    try:
        source_check = supabase.table("sources").select("*").eq("name", "Sahih al-Bukhari").execute()
        
        if not source_check.data:
            logger.info("Creating Sahih al-Bukhari source entry...")
            source = {
                "name": "Sahih al-Bukhari",
                "tradition": "Sunni",
                "description": "Sahih al-Bukhari is a collection of hadith compiled by Imam Muhammad al-Bukhari (d. 256 AH/870 CE).",
                "compiler": "Muhammad ibn Ismail al-Bukhari",
                "created_at": datetime.now().isoformat()
            }
            supabase.table("sources").insert(source).execute()
        return True
    except Exception as e:
        logger.error(f"Error checking/creating source: {e}")
        return False

def main():
    """Main function to collect Sahih al-Bukhari hadiths"""
    # Check if source exists, create if not
    if not args.dry_run and not ensure_source_exists():
        logger.error("Failed to ensure source exists. Exiting.")
        return
    
    # Start collection process
    logger.info(f"Starting collection of Sahih al-Bukhari hadiths...")
    total_collected = 0
    all_collected_hadiths = []
    
    # Get book URLs
    book_urls = get_book_urls()
    logger.info(f"Found {len(book_urls)} books")
    
    # Filter to specific book if requested
    if args.book:
        book_urls = [b for b in book_urls if b[0] == args.book]
        if not book_urls:
            logger.error(f"Book {args.book} not found")
            return
        logger.info(f"Filtering to only book {args.book}")
    # Filter to start from a specific book if requested
    elif args.start_book:
        original_count = len(book_urls)
        book_urls = [b for b in book_urls if b[0] >= args.start_book]
        if not book_urls:
            logger.error(f"No books found with number >= {args.start_book}")
            return
        logger.info(f"Starting from book {args.start_book} onwards (filtered from {original_count} to {len(book_urls)} books)")
    
    # Process each book
    for book_num, book_title, book_url in book_urls:
        try:
            logger.info(f"Processing book {book_num}: {book_title}")
            
            # Get hadith URLs for this book
            hadith_urls = get_hadith_urls(book_url, book_num)
            logger.info(f"Found {len(hadith_urls)} hadiths in book {book_num}")
            
            # Process each hadith
            for hadith_num, hadith_url in hadith_urls:
                try:
                    # Add a small delay to be respectful to the server
                    time.sleep(random.uniform(DEFAULT_SCRAPER_DELAY * 0.5, DEFAULT_SCRAPER_DELAY * 1.5))
                    
                    logger.info(f"Processing hadith {hadith_num} from book {book_num}")
                    hadith = parse_hadith_page(hadith_url, book_num, hadith_num)
                    
                    if hadith:
                        # Save hadith to database or collect for dry run
                        if args.dry_run:
                            all_collected_hadiths.append(hadith)
                            logger.info(f"[DRY RUN] Collected hadith {hadith_num}")
                            total_collected += 1
                        else:
                            success = save_hadith_to_db(hadith)
                            if success:
                                total_collected += 1
                                logger.info(f"Successfully saved hadith {hadith_num} from book {book_num}")
                            else:
                                logger.warning(f"Failed to save hadith {hadith_num} from book {book_num}")
                    else:
                        logger.warning(f"Failed to parse hadith {hadith_num} from book {book_num}")
                
                except Exception as e:
                    logger.error(f"Error processing hadith {hadith_num} in book {book_num}: {e}")
                    continue
            
            logger.info(f"Completed book {book_num}")
        except Exception as e:
            logger.error(f"Error processing book {book_num}: {e}")
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