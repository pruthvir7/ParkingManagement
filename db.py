import sqlite3
from datetime import datetime

DATABASE = "parking.db"

def insert_new_parking_session(license_plate, lot_name, slot_name):
    """
    Inserts a new row into the parking_sessions table.
    """
    conn = sqlite3.connect(DATABASE)
    try:
        cursor = conn.cursor()

        # Insert the new row
        cursor.execute('''
            INSERT INTO parking_sessions (license_plate, lot_name, slot_name, start_time, end_time, duration, paid)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            license_plate,
            lot_name,
            slot_name,
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),  # Current timestamp for start_time
            None,  # No end_time yet
            None,  # No duration yet
            0      # Not paid yet
        ))

        # Commit the changes
        conn.commit()
        print(f"New parking session added: {license_plate} in {lot_name}, {slot_name}")
    except sqlite3.Error as e:
        print(f"Error inserting new parking session: {e}")
    finally:
        conn.close()

# Example usage
if __name__ == "__main__":
    # Add a new parking session
    insert_new_parking_session("CC 19 EW 0001", "Lot_A", "Slot_1")
