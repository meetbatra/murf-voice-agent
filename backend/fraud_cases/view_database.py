import sqlite3
from pathlib import Path
from datetime import datetime

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
DB_PATH = SCRIPT_DIR / "fraud_cases.db"

def view_all_cases():
    """View all fraud cases in the database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM fraud_cases ORDER BY id")
    cases = cursor.fetchall()
    
    print(f"\n{'='*80}")
    print(f"FRAUD CASES DATABASE - {len(cases)} cases")
    print(f"{'='*80}\n")
    
    for case in cases:
        print(f"ID: {case['id']}")
        print(f"Name: {case['userName']}")
        print(f"Card: ****{case['cardEnding']}")
        print(f"Status: {case['caseStatus']}")
        print(f"Transaction: {case['transactionName']}")
        print(f"Amount: ${case['transactionAmount']}")
        print(f"Time: {case['transactionTime']}")
        print(f"Location: {case['transactionLocation']}")
        print(f"Security Question: {case['securityQuestion']}")
        print(f"Security Answer: {case['securityAnswer']}")
        
        if case['resolutionNotes']:
            print(f"Resolution: {case['resolutionNotes']}")
        if case['resolvedAt']:
            print(f"Resolved At: {case['resolvedAt']}")
        
        print(f"Created: {case['createdAt']}")
        print(f"Updated: {case['updatedAt']}")
        print(f"{'-'*80}\n")
    
    conn.close()

def reset_all_cases():
    """Reset all cases to pending status"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE fraud_cases 
        SET caseStatus = 'pending',
            resolutionNotes = NULL,
            resolvedAt = NULL,
            updatedAt = CURRENT_TIMESTAMP
    """)
    
    rows_updated = cursor.rowcount
    conn.commit()
    conn.close()
    
    print(f"\n✓ Reset {rows_updated} cases to 'pending' status\n")

def view_case_by_name(name: str):
    """View a specific case by name"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM fraud_cases WHERE LOWER(userName) = LOWER(?)", (name,))
    case = cursor.fetchone()
    
    if not case:
        print(f"\n✗ No case found for: {name}\n")
        conn.close()
        return
    
    print(f"\n{'='*80}")
    print(f"FRAUD CASE DETAILS")
    print(f"{'='*80}\n")
    
    print(f"ID: {case['id']}")
    print(f"Name: {case['userName']}")
    print(f"Security ID: {case['securityIdentifier']}")
    print(f"Card: ****{case['cardEnding']}")
    print(f"Status: {case['caseStatus']}")
    print(f"\nTransaction Details:")
    print(f"  Name: {case['transactionName']}")
    print(f"  Amount: ${case['transactionAmount']}")
    print(f"  Time: {case['transactionTime']}")
    print(f"  Location: {case['transactionLocation']}")
    print(f"\nSecurity Verification:")
    print(f"  Question: {case['securityQuestion']}")
    print(f"  Answer: {case['securityAnswer']}")
    
    if case['resolutionNotes']:
        print(f"\nResolution:")
        print(f"  Notes: {case['resolutionNotes']}")
        print(f"  Resolved At: {case['resolvedAt']}")
    
    print(f"\nTimestamps:")
    print(f"  Created: {case['createdAt']}")
    print(f"  Updated: {case['updatedAt']}")
    print(f"\n{'='*80}\n")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "reset":
            reset_all_cases()
            view_all_cases()
        elif command == "view" and len(sys.argv) > 2:
            name = " ".join(sys.argv[2:])
            view_case_by_name(name)
        else:
            print("\nUsage:")
            print("  python view_database.py              - View all cases")
            print("  python view_database.py reset        - Reset all cases to pending")
            print("  python view_database.py view <name>  - View specific case by name")
            print("\nExamples:")
            print("  python view_database.py view Mike Chen")
            print("  python view_database.py reset\n")
    else:
        view_all_cases()
