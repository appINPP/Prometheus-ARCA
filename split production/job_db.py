import sqlite3

def init_db(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS events (
        id INTEGER PRIMARY KEY,
        energy REAL,
        bin TEXT,
        status TEXT
    )
    """)

    conn.commit()
    conn.close()
    
def insert_events(db_path, energies, threshold):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    c.execute("DELETE FROM events")
    
    for i, E in enumerate(energies):
        bin_name = "low" if E < threshold else "high"

        c.execute("""
        INSERT OR REPLACE INTO events (id, energy, bin, status)
        VALUES (?, ?, ?, 'PENDING')
        """, (i, float(E), bin_name))

    conn.commit()
    conn.close() 
    
def claim_events(db_path, bin_name, limit=1000):
    conn = sqlite3.connect(db_path)
    # Wait up to 30 seconds if the DB is locked by another worker
    conn.execute("PRAGMA busy_timeout = 30000") 
    c = conn.cursor()

    ids = []
    try:
        # Lock the database for writing immediately
        c.execute("BEGIN IMMEDIATE")

        # Select the specific number of events requested
        c.execute("""
            SELECT id FROM events 
            WHERE status='PENDING' AND bin=? 
            LIMIT ?
        """, (bin_name, limit))
        
        ids = [r[0] for r in c.fetchall()]

        # If we found rows, mark them so no one else touches them
        if ids:
            c.executemany(
                "UPDATE events SET status='CLAIMED' WHERE id=?", 
                [(i,) for i in ids]
            )

        conn.commit() # Save changes and release lock
    except sqlite3.Error as e:
        conn.rollback()
        print(f"Database error: {e}")
    finally:
        conn.close()

    return ids
    
def mark_done(db_path, event_id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
        UPDATE events
        SET status='DONE'
        WHERE id=?
    """, (event_id,))

    conn.commit()
    conn.close()    
    
