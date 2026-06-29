from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app import db, mail
from app.models import User, Student, Parent, LocationHistory, CheckIn, SOSAlert, EmergencyContact
from flask_mail import Message
from datetime import datetime
import math
import re
#blueprint and geofencing
main = Blueprint('main', __name__)

CAMPUS_CENTER_LAT = 12.8231
CAMPUS_CENTER_LON = 80.0444
CAMPUS_RADIUS_KM = 0.5

def is_within_campus(lat, lon):
    R = 6371
    lat1 = math.radians(CAMPUS_CENTER_LAT)
    lat2 = math.radians(lat)
    dlat = math.radians(lat - CAMPUS_CENTER_LAT)
    dlon = math.radians(lon - CAMPUS_CENTER_LON)
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    distance = R * c
    return distance <= CAMPUS_RADIUS_KM


CAMPUS_ZONES = {
    # ═══ GATES & LANDMARKS ═══
    'Arch Gate (Main Entrance)': {
        'lat': 12.8232113, 'lon': 80.03901, 'radius': 0.05},
    'Clock Tower': {
        'lat': 12.8229487, 'lon': 80.0422531, 'radius': 0.05},

    # ═══ ACADEMIC BLOCKS ═══
    'Tech Park (TP-1)': {
        'lat': 12.8248119, 'lon': 80.042491, 'radius': 0.10},
    'Architecture / MBA Block': {
        'lat': 12.824086, 'lon': 80.0414049, 'radius': 0.08},
    'SRM Law Building': {
        'lat': 12.8258886, 'lon': 80.0433639, 'radius': 0.08},
    'SRM Global Hospital': {
        'lat': 12.8229964, 'lon': 80.0454181, 'radius': 0.08},

    # ═══ FOOD & COMMON AREAS ═══
    'Java Food Court': {
        'lat': 12.823354, 'lon': 80.0444979, 'radius': 0.05},
    'Vendhar Square': {
        'lat': 12.8237356, 'lon': 80.0452172, 'radius': 0.05},
    'TPG Auditorium': {
        'lat': 12.8239068, 'lon': 80.0446621, 'radius': 0.06},

    # ═══ GIRLS HOSTELS ═══
    'Kopperundevi Hostel (M Block)': {
        'lat': 12.8207149, 'lon': 80.0433827, 'radius': 0.07},
    'Meenakshi Hostel': {
        'lat': 12.8221546, 'lon': 80.041164, 'radius': 0.07},
    'ESQ Hostel (A & B)': {
        'lat': 12.8221546, 'lon': 80.041164, 'radius': 0.07},
    'Shenbagam Hostel': {
        'lat': 12.8221546, 'lon': 80.041164, 'radius': 0.07},
    'Kalpana Chawla Hostel': {
        'lat': 12.8221546, 'lon': 80.041164, 'radius': 0.07},
    'Malligai Hostel': {
        'lat': 12.8221546, 'lon': 80.041164, 'radius': 0.07},
    'Thamarai Hostel': {
        'lat': 12.8221546, 'lon': 80.041164, 'radius': 0.07},
    'Mullai Hostel': {
        'lat': 12.8221546, 'lon': 80.041164, 'radius': 0.07},
    'Sannasi C Hostel': {
        'lat': 12.8221546, 'lon': 80.041164, 'radius': 0.07},
    'Begam Hostel': {
        'lat': 12.8207149, 'lon': 80.0433827, 'radius': 0.07},
    'N Block Hostel': {
        'lat': 12.8207149, 'lon': 80.0433827, 'radius': 0.07},

    # ═══ BOYS HOSTELS ═══
    'Paari Hostel': {
        'lat': 12.8229455, 'lon': 80.0440749, 'radius': 0.07},
    'Kaari Hostel': {
        'lat': 12.8229455, 'lon': 80.0440749, 'radius': 0.07},
    'Oori Hostel': {
        'lat': 12.8229455, 'lon': 80.0440749, 'radius': 0.07},
    'Adhiyaman Hostel': {
        'lat': 12.8207149, 'lon': 80.0433827, 'radius': 0.07},
    'Agasthiyar Hostel': {
        'lat': 12.8207605, 'lon': 80.0410064, 'radius': 0.07},
    'Nelson Mandela Hostel': {
        'lat': 12.8207149, 'lon': 80.0433827, 'radius': 0.07},
    'Sannasi A Hostel': {
        'lat': 12.8207149, 'lon': 80.0433827, 'radius': 0.07},
    'Manoranjitham Hostel': {
        'lat': 12.8207149, 'lon': 80.0433827, 'radius': 0.07},
}


