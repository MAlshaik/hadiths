"""
Script to initialize the database for the Hadith Similarity Search project
"""
import os
import sys
import asyncio

# Add the parent directory to the path so we can import from app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.db.database import initialize_database, supabase

async def main():
    """
    Initialize the database schema and create initial source entries
    """
    print("Initializing database...")
    success = await initialize_database()
    
    if not success:
        print("Failed to initialize database. Exiting.")
        return
    
    print("Database schema initialized successfully!")
    
    # Check and create source entries if they don't exist
    sources = [
        {
            "name": "Sahih Bukhari",
            "tradition": "Sunni",
            "description": "Sahih al-Bukhari is a collection of hadith compiled by Imam Muhammad al-Bukhari.",
            "compiler": "Muhammad ibn Ismail al-Bukhari"
        },
        {
            "name": "Al-Kafi",
            "tradition": "Shia",
            "description": "Al-Kafi is one of the most influential Shia hadith collections compiled by Muhammad ibn Ya'qub al-Kulayni.",
            "compiler": "Muhammad ibn Ya'qub al-Kulayni"
        }
    ]
    
    try:
        for source in sources:
            # Check if source already exists
            result = supabase.table("sources").select("*").eq("name", source["name"]).execute()
            
            if not result.data:
                print(f"Creating source entry for {source['name']}...")
                supabase.table("sources").insert(source).execute()
                print(f"Source entry for {source['name']} created successfully!")
            else:
                print(f"Source entry for {source['name']} already exists.")
    except Exception as e:
        print(f"Error creating sources: {e}")
    
    print("Database initialization complete!")

if __name__ == "__main__":
    asyncio.run(main())
