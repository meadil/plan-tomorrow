from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import resend
import os
from .models import User, Task
from . import db
from datetime import datetime, date, time

views = Blueprint('views', __name__)

# Initialize Resend API key from environment variable
resend.api_key = os.environ.get('RESEND_API_KEY')

def format_time_str(t):
    return t.strftime("%I:%M %p").lstrip("0") if t else None

@views.route('/')
def home():
    return render_template("base.html", current_time=datetime.now())

@views.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):
            login_user(user, remember=True)
            return redirect(url_for('views.home'))
        else:
            flash('Invalid email or password', category='error')

    return render_template("login.html")

@views.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash('Email already registered', category='error')
        else:
            new_user = User(
                email=email,
                password=generate_password_hash(password, method='scrypt')
            )
            db.session.add(new_user)
            db.session.commit()

            # Send verification email via Resend
            try:
                params = {
                    "from": "Plan Tomorrow <onboarding@resend.dev>",
                    "to": [email],
                    "subject": "Verify your Plan Tomorrow account",
                    "html": """
                    <div style="font-family: sans-serif; max-width: 480px; margin: 0 auto; padding: 20px; border: 1px solid #e5e8eb; border-radius: 16px;">
                        <h2 style="color: #000;">Verify your email</h2>
                        <p style="color: #50545c;">Welcome to <strong>Plan Tomorrow</strong>! Click the button below to verify your email address and start organizing your day.</p>
                        <a href="#" style="display: inline-block; background: #000; color: #fff; padding: 12px 24px; border-radius: 10px; text-decoration: none; font-weight: bold; margin: 15px 0;">Verify Email Address</a>
                        <p style="color: #a0a4ac; font-size: 0.8rem;">If you didn't create an account, you can safely ignore this email.</p>
                    </div>
                    """
                }
                resend.Emails.send(params)
            except Exception as e:
                print("Failed to send verification email:", e)

            login_user(new_user, remember=True)
            return redirect(url_for('views.home'))

    return render_template("signup.html")

@views.route('/get-tasks', methods=['GET'])
def get_tasks():
    date_str = request.args.get('date')
    if not date_str:
        target_date = date.today()
    else:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
    tasks = Task.query.filter_by(date=target_date)\
        .order_by(Task.start_time.asc().nullslast(), Task.created_at.asc()).all()
    
    return jsonify([
        {
            'id': t.id,
            'title': t.title,
            'start_time': format_time_str(t.start_time),
            'end_time': format_time_str(t.end_time),
            'raw_start': t.start_time.strftime('%H:%M') if t.start_time else "",
            'raw_end': t.end_time.strftime('%H:%M') if t.end_time else "",
            'is_completed': t.is_completed
        } for t in tasks
    ])

@views.route('/add-task', methods=['POST'])
def add_task():
    data = request.get_json() or {}
    title = data.get('title')
    date_str = data.get('date')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    if not title or not date_str:
        return jsonify({'error': 'Missing title or date'}), 400

    task_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    parsed_start = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
    parsed_end = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None

    new_task = Task(
        title=title, 
        date=task_date,
        start_time=parsed_start,
        end_time=parsed_end
    )
    db.session.add(new_task)
    db.session.commit()

    return jsonify({
        'id': new_task.id,
        'title': new_task.title,
        'start_time': format_time_str(new_task.start_time),
        'end_time': format_time_str(new_task.end_time),
        'is_completed': new_task.is_completed
    }), 201

@views.route('/edit-task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json() or {}

    if 'title' in data and data['title'].strip():
        task.title = data['title'].strip()

    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    task.start_time = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
    task.end_time = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None

    db.session.commit()
    return jsonify({
        'id': task.id,
        'title': task.title,
        'start_time': format_time_str(task.start_time),
        'end_time': format_time_str(task.end_time),
        'is_completed': task.is_completed
    })

@views.route('/toggle-task/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_completed = not task.is_completed
    db.session.commit()
    return jsonify({'id': task.id, 'is_completed': task.is_completed})

@views.route('/delete-task/<int:task_id>', methods=['DELETE'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})