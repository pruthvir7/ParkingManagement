import sqlite3

# SQLite Database Configuration
DATABASE = 'parking.db'

# Initialize the database and create required tables
def initialize_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Create the reservations table (if not already created)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS reservations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_plate TEXT NOT NULL,
        lot_name TEXT NOT NULL,
        slot_name TEXT NOT NULL,
        reservation_expiry TIMESTAMP NOT NULL
    )
    ''')

    # Create the parking_sessions table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS parking_sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        license_plate TEXT NOT NULL,
        lot_name TEXT NOT NULL,
        slot_name TEXT NOT NULL,
        start_time TIMESTAMP NOT NULL,
        end_time TIMESTAMP NOT NULL,
        duration REAL NOT NULL
    )
    ''')

    conn.commit()
    conn.close()
    print("Database initialized successfully!")

# Run the initialization
if __name__ == "__main__":
    initialize_db()
