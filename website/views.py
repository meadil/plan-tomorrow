from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from datetime import datetime, date
from .models import Task
from . import db

views = Blueprint('views', __name__)

def format_time_str(t):
    """Formats time object to '9:30 AM'."""
    return t.strftime("%I:%M %p").lstrip("0") if t else None

@views.route('/')
@login_required
def home():
    return render_template("home.html", current_time=datetime.now())

@views.route('/get-tasks', methods=['GET'])
@login_required
def get_tasks():
    date_str = request.args.get('date')
    if not date_str:
        target_date = date.today()
    else:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        
    tasks = Task.query.filter_by(user_id=current_user.id, date=target_date)\
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
@login_required
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
        end_time=parsed_end,
        user_id=current_user.id
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
@login_required
def edit_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
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
@login_required
def toggle_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    task.is_completed = not task.is_completed
    db.session.commit()
    return jsonify({'id': task.id, 'is_completed': task.is_completed})

@views.route('/delete-task/<int:task_id>', methods=['DELETE'])
@login_required
def delete_task(task_id):
    task = Task.query.filter_by(id=task_id, user_id=current_user.id).first_or_404()
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})