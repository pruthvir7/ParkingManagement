from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3
from datetime import datetime, timedelta

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
        conn.close()
        if user:
            session['license_plate'] = user['license_plate']  # Save license plate in session
            flash("Login successful!", "success")  # Use the 'success' category for login success
            return redirect(url_for('lots'))
        else:
            flash("Invalid email or password.", "danger")  # Use the 'danger' category for login errors
    return render_template('login.html')


@app.route('/lots')
def lots():
    lots = ['Lot A', 'Lot B', 'Lot C', 'Lot D']
    return render_template('lots.html', lots=lots)

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
    reservation = conn.execute('''
        SELECT * FROM reservations WHERE license_plate = ? AND reservation_expiry > DATETIME('now')
        ORDER BY reservation_expiry DESC LIMIT 1
    ''', (license_plate,)).fetchone()
    conn.close()

    total_amount = 50  # Example calculation
    return render_template('payment.html', total_amount=total_amount, reservation=reservation)

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "success")
    return redirect(url_for('dashboard'))

if __name__ == '__main__':
    app.run(debug=True)
