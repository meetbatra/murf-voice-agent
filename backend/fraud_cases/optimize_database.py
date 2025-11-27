import sqlite3
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "fraud_cases.db"

def optimize_database():
    """Add index and optimize database for faster lookups"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Add index on userName for faster lookups
    try:
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_username 
            ON fraud_cases(userName COLLATE NOCASE)
        """)
        print("✓ Created index on userName")
    except Exception as e:
        print(f"Index creation: {e}")
    
    # Analyze to update query planner statistics
    cursor.execute("ANALYZE")
    print("✓ Database analyzed")
    
    conn.commit()
    conn.close()
    print("✓ Database optimized!")

if __name__ == "__main__":
    optimize_database()
