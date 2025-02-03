from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
from twilio.rest import Client
import pymysql
from dotenv import load_dotenv
import os

load_dotenv()

app = Flask(__name__)
app.secret_key = "your_secret_key"

RDS_HOST = os.getenv('RDS_HOST')
RDS_USER = os.getenv('RDS_USER')
RDS_PASSWORD = os.getenv('RDS_PASSWORD')
RDS_DB_NAME = os.getenv('RDS_DB_NAME')

# Helper function to connect to the AWS RDS MySQL database
def get_db_connection():
    conn = pymysql.connect(
        host=RDS_HOST,
        user=RDS_USER,
        password=RDS_PASSWORD,
        db=RDS_DB_NAME,
        cursorclass=pymysql.cursors.DictCursor  # This allows results to be accessed like dictionaries
    )
    return conn


@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        mobile = request.form['mobile']
        email = request.form['email']
        password = request.form['password']
        license_plate = request.form['license_plate']
        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO users (name, mobile, email, password, license_plate) VALUES (%s, %s, %s, %s, %s)",
                (name, mobile, email, password, license_plate),
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except pymysql.MySQLError:
            flash("Email already registered. Please use a different email.", "danger")
        finally:
            cursor.close()
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        cursor = conn.cursor()

        # Check for superadmin credentials
        if email == 'superadmin' and password == 'superadmin':
            session['role'] = 'superadmin'  # Store superadmin in session
            flash("Login successful! Welcome Super Admin.", "success")
            return redirect(url_for('superadmin_dashboard'))

        # Check for regular user credentials
        cursor.execute(
            "SELECT * FROM users WHERE email = %s AND password = %s", (email, password)
        )
        user = cursor.fetchone()

        if user:
            license_plate = user['license_plate']
            session['license_plate'] = license_plate

            # Check for unpaid parking session
            cursor.execute('''
                SELECT * 
                FROM parking_sessions
                WHERE license_plate = %s AND paid = 0 AND end_time IS NOT NULL
                ORDER BY end_time DESC
                LIMIT 1
            ''', (license_plate,))
            unpaid_session = cursor.fetchone()

            if unpaid_session:
                flash("You have a pending payment for a completed parking session.", "danger")
                return redirect(url_for('payment'))

            flash("Login successful!", "success")
            return redirect(url_for('lots'))
        else:
            flash("Invalid email or password.", "danger")
    
    return render_template('login.html')




