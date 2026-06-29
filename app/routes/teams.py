# app/routes/teams.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.db import db
from app.models import Team, User, Incident
from datetime import datetime

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
        flash('Team not found', 'danger')
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
        flash('You do not have permission to create teams', 'danger')
        return redirect(url_for('teams.index'))

    if request.method == 'POST':
        team = Team()
        team.name = request.form.get('name')
        team.code = request.form.get('code').upper()
        team.station = request.form.get('station')
        team.vehicle_type = request.form.get('vehicle_type')
        team.vehicle_registration = request.form.get('vehicle_registration')

        team.save()

        flash(f'Team {team.name} created successfully', 'success')
        return redirect(url_for('teams.view', team_id=team.id))

    return render_template('teams/new.html')


@teams_bp.route('/<int:team_id>/update', methods=['POST'])
@login_required
def update(team_id):
    """Update team details"""
    team = Team.get_by_id(team_id)
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('teams.index'))

    if request.form.get('name'):
        team.name = request.form.get('name')
    if request.form.get('station'):
        team.station = request.form.get('station')
    if request.form.get('vehicle_type'):
        team.vehicle_type = request.form.get('vehicle_type')
    if request.form.get('vehicle_registration'):
        team.vehicle_registration = request.form.get('vehicle_registration')
    if request.form.get('status'):
        team.status = request.form.get('status')

    team.save()
    flash('Team updated successfully', 'success')
    return redirect(url_for('teams.view', team_id=team.id))


@teams_bp.route('/<int:team_id>/add-member', methods=['POST'])
@login_required
def add_member(team_id):
    """Add a member to the team"""
    team = Team.get_by_id(team_id)
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('teams.index'))

    user_id = request.form.get('user_id')
    user = User.get_by_id(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('teams.view', team_id=team_id))

    user.team_id = team.id
    user.save()

    flash(f'{user.get_full_name()} added to {team.name}', 'success')
    return redirect(url_for('teams.view', team_id=team_id))


@teams_bp.route('/<int:team_id>/remove-member', methods=['POST'])
@login_required
def remove_member(team_id):
    """Remove a member from the team"""
    team = Team.get_by_id(team_id)
    if not team:
        flash('Team not found', 'danger')
        return redirect(url_for('teams.index'))

    user_id = request.form.get('user_id')
    user = User.get_by_id(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('teams.view', team_id=team_id))

    user.team_id = None
    user.save()

    flash(f'{user.get_full_name()} removed from {team.name}', 'info')
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