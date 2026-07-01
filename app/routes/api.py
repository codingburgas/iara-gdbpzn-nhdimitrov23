from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from app.db import db
from app.models import Incident, Team
from psycopg2.extras import RealDictCursor

api_bp = Blueprint('api', __name__)


@api_bp.route('/incidents/nearby')
@login_required
def nearby_incidents():
    """Get incidents near a location"""
    lat = request.args.get('lat', type=float)
    lng = request.args.get('lng', type=float)
    radius = request.args.get('radius', 10, type=float)  # km

    if not lat or not lng:
        return jsonify({'error': 'Latitude and longitude required'}), 400

    conn = db.get_connection()
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute("""
                    SELECT *,
                           (6371 * acos(cos(radians(%s)) * cos(radians(latitude)) *
                                        cos(radians(longitude) - radians(%s)) +
                                        sin(radians(%s)) * sin(radians(latitude)))) AS distance
                    FROM incidents
                    WHERE status IN ('reported', 'dispatched', 'on_site', 'in_progress')
                      AND latitude IS NOT NULL
                      AND longitude IS NOT NULL
                    HAVING distance < %s
                    ORDER BY distance
                    """, (lat, lng, lat, radius))

        incidents = cur.fetchall()

    return jsonify([{
        'id': i['id'],
        'incident_number': i['incident_number'],
        'type': i['type'],
        'status': i['status'],
        'address': i['address'],
        'latitude': float(i['latitude']),
        'longitude': float(i['longitude']),
        'priority': i['priority'],
        'distance': round(float(i['distance']), 2) if i['distance'] else None
    } for i in incidents])


@api_bp.route('/geocode', methods=['POST'])
@login_required
def geocode():
    """Geocode an address to coordinates"""
    data = request.json
    address = data.get('address')

    if not address:
        return jsonify({'error': 'Address required'}), 400

    # Use a geocoding service or simple lookup
    # For now, return a mock response
    # In production, use OpenStreetMap Nominatim or Google Maps API
    return jsonify({
        'address': address,
        'latitude': 42.6977,
        'longitude': 23.3219,
        'formatted': address
    })