# app/models.py
from flask_login import UserMixin
from app.db import db
from datetime import datetime
import json
import uuid
from psycopg2.extras import RealDictCursor


# app/models.py - Fixed User class

class User(UserMixin):
    """User model using direct database access"""

    def __init__(self, data=None):
        # Initialize all attributes with defaults FIRST
        self.id = None
        self.email = None
        self.username = None
        self.password_hash = None
        self.first_name = None
        self.last_name = None
        self.phone = None
        self.role = 'firefighter'
        self.team_id = None
        self.is_available = True
        self.is_on_leave = False
        self.leave_start = None
        self.leave_end = None
        self.last_latitude = None
        self.last_longitude = None
        self.fcm_token = None
        self.created_at = None
        self.updated_at = None

        # Then override with data if provided
        if data:
            self.id = data.get('id')
            self.email = data.get('email')
            self.username = data.get('username')
            self.password_hash = data.get('password_hash')
            self.first_name = data.get('first_name')
            self.last_name = data.get('last_name')
            self.phone = data.get('phone')
            self.role = data.get('role', 'firefighter')
            self.team_id = data.get('team_id')
            self.is_available = data.get('is_available', True)
            self.is_on_leave = data.get('is_on_leave', False)
            self.leave_start = data.get('leave_start')
            self.leave_end = data.get('leave_end')
            self.last_latitude = data.get('last_latitude')
            self.last_longitude = data.get('last_longitude')
            self.fcm_token = data.get('fcm_token')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def is_admin(self):
        return self.role == 'admin'

    def is_dispatcher(self):
        return self.role in ['admin', 'dispatcher']

    @classmethod
    def get_by_id(cls, user_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE id = %s', (user_id,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_by_email(cls, email):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE email = %s', (email,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_by_username(cls, username):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE username = %s', (username,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_all(cls):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM users ORDER BY created_at DESC')
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_by_team(cls, team_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE team_id = %s', (team_id,))
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_available(cls):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM users WHERE is_available = true AND is_on_leave = false')
            return [cls(row) for row in cur.fetchall()]

    def save(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            if self.id:  # Now self.id always exists (even if None)
                cur.execute('''
                            UPDATE users
                            SET email          = %s,
                                username       = %s,
                                first_name     = %s,
                                last_name      = %s,
                                phone          = %s,
                                role           = %s,
                                team_id        = %s,
                                is_available   = %s,
                                is_on_leave    = %s,
                                leave_start    = %s,
                                leave_end      = %s,
                                last_latitude  = %s,
                                last_longitude = %s,
                                fcm_token      = %s,
                                updated_at     = CURRENT_TIMESTAMP
                            WHERE id = %s
                            ''', (
                                self.email, self.username, self.first_name, self.last_name,
                                self.phone, self.role, self.team_id, self.is_available,
                                self.is_on_leave, self.leave_start, self.leave_end,
                                self.last_latitude, self.last_longitude, self.fcm_token,
                                self.id
                            ))
            else:
                cur.execute('''
                            INSERT INTO users
                            (email, username, password_hash, first_name, last_name, phone, role, team_id)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id
                            ''', (
                                self.email, self.username, self.password_hash,
                                self.first_name, self.last_name, self.phone,
                                self.role, self.team_id
                            ))
                self.id = cur.fetchone()[0]
            db.commit()
        return self.id

    def delete(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM users WHERE id = %s', (self.id,))
            db.commit()

    def update_location(self, latitude, longitude):
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute('''
                        UPDATE users
                        SET last_latitude        = %s,
                            last_longitude       = %s,
                            last_location_update = CURRENT_TIMESTAMP
                        WHERE id = %s
                        ''', (latitude, longitude, self.id))
            db.commit()
            self.last_latitude = latitude
            self.last_longitude = longitude


class Team:
    """Team model using direct database access"""

    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.name = data.get('name')
            self.code = data.get('code')
            self.station = data.get('station')
            self.vehicle_type = data.get('vehicle_type')
            self.vehicle_registration = data.get('vehicle_registration')
            self.status = data.get('status', 'available')
            self.current_incident_id = data.get('current_incident_id')
            self.latitude = data.get('latitude')
            self.longitude = data.get('longitude')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')

    @classmethod
    def get_by_id(cls, team_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM teams WHERE id = %s', (team_id,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_by_code(cls, code):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM teams WHERE code = %s', (code,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_all(cls):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM teams ORDER BY name')
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_available(cls):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM teams WHERE status = 'available'")
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_active(cls):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM teams WHERE status IN ('dispatched', 'on_site')")
            return [cls(row) for row in cur.fetchall()]

    def save(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            if self.id:
                cur.execute('''
                    UPDATE teams SET 
                        name = %s, code = %s, station = %s,
                        vehicle_type = %s, vehicle_registration = %s,
                        status = %s, current_incident_id = %s,
                        latitude = %s, longitude = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (
                    self.name, self.code, self.station,
                    self.vehicle_type, self.vehicle_registration,
                    self.status, self.current_incident_id,
                    self.latitude, self.longitude,
                    self.id
                ))
            else:
                cur.execute('''
                    INSERT INTO teams 
                    (name, code, station, vehicle_type, vehicle_registration)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    self.name, self.code, self.station,
                    self.vehicle_type, self.vehicle_registration
                ))
                self.id = cur.fetchone()[0]
            db.commit()
        return self.id

    def update_location(self, latitude, longitude):
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE teams 
                SET latitude = %s, longitude = %s, last_location_update = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (latitude, longitude, self.id))
            db.commit()
            self.latitude = latitude
            self.longitude = longitude

    def get_members(self):
        return User.get_by_team(self.id)

    def delete(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM teams WHERE id = %s', (self.id,))
            db.commit()


class Incident:
    """Incident model using direct database access"""

    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.incident_number = data.get('incident_number')
            self.type = data.get('type')
            self.status = data.get('status', 'reported')
            self.priority = data.get('priority', 1)
            self.address = data.get('address')
            self.latitude = data.get('latitude')
            self.longitude = data.get('longitude')
            self.description = data.get('description')
            self.hazardous_materials = data.get('hazardous_materials')
            self.action_plan = data.get('action_plan')
            self.reporter_name = data.get('reporter_name')
            self.reporter_phone = data.get('reporter_phone')
            self.dispatcher_id = data.get('dispatcher_id')
            self.dispatched_at = data.get('dispatched_at')
            self.fire_front = data.get('fire_front')
            self.wind_direction = data.get('wind_direction')
            self.wind_speed = data.get('wind_speed')
            self.reported_at = data.get('reported_at')
            self.resolved_at = data.get('resolved_at')
            self.closed_at = data.get('closed_at')

    @classmethod
    def get_by_id(cls, incident_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM incidents WHERE id = %s', (incident_id,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_by_number(cls, incident_number):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM incidents WHERE incident_number = %s', (incident_number,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_active(cls):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM incidents 
                WHERE status IN ('reported', 'dispatched', 'on_site', 'in_progress', 'contained')
                ORDER BY priority DESC, reported_at DESC
            """)
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_all(cls, limit=100):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM incidents ORDER BY reported_at DESC LIMIT %s', (limit,))
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_recent(cls, days=7):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("""
                SELECT * FROM incidents 
                WHERE reported_at >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                ORDER BY reported_at DESC
            """, (days,))
            return [cls(row) for row in cur.fetchall()]

    def save(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            if self.id:
                cur.execute('''
                    UPDATE incidents SET 
                        type = %s, status = %s, priority = %s,
                        address = %s, latitude = %s, longitude = %s,
                        description = %s, hazardous_materials = %s,
                        action_plan = %s, reporter_name = %s,
                        reporter_phone = %s, dispatcher_id = %s,
                        dispatched_at = %s, fire_front = %s,
                        wind_direction = %s, wind_speed = %s,
                        resolved_at = %s, closed_at = %s
                    WHERE id = %s
                ''', (
                    self.type, self.status, self.priority,
                    self.address, self.latitude, self.longitude,
                    self.description, self.hazardous_materials,
                    self.action_plan, self.reporter_name,
                    self.reporter_phone, self.dispatcher_id,
                    self.dispatched_at,
                    json.dumps(self.fire_front) if self.fire_front else None,
                    self.wind_direction, self.wind_speed,
                    self.resolved_at, self.closed_at,
                    self.id
                ))
            else:
                # Generate incident number
                incident_number = f"INC-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

                cur.execute('''
                    INSERT INTO incidents 
                    (incident_number, type, status, priority, address, latitude, longitude,
                     description, hazardous_materials, action_plan, reporter_name,
                     reporter_phone, dispatcher_id, dispatched_at)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    incident_number, self.type, self.status, self.priority,
                    self.address, self.latitude, self.longitude,
                    self.description, self.hazardous_materials,
                    self.action_plan, self.reporter_name,
                    self.reporter_phone, self.dispatcher_id,
                    self.dispatched_at
                ))
                self.id = cur.fetchone()[0]
                self.incident_number = incident_number
            db.commit()
        return self.id

    def get_assignments(self):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT a.*, u.first_name, u.last_name, u.email 
                FROM incident_assignments a
                JOIN users u ON a.user_id = u.id
                WHERE a.incident_id = %s
                ORDER BY a.assigned_at DESC
            ''', (self.id,))
            return cur.fetchall()

    def get_communications(self, limit=50):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT c.*, u.first_name, u.last_name 
                FROM communications c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.incident_id = %s
                ORDER BY c.created_at DESC
                LIMIT %s
            ''', (self.id, limit))
            return cur.fetchall()

    def delete(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute('DELETE FROM incidents WHERE id = %s', (self.id,))
            db.commit()


class IncidentAssignment:
    """Incident Assignment model"""

    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.incident_id = data.get('incident_id')
            self.user_id = data.get('user_id')
            self.task = data.get('task')
            self.status = data.get('status', 'assigned')
            self.resources_used = data.get('resources_used')
            self.assigned_at = data.get('assigned_at')
            self.started_at = data.get('started_at')
            self.completed_at = data.get('completed_at')

    @classmethod
    def get_by_id(cls, assignment_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM incident_assignments WHERE id = %s', (assignment_id,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_by_incident(cls, incident_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM incident_assignments WHERE incident_id = %s', (incident_id,))
            return [cls(row) for row in cur.fetchall()]

    def save(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            if self.id:
                cur.execute('''
                    UPDATE incident_assignments SET
                        task = %s, status = %s, resources_used = %s,
                        started_at = %s, completed_at = %s
                    WHERE id = %s
                ''', (self.task, self.status,
                      json.dumps(self.resources_used) if self.resources_used else None,
                      self.started_at, self.completed_at, self.id))
            else:
                cur.execute('''
                    INSERT INTO incident_assignments 
                    (incident_id, user_id, task, status, resources_used)
                    VALUES (%s, %s, %s, %s, %s)
                    RETURNING id
                ''', (self.incident_id, self.user_id, self.task, self.status,
                      json.dumps(self.resources_used) if self.resources_used else None))
                self.id = cur.fetchone()[0]
            db.commit()
        return self.id


class Communication:
    """Communication model"""

    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.incident_id = data.get('incident_id')
            self.user_id = data.get('user_id')
            self.message_type = data.get('message_type', 'text')
            self.content = data.get('content')
            self.media_url = data.get('media_url')
            self.thumbnail_url = data.get('thumbnail_url')
            self.latitude = data.get('latitude')
            self.longitude = data.get('longitude')
            self.is_read = data.get('is_read', False)
            self.is_template = data.get('is_template', False)
            self.template_id = data.get('template_id')
            self.created_at = data.get('created_at')

    @classmethod
    def get_by_id(cls, comm_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM communications WHERE id = %s', (comm_id,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_by_incident(cls, incident_id, limit=50):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT c.*, u.first_name, u.last_name 
                FROM communications c
                LEFT JOIN users u ON c.user_id = u.id
                WHERE c.incident_id = %s
                ORDER BY c.created_at DESC
                LIMIT %s
            ''', (incident_id, limit))
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_recent(cls, limit=50):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT c.*, u.first_name, u.last_name 
                FROM communications c
                LEFT JOIN users u ON c.user_id = u.id
                ORDER BY c.created_at DESC
                LIMIT %s
            ''', (limit,))
            return [cls(row) for row in cur.fetchall()]

    def save(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            if self.id:
                cur.execute('''
                    UPDATE communications SET
                        content = %s, is_read = %s, read_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (self.content, self.is_read, self.id))
            else:
                cur.execute('''
                    INSERT INTO communications 
                    (incident_id, user_id, message_type, content, media_url, thumbnail_url,
                     latitude, longitude, is_template, template_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (
                    self.incident_id, self.user_id, self.message_type,
                    self.content, self.media_url, self.thumbnail_url,
                    self.latitude, self.longitude,
                    self.is_template, self.template_id
                ))
                self.id = cur.fetchone()[0]
            db.commit()
        return self.id

    def mark_read(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE communications 
                SET is_read = true, read_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (self.id,))
            db.commit()
            self.is_read = True


class MessageTemplate:
    """Message Template model"""

    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.name = data.get('name')
            self.category = data.get('category')
            self.content = data.get('content')
            self.is_active = data.get('is_active', True)
            self.created_by = data.get('created_by')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')

    @classmethod
    def get_by_id(cls, template_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM message_templates WHERE id = %s', (template_id,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_all(cls, active_only=True):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            if active_only:
                cur.execute("SELECT * FROM message_templates WHERE is_active = true ORDER BY name")
            else:
                cur.execute("SELECT * FROM message_templates ORDER BY name")
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_by_category(cls, category):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM message_templates WHERE category = %s AND is_active = true", (category,))
            return [cls(row) for row in cur.fetchall()]

    def save(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            if self.id:
                cur.execute('''
                    UPDATE message_templates SET
                        name = %s, category = %s, content = %s,
                        is_active = %s, updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (self.name, self.category, self.content, self.is_active, self.id))
            else:
                cur.execute('''
                    INSERT INTO message_templates (name, category, content, created_by)
                    VALUES (%s, %s, %s, %s)
                    RETURNING id
                ''', (self.name, self.category, self.content, self.created_by))
                self.id = cur.fetchone()[0]
            db.commit()
        return self.id


class Resource:
    """Resource model"""

    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.name = data.get('name')
            self.type = data.get('type')
            self.quantity = data.get('quantity', 1)
            self.available = data.get('available', 1)
            self.team_id = data.get('team_id')
            self.water_capacity = data.get('water_capacity')
            self.current_water = data.get('current_water')
            self.created_at = data.get('created_at')
            self.updated_at = data.get('updated_at')

    @classmethod
    def get_by_id(cls, resource_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM resources WHERE id = %s', (resource_id,))
            data = cur.fetchone()
            if data:
                return cls(data)
        return None

    @classmethod
    def get_all(cls):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM resources ORDER BY name')
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_by_team(cls, team_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('SELECT * FROM resources WHERE team_id = %s', (team_id,))
            return [cls(row) for row in cur.fetchall()]

    def save(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            if self.id:
                cur.execute('''
                    UPDATE resources SET
                        name = %s, type = %s, quantity = %s, available = %s,
                        team_id = %s, water_capacity = %s, current_water = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (self.name, self.type, self.quantity, self.available,
                      self.team_id, self.water_capacity, self.current_water, self.id))
            else:
                cur.execute('''
                    INSERT INTO resources 
                    (name, type, quantity, available, team_id, water_capacity, current_water)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (self.name, self.type, self.quantity, self.available,
                      self.team_id, self.water_capacity, self.current_water))
                self.id = cur.fetchone()[0]
            db.commit()
        return self.id


class Notification:
    """Notification model"""

    def __init__(self, data=None):
        if data:
            self.id = data.get('id')
            self.user_id = data.get('user_id')
            self.title = data.get('title')
            self.message = data.get('message')
            self.type = data.get('type')
            self.is_read = data.get('is_read', False)
            self.incident_id = data.get('incident_id')
            self.data = data.get('data')
            self.created_at = data.get('created_at')
            self.read_at = data.get('read_at')

    @classmethod
    def get_by_user(cls, user_id, limit=50):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM notifications 
                WHERE user_id = %s 
                ORDER BY created_at DESC 
                LIMIT %s
            ''', (user_id, limit))
            return [cls(row) for row in cur.fetchall()]

    @classmethod
    def get_unread(cls, user_id):
        conn = db.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute('''
                SELECT * FROM notifications 
                WHERE user_id = %s AND is_read = false 
                ORDER BY created_at DESC
            ''', (user_id,))
            return [cls(row) for row in cur.fetchall()]

    def save(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            if self.id:
                cur.execute('''
                    UPDATE notifications SET
                        is_read = %s, read_at = CURRENT_TIMESTAMP
                    WHERE id = %s
                ''', (self.is_read, self.id))
            else:
                cur.execute('''
                    INSERT INTO notifications 
                    (user_id, title, message, type, incident_id, data)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING id
                ''', (self.user_id, self.title, self.message, self.type,
                      self.incident_id, json.dumps(self.data) if self.data else None))
                self.id = cur.fetchone()[0]
            db.commit()
        return self.id

    def mark_read(self):
        conn = db.get_connection()
        with conn.cursor() as cur:
            cur.execute('''
                UPDATE notifications 
                SET is_read = true, read_at = CURRENT_TIMESTAMP
                WHERE id = %s
            ''', (self.id,))
            db.commit()
            self.is_read = True