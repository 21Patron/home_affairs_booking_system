from flask import Flask, render_template, request, redirect, url_for, flash, session
import firebase_admin
from firebase_admin import credentials, auth
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "AIzaSyBoqBz3tha0Nuf_bqXSWssMFHVw8Ce9z4Y")  # Better security practice

# Initialize Firebase Admin SDK
cred = credentials.Certificate('C:\\Users\\sm\\Downloads\\newchild-6eddd-firebase-adminsdk-kn3py-b28c7d008d.json')  # Path to your Firebase service account file
firebase_admin.initialize_app(cred)

# Dummy data for services
services = [
    {"id": 1, "name": "ID Application", "description": "Apply for a new ID."},
    {"id": 2, "name": "Passport Application", "description": "Apply for a passport."},
    {"id": 3, "name": "Birth Certificate", "description": "Request a birth certificate."},
    {"id": 4, "name": "Marriage Certificate", "description": "Request a marriage certificate."},
    {"id": 5, "name": "Death Certificate", "description": "Request a death certificate."}
]

# Route for home page
@app.route('/')
def index():
    return render_template('index.html')

# Route for user registration
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')  # Default role to 'user'

        try:
            # Register the user in Firebase Authentication
            user = auth.create_user(email=email, password=password)

            # Store user details in session (or in a database)
            session['user_email'] = email
            session['role'] = role

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration failed: {e}", "danger")
    
    return render_template('register.html')

# Route for user login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']  # Firebase Admin SDK doesn't verify passwords

        try:
            # Fetch the user by email
            user = auth.get_user_by_email(email)
            
            # Assume user authentication succeeded (you may need Firebase JS SDK for actual login verification)
            session['user_id'] = user.uid
            session['user_email'] = email

            # Redirect to services view or based on role
            role = session.get('role', 'user')  # Get from session, or default to 'user'
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            elif role == 'staff':
                return redirect(url_for('staff_dashboard'))
            else:
                return redirect(url_for('view_services'))
        except Exception as e:
            flash(f"Login failed: {e}", "danger")
    
    return render_template('login.html')

# Route to view services
@app.route('/services')
def view_services():
    if 'user_id' not in session:
        flash('Please log in to view services.', 'warning')
        return redirect(url_for('login'))
    
    return render_template('services.html', services=services)

# Route to handle bookings
@app.route('/book/<int:service_id>', methods=['GET', 'POST'])
def book_service(service_id):
    if 'user_id' not in session:
        flash('Please log in to make a booking.', 'warning')
        return redirect(url_for('login'))

    service = next((s for s in services if s['id'] == service_id), None)
    if not service:
        flash("Service not found!", "danger")
        return redirect(url_for('view_services'))

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        date = request.form['date']

        # Normally, you would save the booking details to a database here
        flash(f"Booking confirmed for {service['name']} on {date}.", 'success')
        return redirect(url_for('view_services'))

    return render_template('booking.html', service=service)

# Dashboards for different user roles
@app.route('/dashboard/admin')
def admin_dashboard():
    return render_template('admin_dashboard.html')

@app.route('/dashboard/staff')
def staff_dashboard():
    return render_template('staff_dashboard.html')

# Route for user logout
@app.route('/logout')
def logout():
    session.clear()  # Clear all session data
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

# Running the app
if __name__ == "__main__":
    app.run(debug=True, port=5072)
