# app/routes/incidents.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.db import db
from app.models import Incident, Team, User
from datetime import datetime
import json
import uuid

incidents_bp = Blueprint('incidents', __name__)


@incidents_bp.route('/dashboard')
@login_required
def dashboard():
    """Incident management dashboard"""
    # Get active incidents
    active_incidents = Incident.get_active()

    # Get recent incidents
    recent_incidents = Incident.get_recent(7)[:10]

    # Get available teams
    available_teams = Team.get_available()

    return render_template('incidents/dashboard.html',
                           active_incidents=active_incidents,
                           recent_incidents=recent_incidents,
                           available_teams=available_teams)


@incidents_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new_incident():
    """Create a new incident"""
    if request.method == 'POST':
        try:
            incident = Incident()
            incident.type = request.form.get('type')
            incident.address = request.form.get('address')
            incident.latitude = float(request.form.get('latitude'))
            incident.longitude = float(request.form.get('longitude'))
            incident.description = request.form.get('description')
            incident.hazardous_materials = request.form.get('hazardous_materials')
            incident.action_plan = request.form.get('action_plan')
            incident.priority = int(request.form.get('priority', 1))
            incident.reporter_name = request.form.get('reporter_name')
            incident.reporter_phone = request.form.get('reporter_phone')
            incident.dispatcher_id = current_user.id

            if request.form.get('dispatch_now'):
                incident.dispatched_at = datetime.utcnow()
                incident.status = 'dispatched'

                # Assign teams
                team_ids = request.form.getlist('team_ids')
                conn = db.get_connection()
                with conn.cursor() as cur:
                    for team_id in team_ids:
                        # Update team status
                        cur.execute('''
                                    UPDATE teams
                                    SET status              = 'dispatched',
                                        current_incident_id = %s
                                    WHERE id = %s
                                    ''', (incident.id, team_id))

                        # Create assignment
                        cur.execute('''
                                    INSERT INTO incident_assignments (incident_id, user_id, task)
                                    VALUES (%s, %s, %s)
                                    ''', (incident.id, current_user.id, f"Dispatch to {incident.address}"))
                    db.commit()
            else:
                incident.status = 'reported'

            incident.save()

            flash(f'Incident {incident.incident_number} created successfully', 'success')
            return redirect(url_for('incidents.view', incident_id=incident.id))

        except Exception as e:
            flash(f'Error creating incident: {str(e)}', 'danger')
            return render_template('incidents/new.html', teams=Team.get_all())

    return render_template('incidents/new.html', teams=Team.get_all())


@incidents_bp.route('/<int:incident_id>')
@login_required
def view(incident_id):
    """View incident details"""
    incident = Incident.get_by_id(incident_id)
    if not incident:
        flash('Incident not found', 'danger')
        return redirect(url_for('incidents.dashboard'))

    assignments = incident.get_assignments()
    communications = incident.get_communications(50)

    return render_template('incidents/view.html',
                           incident=incident,
                           assignments=assignments,
                           communications=communications)


@incidents_bp.route('/<int:incident_id>/update', methods=['POST'])
@login_required
def update(incident_id):
    """Update incident details"""
    incident = Incident.get_by_id(incident_id)
    if not incident:
        flash('Incident not found', 'danger')
        return redirect(url_for('incidents.dashboard'))

    if request.form.get('status'):
        incident.status = request.form.get('status')
        if incident.status == 'resolved':
            incident.resolved_at = datetime.utcnow()
        elif incident.status == 'closed':
            incident.closed_at = datetime.utcnow()

    if request.form.get('description'):
        incident.description = request.form.get('description')

    if request.form.get('action_plan'):
        incident.action_plan = request.form.get('action_plan')

    incident.save()

    flash('Incident updated successfully', 'success')
    return redirect(url_for('incidents.view', incident_id=incident.id))


@incidents_bp.route('/api/list')
@login_required
def api_list():
    """API endpoint for incident list"""
    status = request.args.get('status')

    conn = db.get_connection()
    with conn.cursor(cursor_factory=db.get_cursor().__self__.__class__) as cur:
        from psycopg2.extras import RealDictCursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        if status:
            cur.execute('SELECT * FROM incidents WHERE status = %s ORDER BY reported_at DESC', (status,))
        else:
            cur.execute('SELECT * FROM incidents ORDER BY reported_at DESC LIMIT 100')

        incidents = cur.fetchall()

        # Get dispatcher names
        for inc in incidents:
            if inc.get('dispatcher_id'):
                cur.execute('SELECT first_name, last_name FROM users WHERE id = %s', (inc['dispatcher_id'],))
                dispatcher = cur.fetchone()
                if dispatcher:
                    inc['dispatcher_name'] = f"{dispatcher['first_name']} {dispatcher['last_name']}"

    return jsonify([{
        'id': i['id'],
        'incident_number': i['incident_number'],
        'type': i['type'],
        'status': i['status'],
        'address': i['address'],
        'latitude': float(i['latitude']) if i['latitude'] else None,
        'longitude': float(i['longitude']) if i['longitude'] else None,
        'priority': i['priority'],
        'reported_at': i['reported_at'].isoformat() if i['reported_at'] else None,
        'dispatcher_name': i.get('dispatcher_name')
    } for i in incidents])

@incidents_bp.route('/<int:incident_id>/add-communication', methods=['POST'])
@login_required
def add_communication(incident_id):
    """Add communication to an incident"""
    from app.models import Communication

    incident = Incident.get_by_id(incident_id)
    if not incident:
        flash('Incident not found', 'danger')
        return redirect(url_for('incidents.dashboard'))

    content = request.form.get('content')
    if not content:
        flash('Message content is required', 'danger')
        return redirect(url_for('incidents.view', incident_id=incident.id))

    comm = Communication()
    comm.incident_id = incident.id
    comm.user_id = current_user.id
    comm.content = content
    comm.message_type = 'text'
    comm.is_template = False

    comm.save()

    flash('Message sent', 'success')
    return redirect(url_for('incidents.view', incident_id=incident.id))