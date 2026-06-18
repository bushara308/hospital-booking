# Hospital Appointment Booking System 🏥

A complete, modern, and secure Hospital Appointment Booking System built with HTML, CSS, JavaScript (Frontend), Python Flask (Backend), and MySQL (Database). Perfect for a college mini-project! 🎓

---

## 🚀 Step-by-Step Setup Instructions

Follow these instructions carefully to get the project running on your local machine.

### 1. Database Setup (MySQL)
1. Install [MySQL Server](https://dev.mysql.com/downloads/mysql/) and [MySQL Workbench](https://dev.mysql.com/downloads/workbench/) (or XAMPP/WAMP).
2. Open MySQL Workbench and log in with your credentials.
3. Open the `database.sql` file included in this folder.
4. Execute the entire SQL script. This will:
   - Create the `hospital_db` database.
   - Create `patients`, `doctors`, `admins`, and `appointments` tables.
   - Insert sample data (including an admin account and sample doctors).

### 2. Backend Setup (Flask)
1. Ensure you have **Python 3.8+** installed.
2. Open your terminal/command prompt and navigate to the `hospital_booking` directory:
   ```bash
   cd path/to/hospital_booking
   ```
3. (Optional but recommended) Create a virtual environment:
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```
4. Install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```
5. Update your MySQL Credentials:
   Open `config.py` and update `MYSQL_USER` and `MYSQL_PASSWORD` if your local MySQL setup uses something other than `root` / `""`.

### 3. Run the Application
Start the Flask development server:
```bash
python app.py
```
Open your web browser and go to: `http://127.0.0.1:5000`

### 4. How to Test
- **Patient Flow**: Click "Register" to create a new account, then login. Go to the dashboard, select a doctor, and book an appointment.
- **Admin Flow**: Go to the login page, check the "I am an Admin" box. Use the sample credentials: Username: `admin`, Password: `admin123`. Approve or reject pending appointments.

---

## 🔗 Integration Guide (How Frontend connects to Backend)

The system uses a modern **REST API architecture** to connect the HTML frontend with the Python backend.

### 1. API Calls using `fetch()`
Instead of traditional form submissions that reload the page, we use JavaScript's `fetch()` API in `static/js/main.js`.
```javascript
// Example from main.js
const response = await fetch('/api/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ email, password, role })
});
```

### 2. JSON Handling
Data is sent and received in **JSON** (JavaScript Object Notation) format.
- **Frontend to Backend**: We convert JS objects to JSON strings using `JSON.stringify()`.
- **Backend to Frontend**: Flask's `jsonify()` converts Python dictionaries to JSON responses, which `response.json()` parses back into JS objects.

### 3. Error Handling
We check `response.ok` in JS. If the server returns a 400 or 500 error, we catch it and display a user-friendly alert box using the `showAlert()` function in `main.js`.

---

## 🔒 Security Concepts 

This project implements several industry-standard security practices to impress your evaluators:

### 1. SQL Injection Prevention
We use **Parameterized Queries** via PyMySQL. Notice in `app.py`, we never use string formatting (`f"SELECT * FROM users WHERE email='{email}'"`). Instead, we use `%s` placeholders:
```python
cursor.execute("SELECT id FROM patients WHERE email = %s", (email,))
```
This ensures user input is treated as data, not executable SQL code, preventing hackers from manipulating the database.

### 2. Authentication Security (Password Hashing)
We **NEVER store plain-text passwords**. We use Flask's `werkzeug.security` module to generate secure hashes (`scrypt` algorithm) with salt.
```python
hashed_password = generate_password_hash(password)
```
When a user logs in, we compare the hash using `check_password_hash()`. Even if the database is stolen, passwords remain safe.

### 3. Session Management
We use Flask's secure client-side sessions to remember logged-in users. The session cookie is cryptographically signed using the `SECRET_KEY` defined in `config.py`.

### 4. Data Validation
- **Frontend Validation**: HTML5 attributes like `required`, `minlength`, and input types (`email`, `tel`) prevent invalid data from being submitted.
- **Backend Validation**: Flask checks if all required fields are present before attempting database insertion, preventing NULL constraint errors.

### 5. HTTPS Concept
*(Theoretical for College Project)*: In production, this app would run over HTTPS (SSL/TLS). HTTPS encrypts the data travelling between the browser and the server, ensuring that passwords and medical data cannot be intercepted (Man-in-the-Middle attack) on public Wi-Fi networks.

---

## ⭐ Advanced Feature: SMS Notifications (Twilio)

The backend (`app.py`) includes a `send_sms()` function powered by the **Twilio API**. 
When a patient books an appointment, or an admin approves/rejects it, the system attempts to send an SMS to the patient's phone number.

**To activate this:**
1. Create a free account at [Twilio.com](https://www.twilio.com/).
2. Get your `Account SID`, `Auth Token`, and a Twilio phone number.
3. Add these credentials to your environment variables or directly update `config.py`.
4. Ensure the patient registers with a valid phone number (including country code, e.g., `+1234567890`).
