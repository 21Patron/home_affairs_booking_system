from flask import Flask, render_template, request, redirect, url_for, flash, session
import firebase_admin
from firebase_admin import credentials, auth, firestore
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "AIzaSyBoqBz3tha0Nuf_bqXSWssMFHVw8Ce9z4Y")

# Initialize Firebase Admin SDK
cred = credentials.Certificate('c:\\Users\\sm\\Downloads\\newchild-6eddd-firebase-adminsdk-kn3py-4fb4260dd5.json')
firebase_admin.initialize_app(cred)
db = firestore.client()

# Dummy data for services
services = [
    {"id": 1, "name": "ID Application", "description": "Apply for a new ID."},
    {"id": 2, "name": "Passport Application", "description": "Apply for a passport."},
    {"id": 3, "name": "Birth Certificate", "description": "Request a birth certificate."},
    {"id": 4, "name": "Marriage Certificate", "description": "Request a marriage certificate."},
    {"id": 5, "name": "Death Certificate", "description": "Request a death certificate."}
]



@app.route('/')
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form.get('role', 'user')  # Default role to 'user'

        try:
            # Create user in Firebase Auth
            user = auth.create_user(email=email, password=password)
            session['user_email'] = email
            session['role'] = role

            # Save user data to Firestore
            db.collection('users').document(user.uid).set({
                'email': email,
                'role': role,
                'uid': user.uid
            })

            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            flash(f"Registration failed: {e}", "danger")
    
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        try:
            user = auth.get_user_by_email(email)
            session['user_id'] = user.uid
            session['user_email'] = email

            # Retrieve user's role from Firestore
            user_doc = db.collection('users').document(user.uid).get()
            if user_doc.exists:
                role = user_doc.to_dict().get('role', 'user')
                session['role'] = role

                # Redirect to appropriate dashboard or services page
                if role == 'admin':
                    return redirect(url_for('admin_dashboard'))
                elif role == 'staff':
                    return redirect(url_for('staff_dashboard'))
                else:
                    return redirect(url_for('user_dashboard'))  # User role redirects to services page
            else:
                flash("User not found in the database!", "danger")
        except Exception as e:
            flash(f"Login failed: {e}", "danger")
    
    return render_template('login.html')

@app.route('/services')
def view_services():
    if 'user_id' not in session:
        flash('Please log in to view services.', 'warning')
        return redirect(url_for('login'))
    
    return render_template('services.html', services=services)

@app.route('/dashboard/user')
def user_dashboard():
    if session.get('role') != 'user':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    # Example of what might be displayed on user dashboard
    return render_template('user_dashboard.html')

# Helper: Generate time slots (8:00 AM - 3:30 PM, 1-hour interval)
def generate_time_slots():
    start_time = datetime.strptime("08:00", "%H:%M")
    end_time = datetime.strptime("15:30", "%H:%M")
    slots = []

    while start_time <= end_time:
        slot = start_time.strftime("%H:%M")
        slots.append(slot)
        start_time += timedelta(hours=1)

    return slots

@app.route('/book/<int:service_id>', methods=['GET', 'POST'])
def book_service(service_id):
    if 'user_id' not in session:
        flash('Please log in to make a booking.', 'warning')
        return redirect(url_for('login'))

    service = next((s for s in services if s['id'] == service_id), None)
    if not service:
        flash("Service not found!", "danger")
        return redirect(url_for('view_services'))

    user_email = session['user_email']
    user_bookings = db.collection('bookings').where('user_email', '==', user_email).where('status', '==', 'active').stream()
    active_bookings = [b.to_dict() for b in user_bookings]

    if len(active_bookings) >= 3:
        flash("You have reached the maximum of 3 active bookings. Complete or cancel one to make another booking.", "danger")
        return redirect(url_for('view_services'))

    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        slot = f"{date} {time}"

        existing_slot = db.collection('bookings').where('slot', '==', slot).where('status', '==', 'active').get()
        if existing_slot:
            flash(f"The slot {slot} is already booked. Please choose a different time.", "danger")
            return redirect(url_for('book_service', service_id=service_id))

        db.collection('bookings').add({
            'user_email': user_email,
            'service_name': service['name'],
            'slot': slot,
            'status': 'active'
        })

        flash(f"Booking confirmed for {service['name']} on {slot}.", 'success')
        return redirect(url_for('view_services'))

    time_slots = generate_time_slots()  # Generate available time slots
    return render_template('booking.html', service=service, time_slots=time_slots)


@app.route('/bookings')
def view_bookings():
    if 'user_id' not in session:
        flash('Please log in to view bookings.', 'warning')
        return redirect(url_for('login'))

    user_email = session['user_email']
    bookings_ref = db.collection('bookings').where('user_email', '==', user_email).stream()
    bookings = [b.to_dict() for b in bookings_ref]

    return render_template('bookings.html', bookings=bookings)

@app.route('/cancel_booking/<booking_id>')
def cancel_booking(booking_id):
    booking_ref = db.collection('bookings').document(booking_id)
    booking_ref.update({'status': 'cancelled'})

    flash('Booking cancelled successfully.', 'success')
    return redirect(url_for('view_bookings'))

@app.route('/dashboard/staff')
def staff_dashboard():
    if session.get('role') != 'staff':
        flash('Unauthorized access!', 'danger')
        return redirect(url_for('login'))
    
    # Example of what might be displayed on staff dashboard
    return render_template('staff_dashboard.html')

@app.route('/dashboard/admin')
def admin_dashboard():
    # Retrieve users and bookings from Firestore
    users_ref = db.collection('users').stream()
    bookings_ref = db.collection('bookings').stream()

    users = [user.to_dict() for user in users_ref]
    bookings = [booking.to_dict() for booking in bookings_ref]

    return render_template('admin_dashboard.html', users=users, bookings=bookings)

@app.route('/edit_user/<uid>', methods=['GET', 'POST'])
def edit_user(uid):
    user_ref = db.collection('users').document(uid)
    user_doc = user_ref.get()

    if not user_doc.exists:
        flash("User not found", "danger")
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        email = request.form['email']
        role = request.form['role']
        
        # Update user in Firestore
        user_ref.update({
            'email': email,
            'role': role
        })

        flash('User details updated successfully.', 'success')
        return redirect(url_for('admin_dashboard'))

    user = user_doc.to_dict()
    return render_template('edit_user.html', user=user)

@app.route('/delete_user/<uid>')
def delete_user(uid):
    # Delete user from Firestore
    db.collection('users').document(uid).delete()
    flash('User deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/delete_booking/<booking_id>')
def delete_booking(booking_id):
    # Delete booking from Firestore
    booking_ref = db.collection('bookings').document(booking_id)
    booking_ref.delete()
    flash('Booking deleted successfully.', 'success')
    return redirect(url_for('admin_dashboard'))

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True, port=5072)