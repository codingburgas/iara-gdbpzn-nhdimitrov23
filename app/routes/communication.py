from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.db import db
from app.models import Communication, MessageTemplate, Incident
from datetime import datetime
from psycopg2.extras import RealDictCursor

communication_bp = Blueprint('communication', __name__)


@communication_bp.route('/')
@login_required
def index():
    """Communication center"""
    templates = MessageTemplate.get_all()

    conn = db.get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute('''
            SELECT c.*, u.first_name, u.last_name
            FROM communications c
            LEFT JOIN users u ON c.user_id = u.id
            ORDER BY c.created_at DESC LIMIT 50
        ''')
        recent_messages = cur.fetchall()

    return render_template('communication/index.html',
                           templates=templates,
                           recent_messages=recent_messages)


@communication_bp.route('/incident/<int:incident_id>')
@login_required
def incident_chat(incident_id):
    """Incident-specific chat"""
    incident = Incident.get_by_id(incident_id)
    if not incident:
        flash('Произшествие не е намерено', 'danger')
        return redirect(url_for('communication.index'))

    messages = incident.get_communications(100)
    templates = MessageTemplate.get_all()

    return render_template('communication/incident_chat.html',
                           incident=incident,
                           messages=messages,
                           templates=templates)


@communication_bp.route('/send', methods=['POST'])
@login_required
def send_message():
    """Send a message"""
    incident_id = request.form.get('incident_id')
    content = request.form.get('content')
    message_type = request.form.get('message_type', 'text')
    template_id = request.form.get('template_id')

    if not content:
        flash('Моля, въведете съобщение', 'danger')
        return redirect(request.referrer or url_for('communication.index'))

    try:
        comm = Communication()
        comm.incident_id = int(incident_id) if incident_id else None
        comm.user_id = current_user.id
        comm.content = content
        comm.message_type = message_type
        comm.is_template = bool(template_id)
        comm.template_id = int(template_id) if template_id else None

        comm.save()
        flash('Съобщението е изпратено', 'success')
    except Exception as e:
        flash(f'Грешка при изпращане: {str(e)}', 'danger')

    return redirect(request.referrer or url_for('communication.index'))


@communication_bp.route('/template/new', methods=['GET', 'POST'])
@login_required
def new_template():
    """Create a new message template"""
    if request.method == 'POST':
        try:
            template = MessageTemplate()
            template.name = request.form.get('name')
            template.category = request.form.get('category')
            template.content = request.form.get('content')
            template.created_by = current_user.id

            template.save()
            flash('Шаблонът е създаден успешно', 'success')
            return redirect(url_for('communication.index'))
        except Exception as e:
            flash(f'Грешка при създаване на шаблон: {str(e)}', 'danger')

    return render_template('communication/new_template.html')


@communication_bp.route('/api/messages')
@login_required
def api_messages():
    """API endpoint for messages"""
    incident_id = request.args.get('incident_id')
    limit = request.args.get('limit', 50, type=int)

    conn = db.get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        if incident_id:
            cur.execute('''
                SELECT c.*, u.first_name, u.last_name
                FROM communications c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.incident_id = %s
                ORDER BY c.created_at DESC
                LIMIT %s
            ''', (incident_id, limit))
        else:
            cur.execute('''
                SELECT c.*, u.first_name, u.last_name
                FROM communications c
                LEFT JOIN users u ON c.user_id = u.id
                ORDER BY c.created_at DESC
                LIMIT %s
            ''', (limit,))

        messages = cur.fetchall()

    return jsonify([{
        'id': m['id'],
        'incident_id': m['incident_id'],
        'user_name': f"{m['first_name']} {m['last_name']}" if m.get('first_name') else 'Система',
        'content': m['content'],
        'message_type': m['message_type'],
        'is_template': m['is_template'],
        'created_at': m['created_at'].isoformat() if m['created_at'] else None,
        'media_url': m['media_url']
    } for m in messages])