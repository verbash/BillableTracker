from flask import render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
from app import app, db
from models import User, Client, TimeEntry, Invoice
from helpers import generate_invoice_pdf
import io

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        app.logger.debug(f"Login attempt for username: {username}")
        
        user = User.query.filter_by(username=username).first()
        if user:
            app.logger.debug("User found in database")
            if check_password_hash(user.password_hash, password):
                app.logger.debug("Password verified successfully")
                login_user(user)
                return redirect(url_for('dashboard'))
            else:
                app.logger.debug("Password verification failed")
        else:
            app.logger.debug("User not found in database")
        flash('Invalid username or password')
    return render_template('login.html')

@app.route('/clients', methods=['GET', 'POST'])
@login_required
def clients():
    if request.method == 'POST':
        client = Client(
            name=request.form['name'],
            email=request.form['email'],
            billing_address=request.form['billing_address'],
            billing_frequency=request.form['billing_frequency'],
            rate_per_hour=float(request.form['rate_per_hour']),
            user_id=current_user.id
        )
        db.session.add(client)
        db.session.commit()
        return redirect(url_for('clients'))
    
    clients = Client.query.filter_by(user_id=current_user.id).all()
    return render_template('clients.html', clients=clients)

@app.route('/time/start', methods=['POST'])
@login_required
def start_timer():
    entry = TimeEntry(
        start_time=datetime.utcnow(),
        user_id=current_user.id,
        client_id=request.form['client_id']
    )
    db.session.add(entry)
    db.session.commit()
    return jsonify({'id': entry.id})

@app.route('/time/stop/<int:entry_id>', methods=['POST'])
@login_required
def stop_timer(entry_id):
    entry = TimeEntry.query.get_or_404(entry_id)
    entry.end_time = datetime.utcnow()
    entry.duration = (entry.end_time - entry.start_time).total_seconds() / 3600
    db.session.commit()
    return jsonify({'duration': entry.duration})

@app.route('/time/manual', methods=['POST'])
@login_required
def manual_entry():
    entry = TimeEntry(
        start_time=datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M'),
        end_time=datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M'),
        duration=float(request.form['duration']),
        notes=request.form['notes'],
        is_manual=True,
        user_id=current_user.id,
        client_id=request.form['client_id']
    )
    db.session.add(entry)
    db.session.commit()
    return redirect(url_for('time_entries'))

@app.route('/invoices/generate/<int:client_id>', methods=['POST'])
@login_required
def generate_invoice(client_id):
    client = Client.query.get_or_404(client_id)
    start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d')
    end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d')
    
    entries = TimeEntry.query.filter(
        TimeEntry.client_id == client_id,
        TimeEntry.start_time >= start_date,
        TimeEntry.start_time <= end_date
    ).all()
    
    total_hours = sum(entry.duration for entry in entries)
    total_amount = total_hours * client.rate_per_hour
    
    invoice = Invoice(
        client_id=client_id,
        start_date=start_date,
        end_date=end_date,
        total_hours=total_hours,
        total_amount=total_amount,
        invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{client_id}"
    )
    db.session.add(invoice)
    db.session.commit()
    
    pdf = generate_invoice_pdf(invoice, entries, client)
    return send_file(
        io.BytesIO(pdf),
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f"invoice_{invoice.invoice_number}.pdf"
    )
