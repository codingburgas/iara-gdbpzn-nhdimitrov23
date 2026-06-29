# app/routes/main.py
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Incident, Team

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Home page"""
    active_incidents = Incident.get_active()
    available_teams = Team.get_available()

    return render_template('index.html',
                           active_incidents=active_incidents,
                           available_teams=available_teams,
                           active_count=len(active_incidents),
                           available_count=len(available_teams))


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """User dashboard"""
    return render_template('dashboard.html', user=current_user)