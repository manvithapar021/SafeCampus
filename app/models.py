from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(60), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')
    phone = db.Column(db.String(15), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    student_profile = db.relationship('Student', backref='user', uselist=False)
    parent_profile = db.relationship('Parent', backref='user', uselist=False)

    def __repr__(self):
        return f"User('{self.name}', '{self.email}', '{self.role}')"

class Student(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    roll_number = db.Column(db.String(20), unique=True, nullable=False)
    department = db.Column(db.String(100), nullable=True)
    year = db.Column(db.Integer, nullable=True)
    current_latitude = db.Column(db.Float, nullable=True)
    current_longitude = db.Column(db.Float, nullable=True)
    is_on_campus = db.Column(db.Boolean, default=False)
    last_seen = db.Column(db.DateTime, nullable=True)
    parent_id = db.Column(db.Integer, db.ForeignKey('parent.id'), nullable=True)
    emergency_contacts = db.relationship('EmergencyContact', backref='student', lazy=True)

    location_history = db.relationship('LocationHistory', backref='student', lazy=True)
    checkins = db.relationship('CheckIn', backref='student', lazy=True)

    def __repr__(self):
        return f"Student('{self.roll_number}', on_campus={self.is_on_campus})"

class Parent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    phone = db.Column(db.String(15), nullable=True)
    children = db.relationship('Student', backref='parent', lazy=True,
                               foreign_keys='Student.parent_id')

    def __repr__(self):
        return f"Parent('{self.user_id}')"

class LocationHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_on_campus = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f"Location(student={self.student_id}, time={self.timestamp})"

class CheckIn(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    location_name = db.Column(db.String(100), nullable=False)
    message = db.Column(db.String(200), nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"CheckIn('{self.location_name}', '{self.timestamp}')"

class SOSAlert(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    latitude = db.Column(db.Float, nullable=False)
    longitude = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime, nullable=True)
    student = db.relationship('Student', backref='sos_alerts', lazy=True)

    def __repr__(self):
        return f"SOS(student={self.student_id}, resolved={self.is_resolved})"
    
class EmergencyContact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120), nullable=True)
    relationship = db.Column(db.String(50), nullable=False, default='Friend')