from flask import Flask, render_template, request, redirect, url_for, flash

app = Flask(__name__)
app.secret_key = "your_secret_key"  # for flashing messages

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

# Route to view services
@app.route('/services')
def view_services():
    return render_template('services.html', services=services)

# Route to handle bookings
@app.route('/book/<int:service_id>', methods=['GET', 'POST'])
def book_service(service_id):
    service = next((s for s in services if s['id'] == service_id), None)
    if not service:
        flash("Service not found!", "danger")
        return redirect(url_for('view_services'))
    
    if request.method == 'POST':
        # Extract form data
        name = request.form['name']
        email = request.form['email']
        date = request.form['date']
        
        # Normally, save this to a database
        flash(f"Booking confirmed for {service['name']} on {date}.", "success")
        return redirect(url_for('view_services'))
    
    return render_template('booking.html', service=service)

# Running the app
if __name__ == "__main__":
    app.run(debug=True, port=5072)
