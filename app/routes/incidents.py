from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.db import db
from app.models import Incident, Team, User, Communication
from datetime import datetime
import json
import uuid
from psycopg2.extras import RealDictCursor

incidents_bp = Blueprint('incidents', __name__)


@incidents_bp.route('/dashboard')
@login_required
def dashboard():
    """Incident management dashboard"""
    active_incidents = Incident.get_active()
    recent_incidents = Incident.get_recent(7)[:10]
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
            # Create incident object
            incident = Incident()

            # Set all fields
            incident.type = request.form.get('type')
            incident.address = request.form.get('address')

            # Handle coordinates
            lat = request.form.get('latitude')
            lng = request.form.get('longitude')

            if lat and lng:
                incident.latitude = float(lat)
                incident.longitude = float(lng)
            else:
                flash('Моля, изберете местоположение на картата', 'danger')
                return render_template('incidents/new.html', teams=Team.get_all())

            incident.description = request.form.get('description')
            incident.hazardous_materials = request.form.get('hazardous_materials')
            incident.action_plan = request.form.get('action_plan')
            incident.priority = int(request.form.get('priority', 3))
            incident.reporter_name = request.form.get('reporter_name')
            incident.reporter_phone = request.form.get('reporter_phone')
            incident.dispatcher_id = current_user.id
            incident.status = 'reported'

            # Save and get ID
            incident_id = incident.save()

            if not incident_id:
                flash('Грешка при създаване на произшествие', 'danger')
                return render_template('incidents/new.html', teams=Team.get_all())

            # Handle team assignments
            team_ids = request.form.getlist('team_ids')
            if team_ids:
                conn = db.get_connection()
                try:
                    with conn.cursor() as cur:
                        for team_id in team_ids:
                            team_id_int = int(team_id)
                            # Update team status
                            cur.execute('''
                                        UPDATE teams
                                        SET status              = 'dispatched',
                                            current_incident_id = %s,
                                            updated_at          = CURRENT_TIMESTAMP
                                        WHERE id = %s
                                        ''', (incident_id, team_id_int))

                            # Find a user in this team
                            cur.execute('SELECT id FROM users WHERE team_id = %s LIMIT 1', (team_id_int,))
                            user = cur.fetchone()
                            if user:
                                cur.execute('''
                                            INSERT INTO incident_assignments (incident_id, user_id, task, status)
                                            VALUES (%s, %s, %s, %s)
                                            ''', (incident_id, user[0], f"Изпращане до {incident.address}", 'assigned'))

                        db.commit()
                except Exception as e:
                    db.rollback()
                    print(f"Error assigning teams: {e}")

            flash(f'Произшествие {incident.incident_number} създадено успешно', 'success')
            return redirect(url_for('incidents.view', incident_id=incident_id))

        except Exception as e:
            db.rollback()
            import traceback
            traceback.print_exc()
            flash(f'Грешка при създаване на произшествие: {str(e)}', 'danger')
            return render_template('incidents/new.html', teams=Team.get_all())

    # GET request - show form
    teams = Team.get_all()
    return render_template('incidents/new.html', teams=teams)


@incidents_bp.route('/<int:incident_id>')
@login_required
def view(incident_id):
    """View incident details"""
    incident = Incident.get_by_id(incident_id)
    if not incident:
        flash('Произшествие не е намерено', 'danger')
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
        flash('Произшествие не е намерено', 'danger')
        return redirect(url_for('incidents.dashboard'))

    try:
        if request.form.get('status'):
            new_status = request.form.get('status')
            incident.status = new_status

            if new_status == 'resolved':
                incident.resolved_at = datetime.utcnow()
            elif new_status == 'closed':
                incident.closed_at = datetime.utcnow()
            elif new_status in ['dispatched', 'on_site', 'in_progress']:
                if not incident.dispatched_at:
                    incident.dispatched_at = datetime.utcnow()

        if request.form.get('description'):
            incident.description = request.form.get('description')

        if request.form.get('action_plan'):
            incident.action_plan = request.form.get('action_plan')

        incident.save()
        flash('Произшествието е обновено', 'success')
    except Exception as e:
        flash(f'Грешка при обновяване: {str(e)}', 'danger')

    return redirect(url_for('incidents.view', incident_id=incident_id))


@incidents_bp.route('/api/list')
@login_required
def api_list():
    """API endpoint for incident list"""
    status = request.args.get('status')
    conn = db.get_connection()

    with conn.cursor(cursor_factory=RealDictCursor) as cur:
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
    incident = Incident.get_by_id(incident_id)
    if not incident:
        flash('Произшествие не е намерено', 'danger')
        return redirect(url_for('incidents.dashboard'))

    content = request.form.get('content')
    if not content:
        flash('Моля, въведете съобщение', 'danger')
        return redirect(url_for('incidents.view', incident_id=incident.id))

    try:
        comm = Communication()
        comm.incident_id = incident.id  # This now works with the property
        comm.user_id = current_user.id
        comm.content = content
        comm.message_type = 'text'
        comm.is_template = False
        comm.save()
        flash('Съобщението е изпратено', 'success')
    except Exception as e:
        flash(f'Грешка при изпращане: {str(e)}', 'danger')

    return redirect(url_for('incidents.view', incident_id=incident_id))


@incidents_bp.route('/<int:incident_id>/assign-team', methods=['POST'])
@login_required
def assign_team(incident_id):
    """Assign a team to an incident"""
    incident = Incident.get_by_id(incident_id)
    if not incident:
        flash('Произшествие не е намерено', 'danger')
        return redirect(url_for('incidents.dashboard'))

    team_id = request.form.get('team_id')
    if not team_id:
        flash('Моля, изберете екип', 'danger')
        return redirect(url_for('incidents.view', incident_id=incident_id))

    team = Team.get_by_id(int(team_id))
    if not team:
        flash('Екип не е намерен', 'danger')
        return redirect(url_for('incidents.view', incident_id=incident_id))

    conn = db.get_connection()
    try:
        with conn.cursor() as cur:
            # Update team status
            cur.execute('''
                        UPDATE teams
                        SET status              = 'dispatched',
                            current_incident_id = %s,
                            updated_at          = CURRENT_TIMESTAMP
                        WHERE id = %s
                        ''', (incident.id, team.id))

            # Create assignment for team leader
            cur.execute("SELECT id FROM users WHERE team_id = %s AND role IN ('team_leader', 'admin') LIMIT 1",
                        (team.id,))
            user = cur.fetchone()
            if user:
                cur.execute('''
                            INSERT INTO incident_assignments (incident_id, user_id, task, status)
                            VALUES (%s, %s, %s, %s)
                            ''', (incident.id, user[0], f"Координиране на екип {team.name} на {incident.address}",
                                  'assigned'))

            db.commit()
    except Exception as e:
        db.rollback()
        flash(f'Грешка при изпращане на екип: {str(e)}', 'danger')
        return redirect(url_for('incidents.view', incident_id=incident_id))

    flash(f'Екип {team.name} беше изпратен', 'success')
    return redirect(url_for('incidents.view', incident_id=incident_id))


@incidents_bp.route('/<int:incident_id>/map')
@login_required
def map_view(incident_id):
    """View incident on map"""
    incident = Incident.get_by_id(incident_id)
    if not incident:
        flash('Произшествие не е намерено', 'danger')
        return redirect(url_for('incidents.dashboard'))

    return render_template('incidents/map_view.html', incident=incident)