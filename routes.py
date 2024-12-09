from flask import render_template, redirect, url_for, request, flash, jsonify, send_file
from flask_login import login_required, current_user, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import uuid
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
            category=request.form.get('category'),
            status='active',
            user_id=current_user.id
        )
        db.session.add(client)
        db.session.commit()
        flash('Client added successfully')
        return redirect(url_for('clients'))
    
    # Get filter parameters
    status = request.args.get('status', '')
    category = request.args.get('category', '')
    search = request.args.get('search', '')
    
    # Build query
    query = Client.query.filter_by(user_id=current_user.id)
    
    if status:
        query = query.filter_by(status=status)
    if category:
        query = query.filter_by(category=category)
    if search:
        search_term = f"%{search}%"
        query = query.filter(Client.name.ilike(search_term) | Client.email.ilike(search_term))
    
    clients = query.order_by(Client.name).all()
    
    # Get unique categories for filter dropdown
    categories = db.session.query(Client.category)\
        .filter(Client.user_id == current_user.id)\
        .filter(Client.category.isnot(None))\
        .distinct()\
        .order_by(Client.category)\
        .all()
    categories = [cat[0] for cat in categories if cat[0]]  # Flatten and remove None
    
    return render_template('clients.html', clients=clients, categories=categories)
@app.route('/clients/add', methods=['POST'])
@login_required
def clients_add():
    client = Client(
        name=request.form['name'],
        email=request.form['email'],
        billing_address=request.form['billing_address'],
        billing_frequency=request.form['billing_frequency'],
        rate_per_hour=float(request.form['rate_per_hour']),
        category=request.form.get('category'),
        status='active',
        notes=request.form.get('notes'),
        user_id=current_user.id
    )
    db.session.add(client)
    db.session.commit()
    flash('Client added successfully')
    return redirect(url_for('clients'))

@app.route('/clients/edit/<int:client_id>', methods=['POST'])
@login_required
def edit_client(client_id):
    client = Client.query.filter_by(id=client_id, user_id=current_user.id).first_or_404()
    
    client.name = request.form['name']
    client.email = request.form['email']
    client.billing_address = request.form['billing_address']
    client.billing_frequency = request.form['billing_frequency']
    client.rate_per_hour = float(request.form['rate_per_hour'])
    client.category = request.form.get('category')
    client.status = request.form.get('status', 'active')
    client.notes = request.form.get('notes')
    
    db.session.commit()
    flash('Client updated successfully')
    return redirect(url_for('clients'))


@app.route('/time/start', methods=['POST'])
@login_required
def start_timer():
    import pytz
    utc = pytz.UTC
    
    entry = TimeEntry(
        start_time=datetime.now(utc),
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
    import pytz
    
    user_tz = pytz.timezone(current_user.timezone)
    utc = pytz.UTC
    
    # Parse the local time and convert to UTC
    local_start = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
    start_time = user_tz.localize(local_start).astimezone(utc)
    
    end_time = None
    duration = float(request.form['duration'])
    
    # Only parse end_time if it's provided and not empty
    if request.form.get('end_time'):
        local_end = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        end_time = user_tz.localize(local_end).astimezone(utc)
    
    entry = TimeEntry(
        start_time=start_time,
        end_time=end_time,
        duration=duration,
        notes=request.form.get('notes', ''),
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
        invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{client_id}-{uuid.uuid4().hex[:6].upper()}"
    )
    db.session.add(invoice)
    db.session.commit()
    
    # Get aggregation preference
    aggregate_by_day = request.form.get('aggregate_by_day') == 'on'
    
    pdf = generate_invoice_pdf(invoice, entries, client, aggregate_by_day=aggregate_by_day)
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
@app.route('/time/entries')
@login_required
def get_time_entries():
    import pytz
    
    start_date = request.args.get('start')
    end_date = request.args.get('end')
    
    user_tz = pytz.timezone(current_user.timezone)
    utc = pytz.UTC
    
    query = TimeEntry.query.filter_by(user_id=current_user.id)
    
    if start_date:
        local_start = datetime.strptime(start_date, '%Y-%m-%d')
        utc_start = user_tz.localize(local_start).astimezone(utc)
        query = query.filter(TimeEntry.start_time >= utc_start)
    if end_date:
        local_end = datetime.strptime(end_date, '%Y-%m-%d')
        utc_end = user_tz.localize(local_end).astimezone(utc)
        query = query.filter(TimeEntry.start_time <= utc_end + timedelta(days=1))
    
    entries = query.order_by(TimeEntry.start_time.desc()).all()
    
    return jsonify({
        'entries': [{
            'id': entry.id,
            'start_time': entry.start_time.replace(tzinfo=utc).astimezone(user_tz).isoformat(),
            'end_time': entry.end_time.replace(tzinfo=utc).astimezone(user_tz).isoformat() if entry.end_time else None,
            'duration': entry.duration,
            'notes': entry.notes,
            'client_name': entry.client.name
        } for entry in entries]
    })
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    import pytz
    if request.method == 'POST':
        current_user.timezone = request.form['timezone']
        current_user.business_name = request.form['business_name']
        current_user.business_email = request.form['business_email']
        current_user.business_phone = request.form['business_phone']
        current_user.business_address = request.form['business_address']
        db.session.commit()
        flash('Settings updated successfully')
        return redirect(url_for('settings'))
    
    timezones = pytz.all_timezones
    return render_template('settings.html', timezones=timezones)

@app.route('/time/entry/<int:entry_id>')
@login_required
def get_time_entry(entry_id):
    entry = TimeEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    return jsonify({
        'id': entry.id,
        'start_time': entry.start_time.isoformat(),
        'end_time': entry.end_time.isoformat() if entry.end_time else None,
        'notes': entry.notes
    })

@app.route('/time/edit/<int:entry_id>', methods=['POST'])
@login_required
def edit_time_entry(entry_id):
    entry = TimeEntry.query.filter_by(id=entry_id, user_id=current_user.id).first_or_404()
    
    entry.start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
    if request.form.get('end_time'):
        entry.end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
        entry.duration = (entry.end_time - entry.start_time).total_seconds() / 3600
    entry.notes = request.form.get('notes', '')
    
    db.session.commit()
    return jsonify({'success': True})