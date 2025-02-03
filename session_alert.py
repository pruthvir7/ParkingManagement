import pymysql
import time
import os
from app import send_alert  # Import the existing send_alert function
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get AWS RDS credentials from .env
RDS_HOST = os.getenv('RDS_HOST')
RDS_USER = os.getenv('RDS_USER')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_DB_NAME = os.getenv('RDS_DB_NAME')

EXPECTED_PLATE = "KA 18 EQ 0001"  # Replace with the expected plate
PHONE_NUMBER = "+919741078794"  # Replace with your desired phone number


def get_db_connection():
    """Establishes and returns a database connection."""
    try:
        conn = pymysql.connect(
            host=RDS_HOST,
            user=RDS_USER,
            password=RDS_PASSWORD,
            db=RDS_DB_NAME,
            cursorclass=pymysql.cursors.DictCursor
        )
        return conn
    except pymysql.MySQLError as e:
        print(f"Error connecting to the database: {e}")
        return None


def create_processed_sessions_table():
    """Creates the processed_sessions table if it does not already exist."""
    conn = get_db_connection()
    if conn:
        with conn.cursor() as cursor:
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS processed_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    license_plate VARCHAR(255) NOT NULL,
                    lot_name VARCHAR(255) NOT NULL,
                    slot_name VARCHAR(255) NOT NULL,
                    start_time TIMESTAMP NOT NULL,
                    processed_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            conn.commit()
        conn.close()


def insert_parking_session(license_plate, lot_name, slot_name, start_time):
    """Adds a new row to the parking_sessions table."""
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cursor:
                cursor.execute('''
                    INSERT INTO parking_sessions (license_plate, lot_name, slot_name, start_time, end_time, paid)
                    VALUES (%s, %s, %s, %s, NULL, 0)
                ''', (license_plate, lot_name, slot_name, start_time))
                conn.commit()
                print(f"Inserted new parking session: {license_plate}, Lot: {lot_name}, Slot: {slot_name}, Start Time: {start_time}")
        except Exception as e:
            print(f"Error inserting new parking session: {e}")
        finally:
            conn.close()


def process_sessions():
    """Checks for mismatched license plates and sends alerts."""
    create_processed_sessions_table()

    while True:
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cursor:
                # Query all unprocessed active sessions
                cursor.execute('''
                    SELECT ps.id, ps.license_plate AS detected_plate, ps.lot_name, ps.slot_name, ps.start_time,
                           %s AS expected_plate
                    FROM parking_sessions ps
                    WHERE ps.end_time IS NULL
                      AND ps.id NOT IN (SELECT id FROM processed_sessions)
                ''', (EXPECTED_PLATE,))
                sessions = cursor.fetchall()

                for session in sessions:
                    row_id = session["id"]
                    detected_plate = session["detected_plate"]
                    expected_plate = session["expected_plate"]
                    lot_name = session["lot_name"]
                    slot_name = session["slot_name"]

                    # Check for mismatch
                    if detected_plate != expected_plate:
                        print(f"Mismatch detected in Lot: {lot_name}, Slot: {slot_name}")
                        print(f"Detected Plate: {detected_plate}, Expected Plate: {expected_plate}")

                        # Create a message for the alert
                        message = (f"Alert! License plate mismatch detected.\n"
                                   f"Detected: {detected_plate}\n"
                                   f"Expected: {expected_plate}\n"
                                   f"Lot: {lot_name}, Slot: {slot_name}")

                        try:
                            send_alert(PHONE_NUMBER, message)
                            print(f"Alert successfully sent to: {PHONE_NUMBER}")
                        except Exception as e:
                            print(f"Failed to send alert: {e}")

                    # Mark the session as processed
                    try:
                        cursor.execute('''
                            INSERT INTO processed_sessions (id, license_plate, lot_name, slot_name, start_time)
                            SELECT id, license_plate, lot_name, slot_name, start_time
                            FROM parking_sessions
                            WHERE id = %s
                        ''', (row_id,))
                        conn.commit()
                        print(f"Marked session {row_id} as processed.")
                    except Exception as e:
                        print(f"Error marking session {row_id} as processed: {e}")

            conn.close()

        # Wait for 10 seconds before the next check
        time.sleep(10)


if __name__ == "__main__":
    print("Starting session alert processor...")

    # Add a test row (optional, for demonstration purposes)
    test_license_plate = "CG 19 EQ 0001"
    test_lot_name = "Lot_A"
    test_slot_name = "Slot_1"
    test_start_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    insert_parking_session(test_license_plate, test_lot_name, test_slot_name, test_start_time)

    # Start monitoring sessions for mismatched plates
    process_sessions()
