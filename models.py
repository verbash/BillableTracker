from datetime import datetime
from app import db
from flask_login import UserMixin

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256))
    clients = db.relationship('Client', backref='user', lazy=True)
    time_entries = db.relationship('TimeEntry', backref='user', lazy=True)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    billing_address = db.Column(db.Text)
    billing_frequency = db.Column(db.String(20))  # weekly, biweekly, monthly, semi-monthly
    rate_per_hour = db.Column(db.Float)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    time_entries = db.relationship('TimeEntry', backref='client', lazy=True)

class TimeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime)
    duration = db.Column(db.Float)  # in hours
    notes = db.Column(db.Text)
    is_manual = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)

class Invoice(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    invoice_number = db.Column(db.String(20), unique=True)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    total_hours = db.Column(db.Float)
    total_amount = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='draft')  # draft, sent, paid
