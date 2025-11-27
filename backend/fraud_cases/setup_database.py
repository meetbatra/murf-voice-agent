import sqlite3
import json
from pathlib import Path

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "fraud_cases.db"
JSON_PATH = SCRIPT_DIR / "fraud_cases.json"

def create_database():
    """Create the fraud cases SQLite database with schema"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create fraud_cases table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS fraud_cases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            userName TEXT NOT NULL UNIQUE,
            securityIdentifier TEXT NOT NULL,
            cardEnding TEXT NOT NULL,
            caseStatus TEXT NOT NULL DEFAULT 'pending',
            transactionName TEXT NOT NULL,
            transactionAmount REAL NOT NULL,
            transactionTime TEXT NOT NULL,
            transactionLocation TEXT NOT NULL,
            securityQuestion TEXT NOT NULL,
            securityAnswer TEXT NOT NULL,
            resolutionNotes TEXT,
            resolvedAt TEXT,
            createdAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    
    conn.commit()
    conn.close()
    print(f"✓ Database created at: {DB_PATH}")

def load_fraud_cases():
    """Load fraud cases from JSON file into the database"""
    if not JSON_PATH.exists():
        print(f"✗ JSON file not found at: {JSON_PATH}")
        return
    
    with open(JSON_PATH, 'r') as f:
        data = json.load(f)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cases_loaded = 0
    for case in data.get('cases', []):
        try:
            cursor.execute("""
                INSERT INTO fraud_cases (
                    userName, securityIdentifier, cardEnding, caseStatus,
                    transactionName, transactionAmount, transactionTime, transactionLocation,
                    securityQuestion, securityAnswer, resolutionNotes, resolvedAt
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                case['userName'],
                case['securityIdentifier'],
                case['cardEnding'],
                case['caseStatus'],
                case['transactionName'],
                case['transactionAmount'],
                case['transactionTime'],
                case['transactionLocation'],
                case['securityQuestion'],
                case['securityAnswer'],
                case.get('resolutionNotes'),
                case.get('resolvedAt')
            ))
            cases_loaded += 1
        except sqlite3.IntegrityError:
            print(f"⚠ Skipping duplicate case: {case['userName']}")
    
    conn.commit()
    conn.close()
    print(f"✓ Loaded {cases_loaded} fraud cases into database")

def verify_database():
    """Verify the database was created and populated correctly"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM fraud_cases")
    count = cursor.fetchone()[0]
    print(f"✓ Database contains {count} fraud cases")
    
    cursor.execute("SELECT userName, caseStatus FROM fraud_cases")
    cases = cursor.fetchall()
    print("\nFraud cases in database:")
    for userName, status in cases:
        print(f"  - {userName}: {status}")
    
    conn.close()

if __name__ == "__main__":
    print("Setting up fraud cases database...\n")
    create_database()
    load_fraud_cases()
    verify_database()
    print("\n✓ Database setup complete!")
