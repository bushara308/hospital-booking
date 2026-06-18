import pymysql
import pymysql.cursors
from flask import Flask, request, jsonify, render_template, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from twilio.rest import Client
import datetime
from config import Config

app = Flask(__name__)
app.config.from_object(Config)

# Database Connection Helper
def get_db_connection():
    try:
        connection = pymysql.connect(
            host=app.config['MYSQL_HOST'],
            user=app.config['MYSQL_USER'],
            password=app.config['MYSQL_PASSWORD'],
            database=app.config['MYSQL_DB'],
            cursorclass=pymysql.cursors.DictCursor
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

# Optional: Helper to send SMS
def send_sms(to_number, message):
    if not to_number.startswith('+') and len(to_number) == 10:
        to_number = '+91' + to_number
        
    if app.config['TWILIO_ACCOUNT_SID'] and app.config['TWILIO_ACCOUNT_SID'] != 'your_twilio_account_sid':
        try:
            client = Client(app.config['TWILIO_ACCOUNT_SID'], app.config['TWILIO_AUTH_TOKEN'])
            client.messages.create(
                body=message,
                from_=app.config['TWILIO_PHONE_NUMBER'],
                to=to_number
            )
        except Exception as e:
            print(f"SMS Error: {e}")

# ==========================================
# Frontend Routes (HTML Pages)
# ==========================================
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/register')
def register_page():
    return render_template('register.html')

@app.route('/dashboard')
def dashboard_page():
    if 'user_id' not in session or session.get('role') != 'patient':
        return redirect(url_for('login_page'))
    return render_template('dashboard.html')

@app.route('/admin')
def admin_page():
    if 'user_id' not in session or session.get('role') != 'admin':
        return redirect(url_for('login_page'))
    return render_template('admin.html')

# ==========================================
# Backend API Routes
# ==========================================

# --- Authentication APIs ---
@app.route('/api/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    if not all([name, email, password, phone]):
        return jsonify({'error': 'All fields are required'}), 400

    hashed_password = generate_password_hash(password)
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 500
        
    try:
        with conn.cursor() as cursor:
            # Check if email exists
            cursor.execute("SELECT id FROM patients WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({'error': 'Email already registered'}), 400
            
            # Insert patient
            sql = "INSERT INTO patients (name, email, password_hash, phone) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (name, email, hashed_password, phone))
        conn.commit()
        return jsonify({'message': 'Registration successful'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/api/login', methods=['POST'])
def login():
    data = request.json
    email_or_username = data.get('email')  # Can be email (patient) or username (admin)
    password = data.get('password')
    role = data.get('role', 'patient') # Default to patient

    if not email_or_username or not password:
        return jsonify({'error': 'Credentials required'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'error': 'Database unavailable'}), 500

    try:
        with conn.cursor() as cursor:
            if role == 'patient':
                cursor.execute("SELECT id, name, password_hash FROM patients WHERE email = %s", (email_or_username,))
                user = cursor.fetchone()
                if user and check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['name'] = user['name']
                    session['role'] = 'patient'
                    return jsonify({'message': 'Login successful', 'redirect': '/dashboard'}), 200
            elif role == 'admin':
                cursor.execute("SELECT id, username, password_hash FROM admins WHERE username = %s", (email_or_username,))
                user = cursor.fetchone()
                if user and check_password_hash(user['password_hash'], password):
                    session['user_id'] = user['id']
                    session['name'] = user['username']
                    session['role'] = 'admin'
                    return jsonify({'message': 'Admin login successful', 'redirect': '/admin'}), 200
            
            return jsonify({'error': 'Invalid credentials'}), 401
    finally:
        conn.close()

@app.route('/api/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out successfully'}), 200

# --- Patient APIs ---
@app.route('/api/doctors', methods=['GET'])
def get_doctors():
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("SELECT id, name, specialization, available_days FROM doctors")
            doctors = cursor.fetchall()
            return jsonify(doctors), 200
    finally:
        if conn: conn.close()

@app.route('/api/doctors/<int:doctor_id>/slots', methods=['GET'])
def get_doctor_slots(doctor_id):
    date_str = request.args.get('date')
    if not date_str:
        return jsonify({'error': 'Date is required'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = "SELECT appointment_time FROM appointments WHERE doctor_id=%s AND appointment_date=%s AND status != 'Cancelled' AND status != 'Rejected'"
            cursor.execute(sql, (doctor_id, date_str))
            booked = cursor.fetchall()
            booked_times = []
            for b in booked:
                if isinstance(b['appointment_time'], datetime.timedelta):
                    total_seconds = int(b['appointment_time'].total_seconds())
                    hours, remainder = divmod(total_seconds, 3600)
                    minutes, seconds = divmod(remainder, 60)
                    booked_times.append(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
                else:
                    booked_times.append(str(b['appointment_time']))
            
            all_slots = []
            start_time = datetime.datetime.strptime('09:00', '%H:%M')
            end_time = datetime.datetime.strptime('17:00', '%H:%M')
            
            current_time = start_time
            while current_time <= end_time:
                time_str = current_time.strftime('%H:%M:%S')
                all_slots.append(time_str)
                current_time += datetime.timedelta(minutes=30)
                
            available_slots = [s for s in all_slots if s not in booked_times]
            
            return jsonify({
                'booked_slots': booked_times,
                'available_slots': available_slots,
                'all_slots': all_slots
            }), 200
    finally:
        if conn: conn.close()

@app.route('/api/appointments', methods=['GET'])
def get_appointments():
    if 'user_id' not in session or session.get('role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401
        
    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT a.id, a.doctor_id, d.name as doctor_name, d.specialization, 
                       a.appointment_date, a.appointment_time, a.status 
                FROM appointments a
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.patient_id = %s
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """
            cursor.execute(sql, (session['user_id'],))
            appointments = cursor.fetchall()
            
            # Format dates and times for JSON serialization
            for appt in appointments:
                if isinstance(appt['appointment_date'], datetime.date):
                    appt['appointment_date'] = appt['appointment_date'].strftime('%Y-%m-%d')
                if isinstance(appt['appointment_time'], datetime.timedelta):
                    appt['appointment_time'] = str(appt['appointment_time'])

            return jsonify(appointments), 200
    finally:
        if conn: conn.close()

@app.route('/api/appointments', methods=['POST'])
def book_appointment():
    if 'user_id' not in session or session.get('role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    doctor_id = data.get('doctor_id')
    appointment_date = data.get('appointment_date')
    appointment_time = data.get('appointment_time')

    if not all([doctor_id, appointment_date, appointment_time]):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Check for conflict
            conflict_sql = "SELECT id FROM appointments WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s AND status != 'Cancelled'"
            cursor.execute(conflict_sql, (doctor_id, appointment_date, appointment_time))
            if cursor.fetchone():
                return jsonify({'error': 'Time slot already booked for this doctor'}), 400

            # Insert appointment
            sql = "INSERT INTO appointments (patient_id, doctor_id, appointment_date, appointment_time) VALUES (%s, %s, %s, %s)"
            cursor.execute(sql, (session['user_id'], doctor_id, appointment_date, appointment_time))
            
            # Optionally send SMS
            cursor.execute("SELECT name FROM doctors WHERE id = %s", (doctor_id,))
            doctor = cursor.fetchone()
            doctor_name = doctor['name'] if doctor else "the doctor"

            cursor.execute("SELECT phone FROM patients WHERE id = %s", (session['user_id'],))
            patient = cursor.fetchone()
            if patient and patient['phone']:
                send_sms(patient['phone'], f"Your appointment in Medicare Hospital is booked on {appointment_date} at {appointment_time} with {doctor_name}.")
                
        conn.commit()
        return jsonify({'message': 'Appointment booked successfully'}), 201
    finally:
        if conn: conn.close()

@app.route('/api/appointments/<int:appt_id>/cancel', methods=['POST'])
def cancel_appointment(appt_id):
    if 'user_id' not in session or session.get('role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verify ownership
            cursor.execute("SELECT id, appointment_date, appointment_time FROM appointments WHERE id=%s AND patient_id=%s", (appt_id, session['user_id']))
            appt = cursor.fetchone()
            if not appt:
                return jsonify({'error': 'Appointment not found or unauthorized'}), 404
            
            if isinstance(appt['appointment_date'], datetime.date):
                date_part = appt['appointment_date'].strftime('%Y-%m-%d')
            else:
                date_part = str(appt['appointment_date'])
                
            if isinstance(appt['appointment_time'], datetime.timedelta):
                total_seconds = int(appt['appointment_time'].total_seconds())
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                time_part = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            else:
                time_part = str(appt['appointment_time'])
                
            appt_datetime_str = f"{date_part} {time_part}"
            try:
                appt_datetime = datetime.datetime.strptime(appt_datetime_str, '%Y-%m-%d %H:%M:%S')
                if appt_datetime - datetime.datetime.now() < datetime.timedelta(hours=24):
                    return jsonify({'error': 'Appointments can only be cancelled at least 24 hours in advance'}), 400
            except Exception as e:
                pass # Fallback if parsing fails

            cursor.execute("UPDATE appointments SET status='Cancelled' WHERE id=%s", (appt_id,))
        conn.commit()
        return jsonify({'message': 'Appointment cancelled'}), 200
    finally:
        if conn: conn.close()

@app.route('/api/appointments/<int:appt_id>', methods=['PUT'])
def edit_appointment(appt_id):
    if 'user_id' not in session or session.get('role') != 'patient':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    doctor_id = data.get('doctor_id')
    appointment_date = data.get('appointment_date')
    appointment_time = data.get('appointment_time')

    if not all([doctor_id, appointment_date, appointment_time]):
        return jsonify({'error': 'Missing required fields'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            # Verify ownership and status
            cursor.execute("SELECT id, status FROM appointments WHERE id=%s AND patient_id=%s", (appt_id, session['user_id']))
            appt = cursor.fetchone()
            if not appt:
                return jsonify({'error': 'Appointment not found or unauthorized'}), 404
            
            if appt['status'] != 'Pending':
                return jsonify({'error': 'Only pending appointments can be edited'}), 400
            
            # Check for conflict
            conflict_sql = "SELECT id FROM appointments WHERE doctor_id=%s AND appointment_date=%s AND appointment_time=%s AND status != 'Cancelled' AND id != %s"
            cursor.execute(conflict_sql, (doctor_id, appointment_date, appointment_time, appt_id))
            if cursor.fetchone():
                return jsonify({'error': 'Time slot already booked for this doctor'}), 400

            # Update appointment
            sql = "UPDATE appointments SET doctor_id=%s, appointment_date=%s, appointment_time=%s WHERE id=%s"
            cursor.execute(sql, (doctor_id, appointment_date, appointment_time, appt_id))
                
        conn.commit()
        return jsonify({'message': 'Appointment updated successfully'}), 200
    finally:
        if conn: conn.close()

# --- Admin APIs ---
@app.route('/api/admin/appointments', methods=['GET'])
def admin_get_appointments():
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                SELECT a.id, p.name as patient_name, p.phone as patient_phone,
                       d.name as doctor_name, a.appointment_date, a.appointment_time, a.status 
                FROM appointments a
                JOIN patients p ON a.patient_id = p.id
                JOIN doctors d ON a.doctor_id = d.id
                ORDER BY a.appointment_date DESC, a.appointment_time DESC
            """
            cursor.execute(sql)
            appointments = cursor.fetchall()
            
            for appt in appointments:
                if isinstance(appt['appointment_date'], datetime.date):
                    appt['appointment_date'] = appt['appointment_date'].strftime('%Y-%m-%d')
                if isinstance(appt['appointment_time'], datetime.timedelta):
                    appt['appointment_time'] = str(appt['appointment_time'])

            return jsonify(appointments), 200
    finally:
        if conn: conn.close()

@app.route('/api/admin/appointments/<int:appt_id>/status', methods=['POST'])
def admin_update_appointment_status(appt_id):
    if 'user_id' not in session or session.get('role') != 'admin':
        return jsonify({'error': 'Unauthorized'}), 401

    data = request.json
    new_status = data.get('status')
    if new_status not in ['Approved', 'Rejected', 'Pending', 'Cancelled']:
        return jsonify({'error': 'Invalid status'}), 400

    conn = get_db_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("UPDATE appointments SET status=%s WHERE id=%s", (new_status, appt_id))
            
            # Send SMS Notification about status change
            cursor.execute("""
                SELECT p.phone, a.appointment_date, a.appointment_time, d.name as doc_name
                FROM appointments a 
                JOIN patients p ON a.patient_id = p.id 
                JOIN doctors d ON a.doctor_id = d.id
                WHERE a.id = %s
            """, (appt_id,))
            appt_info = cursor.fetchone()
            
            if appt_info and appt_info['phone']:
                date_str = appt_info['appointment_date'].strftime('%Y-%m-%d') if isinstance(appt_info['appointment_date'], datetime.date) else appt_info['appointment_date']
                msg = f"Your appointment with {appt_info['doc_name']} on {date_str} has been {new_status}."
                send_sms(appt_info['phone'], msg)
                
        conn.commit()
        return jsonify({'message': f'Status updated to {new_status}'}), 200
    finally:
        if conn: conn.close()

if __name__ == '__main__':
    # Initialize the database logic here or simply run the app
    # For a real application, make sure MySQL is running and the database is created
    app.run(debug=True, port=5000)