def get_current_zone(lat, lon):
    for zone_name, zone in CAMPUS_ZONES.items():
        d = math.sqrt(
            (lat - zone['lat'])**2 + 
            (lon - zone['lon'])**2
        ) * 111
        if d <= zone['radius']:
            return zone_name
    return None
#basic routes
@main.route('/')
def home():
    return render_template('home.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        password = request.form.get('password')
        role = request.form.get('role')
        phone = request.form.get('phone')

        # Password validation starts here
        if not password or len(password) < 8:
            flash('Password must be at least 8 characters.', 'danger')
            return redirect(url_for('main.register'))

        if not re.search(r'[A-Z]', password):
            flash('Password must contain at least one uppercase letter.', 'danger')
            return redirect(url_for('main.register'))

        if not re.search(r'[0-9]', password):
            flash('Password must contain at least one number.', 'danger')
            return redirect(url_for('main.register'))
        
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Email already registered. Please login.', 'danger')
            return redirect(url_for('main.register'))

        hashed_password = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_password,
                   role=role, phone=phone)
        db.session.add(user)
        db.session.flush()

        if role == 'student':
            roll_number = request.form.get('roll_number')
            department = request.form.get('department')
            year = request.form.get('year')
            student = Student(user_id=user.id, roll_number=roll_number,
                            department=department, year=year)
            db.session.add(student)

        elif role == 'parent':
            student_roll = request.form.get('student_roll')
            student = Student.query.filter_by(roll_number=student_roll).first()
            parent = Parent(user_id=user.id, phone=phone)
            db.session.add(parent)
            db.session.flush()
            if student:
                student.parent_id = parent.id

        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html')
#login and logout
@main.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Login successful!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            flash('Invalid email or password.', 'danger')

    return render_template('login.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.home'))
#Dashboard
@main.route('/dashboard')
@login_required
def dashboard():
    if current_user.role == 'student':
        student = Student.query.filter_by(user_id=current_user.id).first()
        checkins = CheckIn.query.filter_by(student_id=student.id)\
                  .order_by(CheckIn.timestamp.desc()).limit(5).all()
        sos_alerts = SOSAlert.query.filter_by(student_id=student.id,
                    is_resolved=False).all()
        return render_template('student_dashboard.html', student=student,
                             checkins=checkins, sos_alerts=sos_alerts)

    elif current_user.role == 'parent':
        parent = Parent.query.filter_by(user_id=current_user.id).first()
        children = Student.query.filter_by(parent_id=parent.id).all()
        return render_template('parent_dashboard.html', parent=parent,
                             children=children)

    elif current_user.role == 'admin':
        all_students = Student.query.all()
        on_campus = Student.query.filter_by(is_on_campus=True).all()
        sos_alerts = SOSAlert.query.filter_by(is_resolved=False).all()
        total_checkins = CheckIn.query.count()
        return render_template('admin_dashboard.html',
                             all_students=all_students,
                             on_campus=on_campus,
                             sos_alerts=sos_alerts,
                             total_checkins=total_checkins)
    
