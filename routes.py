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
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Please fill in both username and password')
            return render_template('login.html')
            
        app.logger.info(f"Login attempt for username: {username}")
        user = User.query.filter_by(username=username).first()
        
        if user is None:
            app.logger.warning(f"No user found with username: {username}")
            flash('Invalid username or password')
            return render_template('login.html')
            
        if not check_password_hash(user.password_hash, password):
            app.logger.warning(f"Invalid password for user: {username}")
            flash('Invalid username or password')
            return render_template('login.html')
            
        login_user(user)
        app.logger.info(f"Successful login for user: {username}")
        
        next_page = request.args.get('next')
        if not next_page or not next_page.startswith('/'):
            next_page = url_for('dashboard')
        return redirect(next_page)
        
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        
        if not username or not email or not password:
            flash('Please fill in all fields')
            return render_template('register.html')
            
        if User.query.filter_by(username=username).first():
            flash('Username already exists')
            return render_template('register.html')
            
        if User.query.filter_by(email=email).first():
            flash('Email already registered')
            return render_template('register.html')
            
        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password)
        )
        db.session.add(user)
        db.session.commit()
        
        app.logger.info(f"New user registered: {username}")
        flash('Registration successful! Please log in.')
        return redirect(url_for('login'))
        
    return render_template('register.html')

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
@app.route('/time_entries')
@login_required
def time_entries():
    entries = TimeEntry.query.filter_by(user_id=current_user.id)\
        .order_by(TimeEntry.start_time.desc()).all()
    return render_template('time_entries.html', entries=entries)