# app/routes/admin.py
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app.db import db
from app.models import User, Team, Incident, Resource
from datetime import datetime
from werkzeug.security import generate_password_hash

admin_bp = Blueprint('admin', __name__)


@admin_bp.route('/')
@login_required
def dashboard():
    """Admin dashboard"""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))

    # Stats
    total_users = len(User.get_all())
    total_teams = len(Team.get_all())
    active_incidents = len(Incident.get_active())

    return render_template('admin/dashboard.html',
                           total_users=total_users,
                           total_teams=total_teams,
                           total_incidents=len(Incident.get_all()),
                           active_incidents=active_incidents)


@admin_bp.route('/users')
@login_required
def users():
    """Manage users"""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))

    users = User.get_all()
    teams = Team.get_all()
    return render_template('admin/users.html', users=users, teams=teams)


@admin_bp.route('/users/new', methods=['GET', 'POST'])
@login_required
def new_user():
    """Create a new user"""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        user = User()
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.password_hash = generate_password_hash(request.form.get('password'))
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        user.role = request.form.get('role')
        user.team_id = int(request.form.get('team_id')) if request.form.get('team_id') else None

        user.save()

        flash(f'User {user.username} created successfully', 'success')
        return redirect(url_for('admin.users'))

    teams = Team.get_all()
    return render_template('admin/new_user.html', teams=teams)


@admin_bp.route('/users/<int:user_id>/edit', methods=['POST'])
@login_required
def edit_user(user_id):
    """Edit a user"""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))

    user = User.get_by_id(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))

    user.first_name = request.form.get('first_name')
    user.last_name = request.form.get('last_name')
    user.phone = request.form.get('phone')
    user.role = request.form.get('role')
    user.team_id = int(request.form.get('team_id')) if request.form.get('team_id') else None

    if request.form.get('password'):
        user.password_hash = generate_password_hash(request.form.get('password'))

    user.save()
    flash(f'User {user.username} updated', 'success')
    return redirect(url_for('admin.users'))


@admin_bp.route('/users/<int:user_id>/delete', methods=['POST'])
@login_required
def delete_user(user_id):
    """Delete a user"""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))

    user = User.get_by_id(user_id)
    if not user:
        flash('User not found', 'danger')
        return redirect(url_for('admin.users'))

    username = user.username
    user.delete()

    flash(f'User {username} deleted', 'info')
    return redirect(url_for('admin.users'))


@admin_bp.route('/resources')
@login_required
def resources():
    """Manage resources"""
    if current_user.role != 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('main.index'))

    conn = db.get_connection()
    with conn.cursor(cursor_factory=db.get_cursor().__self__.__class__) as cur:
        from psycopg2.extras import RealDictCursor
        cur = conn.cursor(cursor_factory=RealDictCursor)
        cur.execute('SELECT * FROM resources ORDER BY name')
        resources = cur.fetchall()

    teams = Team.get_all()
    return render_template('admin/resources.html', resources=resources, teams=teams)


@admin_bp.route('/resources/new', methods=['POST'])
@login_required
def new_resource():
    """Create a new resource"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'})

    conn = db.get_connection()
    with conn.cursor() as cur:
        cur.execute('''
                    INSERT INTO resources (name, type, quantity, available, team_id, water_capacity)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    ''', (
                        request.form.get('name'),
                        request.form.get('type'),
                        int(request.form.get('quantity', 1)),
                        int(request.form.get('available', 1)),
                        int(request.form.get('team_id')) if request.form.get('team_id') else None,
                        float(request.form.get('water_capacity', 0)) if request.form.get('water_capacity') else None
                    ))
        db.commit()

    flash('Resource created successfully', 'success')
    return redirect(url_for('admin.resources'))


@admin_bp.route('/api/stats')
@login_required
def api_stats():
    """API endpoint for admin stats"""
    if current_user.role != 'admin':
        return jsonify({'success': False, 'error': 'Access denied'})

    conn = db.get_connection()
    with conn.cursor(cursor_factory=db.get_cursor().__self__.__class__) as cur:
        from psycopg2.extras import RealDictCursor
        cur = conn.cursor(cursor_factory=RealDictCursor)

        # User stats
        cur.execute('SELECT role, COUNT(*) as count FROM users GROUP BY role')
        users_by_role = {row['role']: row['count'] for row in cur.fetchall()}

        # Incident stats
        cur.execute('SELECT status, COUNT(*) as count FROM incidents GROUP BY status')
        incidents_by_status = {row['status']: row['count'] for row in cur.fetchall()}

        # Team stats
        cur.execute('SELECT status, COUNT(*) as count FROM teams GROUP BY status')
        teams_by_status = {row['status']: row['count'] for row in cur.fetchall()}

    return jsonify({
        'success': True,
        'stats': {
            'users': {
                'total': sum(users_by_role.values()),
                'by_role': users_by_role
            },
            'incidents': {
                'total': sum(incidents_by_status.values()),
                'by_status': incidents_by_status
            },
            'teams': {
                'total': sum(teams_by_status.values()),
                'by_status': teams_by_status
            }
        }
    })