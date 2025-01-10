from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta
from twilio.rest import Client

app = Flask(__name__)
app.secret_key = "your_secret_key"

DATABASE = 'parking.db'


# Helper function to connect to the database
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
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
        try:
            conn.execute(
                "INSERT INTO users (name, mobile, email, password, license_plate) VALUES (?, ?, ?, ?, ?)",
                (name, mobile, email, password, license_plate),
            )
            conn.commit()
            flash("Registration successful! Please log in.", "success")
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash("Email already registered. Please use a different email.", "danger")
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        user = conn.execute(
            "SELECT * FROM users WHERE email = ? AND password = ?", (email, password)
        ).fetchone()

        if user:
            license_plate = user['license_plate']
            session['license_plate'] = license_plate

            # Check for unpaid parking session
            unpaid_session = conn.execute('''
                SELECT * 
                FROM parking_sessions
                WHERE license_plate = ? AND paid = 0 AND end_time IS NOT NULL
                ORDER BY end_time DESC
                LIMIT 1
            ''', (license_plate,)).fetchone()

            conn.close()

            if unpaid_session:
                print("Redirecting to payment for unpaid session.")  # Debugging
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

    # Check for unpaid parking sessions
    unpaid_session = conn.execute('''
        SELECT * 
        FROM parking_sessions 
        WHERE license_plate = ? AND paid = 0 AND end_time IS NOT NULL
    ''', (license_plate,)).fetchone()

    if unpaid_session:
        conn.close()
        flash("You have unpaid parking charges. Please proceed to payment.", "warning")
        return redirect(url_for('payment'))

    conn.close()
    lots = ['Lot A', 'Lot B', 'Lot C', 'Lot D']
    return render_template('lots.html', lots=lots)

def send_alert(actual_license_plate, reserved_license_plate):
    # Twilio credentials
    account_sid = "AC3db0b56ac1e8939e60ace980f9f16156"  # Replace with your Twilio Account SID
    auth_token = "c6cae599e693f6529f23ad3a969eedf5"    # Replace with your Twilio Auth Token
    client = Client(account_sid, auth_token)

    # Your mobile number (person in charge of parking lot)
    manager_phone_number = "+919741078794"  # Replace with your verified Twilio number

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
        from_="+17174008507",  # Replace with your Twilio phone number
        to=manager_phone_number  # Send alert to the parking manager
    )

    print(f"Alert sent to {manager_phone_number}: {message.sid}")



@app.route('/validate_entry', methods=['POST'])
def validate_entry():
    actual_license_plate = request.form['license_plate']  # License plate captured on entry
    lot_name = request.form['lot_name']
    slot_name = request.form['slot_name']

    conn = get_db_connection()
    reservation = conn.execute('''
        SELECT * FROM reservations
        WHERE lot_name = ? AND slot_name = ? AND reservation_expiry > DATETIME('now')
    ''', (lot_name, slot_name)).fetchone()

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

    # Get current reservations for the selected lot
    reservations = conn.execute('''
        SELECT slot_name, reservation_expiry FROM reservations
        WHERE lot_name = ? AND reservation_expiry > DATETIME('now')
    ''', (lot_name,)).fetchall()

    # Build slot status dictionary
    slots = {f'Slot {i}': None for i in range(1, 9)}  # Default all slots as available
    for reservation in reservations:
        try:
            # Convert reservation_expiry to a datetime object, including fractional seconds
            expiry_datetime = datetime.strptime(reservation['reservation_expiry'], '%Y-%m-%d %H:%M:%S.%f')
        except ValueError:
            # Fallback if no fractional seconds are present
            expiry_datetime = datetime.strptime(reservation['reservation_expiry'], '%Y-%m-%d %H:%M:%S')
        slots[reservation['slot_name']] = expiry_datetime

    conn.close()
    return render_template('slots.html', lot_name=lot_name, slots=slots)


@app.route('/reserve', methods=['POST'])
def reserve():
    lot_name = request.form['lot_name']
    slot_name = request.form['slot_name']
    license_plate = session.get('license_plate')  # Get license plate from session
    if not license_plate:
        flash("You must be logged in to reserve a slot.", "danger")
        return redirect(url_for('login'))
    
    reservation_expiry = datetime.now() + timedelta(minutes=10)

    conn = get_db_connection()
    try:
        # Insert the reservation into the database
        conn.execute('''
            INSERT INTO reservations (license_plate, lot_name, slot_name, reservation_expiry)
            VALUES (?, ?, ?, ?)
        ''', (license_plate, lot_name, slot_name, reservation_expiry))
        conn.commit()

        # Pass the booking details to the thank you page
        session['booking_details'] = {
            'license_plate': license_plate,
            'lot_name': lot_name,
            'slot_name': slot_name,
            'reservation_expiry': reservation_expiry.strftime('%Y-%m-%d %H:%M:%S')
        }
        flash(f"Slot {slot_name} in {lot_name} reserved successfully!", "success")
        return redirect(url_for('thankyou'))
    except sqlite3.IntegrityError:
        flash("Failed to reserve slot. Please try again.", "danger")
    finally:
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
    # Fetch the latest unpaid, completed parking session
    session_data = conn.execute('''
        SELECT * 
        FROM parking_sessions
        WHERE license_plate = ? AND paid = 0 AND end_time IS NOT NULL
        ORDER BY end_time DESC
        LIMIT 1
    ''', (license_plate,)).fetchone()

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
    start_time = datetime.strptime(session_data['start_time'], '%Y-%m-%d %H:%M:%S')
    end_time = datetime.strptime(session_data['end_time'], '%Y-%m-%d %H:%M:%S')
    total_time_spent = end_time - start_time

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
    
    print(f"License Plate: {license_plate}")  # Debugging

    if not license_plate:
        flash("You must be logged in to confirm payment.", "danger")
        return redirect(url_for('login'))

    conn = get_db_connection()
    row_to_update = conn.execute('''
        SELECT id
        FROM parking_sessions
        WHERE license_plate = ? AND end_time IS NOT NULL AND paid = 0
        ORDER BY end_time DESC
        LIMIT 1
    ''', (license_plate,)).fetchone()

    if row_to_update:
        conn.execute('''
            UPDATE parking_sessions
            SET paid = 1
            WHERE id = ?
        ''', (row_to_update['id'],))
        conn.commit()
        flash("Payment confirmed successfully!", "success")
    else:
        flash("No pending payments to confirm.", "info")

    conn.close()

    print("Redirecting to 'lots' page...")  # Debugging

    return redirect(url_for('lots'))


@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)