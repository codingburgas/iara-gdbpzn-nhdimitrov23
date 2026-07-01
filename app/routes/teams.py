from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.db import db
from app.models import Team, User, Incident
from datetime import datetime
from psycopg2.extras import RealDictCursor

teams_bp = Blueprint('teams', __name__)


@teams_bp.route('/')
@login_required
def index():
    """Teams overview"""
    teams = Team.get_all()
    return render_template('teams/index.html', teams=teams)


@teams_bp.route('/<int:team_id>')
@login_required
def view(team_id):
    """View team details"""
    team = Team.get_by_id(team_id)
    if not team:
        flash('Екип не е намерен', 'danger')
        return redirect(url_for('teams.index'))

    members = User.get_by_team(team_id)
    current_incident = Incident.get_by_id(team.current_incident_id) if team.current_incident_id else None

    return render_template('teams/view.html',
                           team=team,
                           members=members,
                           current_incident=current_incident)


@teams_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    """Create a new team"""
    if current_user.role not in ['admin', 'dispatcher']:
        flash('Нямате права да създавате екипи', 'danger')
        return redirect(url_for('teams.index'))

    if request.method == 'POST':
        try:
            team = Team()
            team.name = request.form.get('name')
            team.code = request.form.get('code').upper()
            team.station = request.form.get('station')
            team.vehicle_type = request.form.get('vehicle_type')
            team.vehicle_registration = request.form.get('vehicle_registration')
            team.status = 'available'

            # Check if code exists
            if Team.get_by_code(team.code):
                flash('Този код вече съществува', 'danger')
                return render_template('teams/new.html')

            team.save()

            flash(f'Екип {team.name} създаден успешно', 'success')
            return redirect(url_for('teams.view', team_id=team.id))
        except Exception as e:
            flash(f'Грешка при създаване на екип: {str(e)}', 'danger')

    return render_template('teams/new.html')


@teams_bp.route('/<int:team_id>/update', methods=['POST'])
@login_required
def update(team_id):
    """Update team details"""
    team = Team.get_by_id(team_id)
    if not team:
        flash('Екип не е намерен', 'danger')
        return redirect(url_for('teams.index'))

    try:
        if request.form.get('name'):
            team.name = request.form.get('name')
        if request.form.get('station'):
            team.station = request.form.get('station')
        if request.form.get('vehicle_type'):
            team.vehicle_type = request.form.get('vehicle_type')
        if request.form.get('vehicle_registration'):
            team.vehicle_registration = request.form.get('vehicle_registration')
        if request.form.get('status'):
            old_status = team.status
            team.status = request.form.get('status')

            # If status changes to available, clear current incident
            if team.status == 'available' and old_status != 'available':
                team.current_incident_id = None

        team.save()
        flash('Екипът е обновен успешно', 'success')
    except Exception as e:
        flash(f'Грешка при обновяване: {str(e)}', 'danger')

    return redirect(url_for('teams.view', team_id=team.id))


@teams_bp.route('/<int:team_id>/add-member', methods=['POST'])
@login_required
def add_member(team_id):
    """Add a member to the team"""
    if current_user.role not in ['admin', 'dispatcher']:
        flash('Нямате права за това действие', 'danger')
        return redirect(url_for('teams.index'))

    team = Team.get_by_id(team_id)
    if not team:
        flash('Екип не е намерен', 'danger')
        return redirect(url_for('teams.index'))

    user_id = request.form.get('user_id')
    user = User.get_by_id(user_id)
    if not user:
        flash('Потребител не е намерен', 'danger')
        return redirect(url_for('teams.view', team_id=team_id))

    try:
        user.team_id = team.id
        user.save()
        flash(f'{user.get_full_name()} добавен към {team.name}', 'success')
    except Exception as e:
        flash(f'Грешка: {str(e)}', 'danger')

    return redirect(url_for('teams.view', team_id=team_id))


@teams_bp.route('/<int:team_id>/remove-member', methods=['POST'])
@login_required
def remove_member(team_id):
    """Remove a member from the team"""
    if current_user.role not in ['admin', 'dispatcher']:
        flash('Нямате права за това действие', 'danger')
        return redirect(url_for('teams.index'))

    team = Team.get_by_id(team_id)
    if not team:
        flash('Екип не е намерен', 'danger')
        return redirect(url_for('teams.index'))

    user_id = request.form.get('user_id')
    user = User.get_by_id(user_id)
    if not user:
        flash('Потребител не е намерен', 'danger')
        return redirect(url_for('teams.view', team_id=team_id))

    try:
        user.team_id = None
        user.save()
        flash(f'{user.get_full_name()} премахнат от {team.name}', 'info')
    except Exception as e:
        flash(f'Грешка: {str(e)}', 'danger')

    return redirect(url_for('teams.view', team_id=team_id))


@teams_bp.route('/api/locations')
@login_required
def api_locations():
    """API endpoint for team locations"""
    teams = Team.get_all()

    return jsonify([{
        'id': t.id,
        'name': t.name,
        'status': t.status,
        'latitude': float(t.latitude) if t.latitude else None,
        'longitude': float(t.longitude) if t.longitude else None,
        'incident_id': t.current_incident_id
    } for t in teams])