@app.route('/lots')
def lots():
    license_plate = session.get('license_plate')
    if not license_plate:
        flash("You must be logged in to access this page.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check for unpaid parking sessions
    cursor.execute('''
        SELECT * 
        FROM parking_sessions 
        WHERE license_plate = %s AND paid = 0 AND end_time IS NOT NULL
    ''', (license_plate,))
    unpaid_session = cursor.fetchone()

    if unpaid_session:
        conn.close()
        flash("You have unpaid parking charges. Please proceed to payment.", "warning")
        return redirect(url_for('payment'))

    conn.close()
    lots = ['Lot A', 'Lot B', 'Lot C', 'Lot D']
    return render_template('lots.html', lots=lots)

# The send_alert function and other routes remain unchanged. Just update cursor-based execution inside the functions.

def send_alert(actual_license_plate, reserved_license_plate):
    # Twilio credentials
    account_sid = os.getenv("ACCOUNT_SID")
    auth_token = os.getenv("AUTH_TOKEN")    # Replace with your Twilio Auth Token
    client = Client(account_sid, auth_token)

    # Your mobile number (person in charge of parking lot)
    manager_phone_number = os.getenv("MANAGER_PHONE_NUMBER")  # Replace with your verified Twilio number

    # SMS content
    message_body = (
        f"Alert! License plate mismatch detected.\n"
        f"Actual: {actual_license_plate}\n"
        f"Reserved: {reserved_license_plate}.\n"
        f"Please verify the issue immediately."
    )

    # Send SMS
    message = client.messages.create(
        body=message_body,
        from_=os.getenv("TWILIO_NO"),  
        to=manager_phone_number  # Send alert to the parking manager
    )

    print(f"Alert sent to {manager_phone_number}: {message.sid}")

@app.route('/validate_entry', methods=['POST'])
def validate_entry():
    actual_license_plate = request.form['license_plate']  # License plate captured on entry
    lot_name = request.form['lot_name']
    slot_name = request.form['slot_name']

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
    SELECT * FROM reservations
    WHERE lot_name = %s AND slot_name = %s AND reservation_expiry > NOW()
''', (lot_name, slot_name)).fetchone()
    reservation = cursor.fetchone()

    conn.close()

    if reservation:
        reserved_license_plate = reservation['license_plate']
        if actual_license_plate != reserved_license_plate:
            print(f"Mismatch detected: {actual_license_plate} != {reserved_license_plate}.")
            # Send alert to parking manager
            send_alert(actual_license_plate, reserved_license_plate)
            flash("License plate mismatch detected! Alert sent to the parking manager.", "danger")
        else:
            flash("License plate matches the reservation. Entry validated.", "success")
    else:
        flash("No reservation found for this slot.", "warning")

    return redirect(url_for('lots'))

@app.route('/slots/<lot_name>', methods=['GET'])
def slots(lot_name):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get current reservations for the selected lot
    cursor.execute('''
        SELECT slot_name, reservation_expiry FROM reservations
        WHERE lot_name = %s AND reservation_expiry > NOW()
    ''', (lot_name,))
    reservations = cursor.fetchall()

    # Build slot status dictionary
    slots = {f'Slot {i}': None for i in range(1, 9)}  # Default all slots as available
    for reservation in reservations:
        try:
            # Check if reservation_expiry is a string
            if isinstance(reservation['reservation_expiry'], str):
                # Convert string to datetime object, including fractional seconds
                expiry_datetime = datetime.strptime(reservation['reservation_expiry'], '%Y-%m-%d %H:%M:%S.%f')
            else:
                # If it's already a datetime, use it directly
                expiry_datetime = reservation['reservation_expiry']
        except ValueError:
            # Fallback if no fractional seconds are present
            if isinstance(reservation['reservation_expiry'], str):
                expiry_datetime = datetime.strptime(reservation['reservation_expiry'], '%Y-%m-%d %H:%M:%S')
            else:
                expiry_datetime = reservation['reservation_expiry']
        
        # Update the slots dictionary with the expiry time
        slots[reservation['slot_name']] = expiry_datetime

    conn.close()
    return render_template('slots.html', lot_name=lot_name, slots=slots)

@app.route('/reserve', methods=['POST'])
def reserve():
    license_plate = session.get('license_plate')  # Get license plate from session
    if not license_plate:
        flash("You must be logged in to reserve a slot.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if the user has any unpaid parking sessions
    cursor.execute('''
        SELECT * 
        FROM parking_sessions 
        WHERE license_plate = %s AND paid = 0 AND end_time IS NOT NULL
    ''', (license_plate,))
    unpaid_session = cursor.fetchone()

    if unpaid_session:
        conn.close()
        flash("You have unpaid parking charges. Please proceed to payment.", "warning")
        return redirect(url_for('payment'))

    # Proceed with reservation if no unpaid session
    lot_name = request.form['lot_name']
    slot_name = request.form['slot_name']
    reservation_expiry = datetime.now() + timedelta(minutes=10)

    try:
        cursor.execute('''
            INSERT INTO reservations (license_plate, lot_name, slot_name, reservation_expiry)
            VALUES (%s, %s, %s, %s)
        ''', (license_plate, lot_name, slot_name, reservation_expiry))
        conn.commit()

        session['booking_details'] = {
            'license_plate': license_plate,
            'lot_name': lot_name,
            'slot_name': slot_name,
            'reservation_expiry': reservation_expiry.strftime('%Y-%m-%d %H:%M:%S')
        }
        flash(f"Slot {slot_name} in {lot_name} reserved successfully!", "success")
        return redirect(url_for('thankyou'))
    except pymysql.MySQLError:
        flash("Failed to reserve slot. Please try again.", "danger")
    finally:
        cursor.close()
        conn.close()


@app.route('/thankyou')
def thankyou():
    booking_details = session.get('booking_details')
    if not booking_details:
        flash("No booking details found. Please make a reservation first.", "danger")
        return redirect(url_for('lots'))

    return render_template('thankyou.html', booking_details=booking_details)

@app.route('/payment')
def payment():
    license_plate = session.get('license_plate')
    if not license_plate:
        flash("You must be logged in to view payment details.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()
    # Fetch the latest unpaid, completed parking session
    cursor.execute('''
        SELECT * 
        FROM parking_sessions
        WHERE license_plate = %s AND paid = 0 AND end_time IS NOT NULL
        ORDER BY end_time DESC
        LIMIT 1
    ''', (license_plate,))
    session_data = cursor.fetchone()

    if not session_data:
        conn.close()
        # Only redirect to `lots` if no pending payments exist
        return redirect(url_for('lots'))

    # Calculate payment based on duration
    duration_minutes = session_data['duration'] // 60  # Convert seconds to minutes
    if duration_minutes <= 10:
        total_amount = 20  # Flat rate for first 10 minutes
    else:
        additional_minutes = duration_minutes - 10
        total_amount = 20 + (additional_minutes * 2)  # ₹20 for first 10 mins + ₹2 per extra minute

    # Calculate total time spent
    start_time = session_data['start_time']
    end_time = session_data['end_time']
    total_time_spent = end_time - start_time  # This works if start_time and end_time are datetime objects

    conn.close()

    return render_template(
        'payment.html',
        total_amount=total_amount,
        session_data=session_data,
        start_time=start_time.strftime('%Y-%m-%d %H:%M:%S'),
        end_time=end_time.strftime('%Y-%m-%d %H:%M:%S'),
        total_time_spent=str(total_time_spent)
    )

@app.route('/confirm_payment', methods=['POST'])
def confirm_payment():
    license_plate = session.get('license_plate')
    
    print(f"Session License Plate: {license_plate}")  # Debugging

    if not license_plate:
        flash("You must be logged in to confirm payment.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    
    try:
        # Fetch the row that needs to be updated
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id
            FROM parking_sessions
            WHERE license_plate = %s AND end_time IS NOT NULL AND paid = 0
            ORDER BY end_time DESC
            LIMIT 1
        ''', (license_plate,))
        row_to_update = cursor.fetchone()

        print(f"Row to update: {row_to_update}")  # Debugging

        if row_to_update:
            # Update the 'paid' status to 1
            cursor.execute('''
                UPDATE parking_sessions
                SET paid = 1
                WHERE id = %s
            ''', (row_to_update['id'],))
            conn.commit()
            flash("Payment confirmed successfully!", "success")
        else:
            flash("No pending payments to confirm.", "info")

    except Exception as e:
        flash(f"Error: {str(e)}", "danger")
    
    finally:
        conn.close()  # Always close the connection

    print("Redirecting to 'lots' page...")  # Debugging

    return redirect(url_for('lots'))


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('dashboard'))