@main.route('/update_location', methods=['POST'])
@login_required
def update_location():
    if current_user.role != 'student':
        return jsonify({'error': 'Not a student'}), 403

    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')

    if not lat or not lon:
        return jsonify({'error': 'No location data'}), 400

    student = Student.query.filter_by(user_id=current_user.id).first()
    on_campus = is_within_campus(lat, lon)
    previously_on_campus = student.is_on_campus

    student.current_latitude = lat
    student.current_longitude = lon
    student.is_on_campus = on_campus
    student.last_seen = datetime.utcnow()

    history = LocationHistory(student_id=student.id, latitude=lat,
                             longitude=lon, is_on_campus=on_campus)
    db.session.add(history)
    db.session.commit()

    if on_campus != previously_on_campus:
        send_campus_alert(student, on_campus)

    return jsonify({
        'status': 'updated',
        'on_campus': on_campus,
        'message': 'On campus' if on_campus else 'Off campus'
    })

@main.route('/sos', methods=['POST'])
@login_required
def sos():
    if current_user.role != 'student':
        return jsonify({'error': 'Not a student'}), 403

    data = request.get_json()
    lat = data.get('latitude')
    lon = data.get('longitude')

    student = Student.query.filter_by(user_id=current_user.id).first()
    alert = SOSAlert(student_id=student.id, latitude=lat, longitude=lon)
    db.session.add(alert)
    db.session.commit()

    send_sos_alert(student, lat, lon)

    return jsonify({'status': 'sos_sent', 'message': 'SOS alert sent!'})

@main.route('/edit_contact/<int:contact_id>', methods=['GET', 'POST'])
@login_required
def edit_contact(contact_id):
    contact = EmergencyContact.query.get_or_404(contact_id)
    if request.method == 'POST':
        contact.name = request.form.get('name')
        contact.phone = request.form.get('phone')
        contact.email = request.form.get('email')
        contact.relationship = request.form.get('relationship')
        db.session.commit()
        flash('Contact updated!', 'success')
        return redirect(url_for('main.emergency_contacts'))
    return render_template('edit_contact.html', contact=contact)

@main.route('/checkin', methods=['POST'])
@login_required
def checkin():
    if current_user.role != 'student':
        return jsonify({'error': 'Not a student'}), 403

    data = request.get_json()
    location_name = data.get('location_name')
    message = data.get('message', '')

    student = Student.query.filter_by(user_id=current_user.id).first()
    checkin = CheckIn(student_id=student.id, location_name=location_name,
                     message=message)
    db.session.add(checkin)
    db.session.commit()

    return jsonify({'status': 'checked_in', 'location': location_name})

@main.route('/api/students_locations')
@login_required
def students_locations():
    if current_user.role not in ['admin', 'parent']:
        return jsonify({'error': 'Unauthorized'}), 403

    if current_user.role == 'parent':
        parent = Parent.query.filter_by(user_id=current_user.id).first()
        students = Student.query.filter_by(parent_id=parent.id).all()
    else:
        students = Student.query.all()

    data = []
    for s in students:
        if s.current_latitude and s.current_longitude:
            data.append({
                'name': s.user.name,
                'roll': s.roll_number,
                'lat': s.current_latitude,
                'lon': s.current_longitude,
                'on_campus': s.is_on_campus,
                'last_seen': s.last_seen.strftime('%I:%M %p') if s.last_seen else 'Never'
            })

    return jsonify(data)

@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
      email = request.form.get('email')
      user = User.query.filter_by(email=email).first()
      if user:
            # Generate a simple reset token
            import secrets
            token = secrets.token_urlsafe(32)
            # Store token in session temporarily
            from flask import session
            session[f'reset_token_{email}'] = token
            reset_link = url_for('main.reset_password', 
                                token=token, email=email, _external=True)
            try:
                msg = Message(
                    subject='SafeCampus — Password Reset',
                    recipients=[email],
                    body=f'''Hello {user.name},

Click this link to reset your password:
{reset_link}

This link expires when you close your browser.

SafeCampus Team'''
                )
                mail.send(msg)
                flash('Password reset link sent to your email!', 'success')
            except:
                flash('Could not send email. Contact admin.', 'danger')
    else:
            flash('No account found with that email.', 'danger')
    return render_template('forgot_password.html')

