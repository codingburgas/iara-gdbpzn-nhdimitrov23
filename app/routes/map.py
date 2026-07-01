from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from app.db import db
from app.models import Incident, Team
from datetime import datetime
import json
from psycopg2.extras import RealDictCursor

map_bp = Blueprint('map', __name__)


@map_bp.route('/')
@login_required
def index():
    """Operational map view"""
    return render_template('map/index.html')


@map_bp.route('/api/data')
@login_required
def api_data():
    """Get map data with all active units and incidents"""
    conn = db.get_connection()

    # Active incidents
    active_incidents = Incident.get_active()

    # Active teams - using proper cursor
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("SELECT * FROM teams WHERE status IN ('dispatched', 'on_site')")
        active_teams = cur.fetchall()

        cur.execute("SELECT * FROM teams WHERE status = 'available'")
        available_teams = cur.fetchall()

    return jsonify({
        'incidents': [{
            'id': i.id,
            'incident_number': i.incident_number,
            'type': i.type,
            'status': i.status,
            'address': i.address,
            'latitude': float(i.latitude) if i.latitude else None,
            'longitude': float(i.longitude) if i.longitude else None,
            'priority': i.priority,
            'fire_front': i.fire_front,
            'reported_at': i.reported_at.isoformat() if i.reported_at else None
        } for i in active_incidents],
        'active_teams': [{
            'id': t['id'],
            'name': t['name'],
            'status': t['status'],
            'latitude': float(t['latitude']) if t['latitude'] else None,
            'longitude': float(t['longitude']) if t['longitude'] else None,
            'current_incident_id': t['current_incident_id']
        } for t in active_teams],
        'available_teams': [{
            'id': t['id'],
            'name': t['name'],
            'latitude': float(t['latitude']) if t['latitude'] else None,
            'longitude': float(t['longitude']) if t['longitude'] else None,
            'station': t['station']
        } for t in available_teams]
    })


@map_bp.route('/api/incident/<int:incident_id>/fire-front', methods=['POST'])
@login_required
def update_fire_front(incident_id):
    """Update fire front polygon"""
    data = request.json
    incident = Incident.get_by_id(incident_id)
    if not incident:
        return jsonify({'success': False, 'error': 'Incident not found'})

    incident.fire_front = data.get('fire_front')
    incident.wind_direction = data.get('wind_direction')
    incident.wind_speed = data.get('wind_speed')
    incident.save()

    return jsonify({'success': True})


@map_bp.route('/api/incident/<int:incident_id>/location')
@login_required
def get_incident_location(incident_id):
    """Get incident location details"""
    incident = Incident.get_by_id(incident_id)
    if not incident:
        return jsonify({'error': 'Incident not found'}), 404

    return jsonify({
        'id': incident.id,
        'incident_number': incident.incident_number,
        'latitude': float(incident.latitude) if incident.latitude else None,
        'longitude': float(incident.longitude) if incident.longitude else None,
        'address': incident.address,
        'status': incident.status,
        'type': incident.type
    })