@app.route('/superadmin')
def superadmin_dashboard():
    # Ensure the user is logged in and is a superadmin
    if session.get('role') != 'superadmin':
        flash("You do not have permission to access this page.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()

    cursor.execute("SELECT * FROM reservations")
    reservations = cursor.fetchall()

    cursor.execute("SELECT * FROM parking_sessions")
    parking_sessions = cursor.fetchall()

    conn.close()

    return render_template('super_admin.html', users=users, reservations=reservations, parking_sessions=parking_sessions)


# Add User
@app.route('/add_user', methods=['POST'])
def add_user():
    name = request.form['name']
    email = request.form['email']
    mobile = request.form['mobile']
    license_plate = request.form['license_plate']
    password = (request.form['password'])

    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO users (name, email, mobile, license_plate, password, role) 
            VALUES (%s, %s, %s, %s, %s, 'user')
        """, (name, email, mobile, license_plate, password))
        conn.commit()
        flash("User added successfully!", "success")
    except pymysql.MySQLError:
        flash("Error adding user. Please try again.", "danger")
        conn.rollback()

    conn.close()
    return redirect(url_for('superadmin_dashboard'))


# Delete User
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        conn.commit()
        flash("User deleted successfully.", "success")
    except pymysql.MySQLError:
        flash("Error deleting user. Please try again.", "danger")
        conn.rollback()

    conn.close()
    return redirect(url_for('superadmin_dashboard'))


# Delete Reservation
@app.route('/delete_reservation/<int:reservation_id>', methods=['POST'])
def delete_reservation(reservation_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("DELETE FROM reservations WHERE id = %s", (reservation_id,))
        conn.commit()
        flash("Reservation deleted successfully.", "success")
    except pymysql.MySQLError:
        flash("Error deleting reservation. Please try again.", "danger")
        conn.rollback()

    conn.close()
    return redirect(url_for('superadmin_dashboard'))


# Mark Parking Session as Paid
@app.route('/mark_paid/<int:session_id>', methods=['POST'])
def mark_paid(session_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE parking_sessions SET paid = 1 WHERE id = %s", (session_id,))
        conn.commit()
        flash("Parking session marked as paid.", "success")
    except pymysql.MySQLError:
        flash("Error marking session as paid. Please try again.", "danger")
        conn.rollback()

    conn.close()
    return redirect(url_for('superadmin_dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