@main.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    email = request.args.get('email')
    from flask import session
    stored_token = session.get(f'reset_token_{email}')
    
    if not stored_token or stored_token != token:
        flash('Invalid or expired reset link.', 'danger')
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        new_password = request.form.get('password')
        user = User.query.filter_by(email=email).first()
        if user:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            session.pop(f'reset_token_{email}', None)
            flash('Password reset successfully! Please login.', 'success')
            return redirect(url_for('main.login'))
    
    return render_template('reset_password.html', token=token, email=email)
@main.route('/emergency_contacts', methods=['GET', 'POST'])
@login_required
def emergency_contacts():
    if current_user.role != 'student':
        return redirect(url_for('main.dashboard'))
    
    student = Student.query.filter_by(user_id=current_user.id).first()
    
    if request.method == 'POST':
        name = request.form.get('name')
        phone = request.form.get('phone')
        email = request.form.get('email')
        relationship = request.form.get('relationship')
        
        existing = EmergencyContact.query.filter_by(student_id=student.id).count()
        if existing >= 2:
            flash('Maximum 2 emergency contacts allowed.', 'warning')
            return redirect(url_for('main.emergency_contacts'))
        
        contact = EmergencyContact(
            student_id=student.id,
            name=name,
            phone=phone,
            email=email,
            relationship=relationship
        )
        db.session.add(contact)
        db.session.commit()

        flash('Emergency contact added!', 'success')
        return redirect(url_for('main.emergency_contacts'))
    
    contacts = EmergencyContact.query.filter_by(student_id=student.id).all()
    return render_template(
        'emergency_contacts.html',
        contacts=contacts,
        student=student
    )


@main.route('/delete_contact/<int:contact_id>')
@login_required
def delete_contact(contact_id):
    if current_user.role != 'student':
        return redirect(url_for('main.dashboard'))

    student = Student.query.filter_by(user_id=current_user.id).first()
    contact = EmergencyContact.query.get_or_404(contact_id)

    if contact.student_id != student.id:
        flash('Unauthorized action.', 'danger')
        return redirect(url_for('main.emergency_contacts'))

    db.session.delete(contact)
    db.session.commit()

    flash('Contact removed.', 'info')
    return redirect(url_for('main.emergency_contacts'))
def send_campus_alert(student, entered_campus):
    if not student.parent_id:
        return
    parent = Parent.query.get(student.parent_id)
    if not parent:
        return
    parent_user = User.query.get(parent.user_id)
    status = "entered" if entered_campus else "left"
    time_now = datetime.utcnow().strftime('%I:%M %p')
    try:
        msg = Message(
            subject=f'SafeCampus Alert — {student.user.name} {status} campus',
            recipients=[parent_user.email],
            body=f'''Hello,

{student.user.name} has {status} campus at {time_now}.

Stay safe,
SafeCampus Team'''
        )
        mail.send(msg)
    except:
        pass

def send_sos_alert(student, lat, lon):
    maps_link = f"https://www.google.com/maps?q={lat},{lon}"
    time_now = datetime.utcnow().strftime('%I:%M %p')
    
    recipients = []
    
    if student.parent_id:
        parent = Parent.query.get(student.parent_id)
        if parent:
            parent_user = User.query.get(parent.user_id)
            if parent_user and parent_user.email:
                recipients.append(parent_user.email)
    
    contacts = EmergencyContact.query.filter_by(student_id=student.id).all()
    for contact in contacts:
        if contact.email:
            recipients.append(contact.email)
    
    if not recipients:
        return
        
    try:
        msg = Message(
            subject=f'🚨 SOS ALERT — {student.user.name} needs help!',
            recipients=recipients,
            body=f'''EMERGENCY ALERT!

{student.user.name} has triggered an SOS alert at {time_now}.

Last known location: {maps_link}

Please call them immediately or contact campus security: 044-27417000

SafeCampus Team'''
        )
        mail.send(msg)
    except:
        pass