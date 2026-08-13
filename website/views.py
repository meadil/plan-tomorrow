from flask import Blueprint, render_template, request, jsonify
from .models import Task
from . import db
from datetime import datetime, date, time

views = Blueprint('views', __name__)

# Helper to format Python time object to "09:30 AM" string
def format_time_str(t):
    return t.strftime("%I:%M %p").lstrip("0") if t else None

@views.route('/')
def home():
    return render_template("base.html", current_time=datetime.now())

# Fetch tasks ordered by start_time (nulls last), then creation order
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
            'raw_start_time': t.start_time.strftime("%H:%M") if t.start_time else "",
            'raw_end_time': t.end_time.strftime("%H:%M") if t.end_time else "",
            'is_completed': t.is_completed
        } for t in tasks
    ])

# Add task with start and end time
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

    return jsonify({'success': True}), 201

# Edit task title and times
@views.route('/edit-task/<int:task_id>', methods=['POST'])
def edit_task(task_id):
    task = Task.query.get_or_404(task_id)
    data = request.get_json() or {}

    title = data.get('title')
    start_time_str = data.get('start_time')
    end_time_str = data.get('end_time')

    if title:
        task.title = title
    
    task.start_time = datetime.strptime(start_time_str, '%H:%M').time() if start_time_str else None
    task.end_time = datetime.strptime(end_time_str, '%H:%M').time() if end_time_str else None

    db.session.commit()
    return jsonify({'success': True})

# Delete task
@views.route('/delete-task/<int:task_id>', methods=['POST'])
def delete_task(task_id):
    task = Task.query.get_or_404(task_id)
    db.session.delete(task)
    db.session.commit()
    return jsonify({'success': True})

@views.route('/toggle-task/<int:task_id>', methods=['POST'])
def toggle_task(task_id):
    task = Task.query.get_or_404(task_id)
    task.is_completed = not task.is_completed
    db.session.commit()
    return jsonify({'id': task.id, 'is_completed': task.is_completed})