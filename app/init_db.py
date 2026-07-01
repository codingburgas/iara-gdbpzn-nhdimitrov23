from app.db import db
from werkzeug.security import generate_password_hash
import logging


def init_database():
    """Initialize database tables and default data"""
    conn = db.get_connection()

    try:
        with conn.cursor() as cur:
            # Users table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    email VARCHAR(255) UNIQUE NOT NULL,
                    username VARCHAR(80) UNIQUE NOT NULL,
                    password_hash VARCHAR(200) NOT NULL,
                    first_name VARCHAR(80) NOT NULL,
                    last_name VARCHAR(80) NOT NULL,
                    phone VARCHAR(20),
                    role VARCHAR(50) DEFAULT 'firefighter',
                    team_id INTEGER,
                    is_available BOOLEAN DEFAULT TRUE,
                    is_on_leave BOOLEAN DEFAULT FALSE,
                    leave_start TIMESTAMP,
                    leave_end TIMESTAMP,
                    last_latitude DECIMAL(10, 8),
                    last_longitude DECIMAL(11, 8),
                    last_location_update TIMESTAMP,
                    fcm_token VARCHAR(255),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Teams table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS teams (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    code VARCHAR(20) UNIQUE NOT NULL,
                    station VARCHAR(100),
                    vehicle_type VARCHAR(50),
                    vehicle_registration VARCHAR(20),
                    status VARCHAR(50) DEFAULT 'available',
                    current_incident_id INTEGER,
                    latitude DECIMAL(10, 8),
                    longitude DECIMAL(11, 8),
                    last_location_update TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Incidents table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS incidents (
                    id SERIAL PRIMARY KEY,
                    incident_number VARCHAR(20) UNIQUE NOT NULL,
                    type VARCHAR(50) NOT NULL,
                    status VARCHAR(50) DEFAULT 'reported',
                    priority INTEGER DEFAULT 1,
                    address VARCHAR(255) NOT NULL,
                    latitude DECIMAL(10, 8) NOT NULL,
                    longitude DECIMAL(11, 8) NOT NULL,
                    description TEXT,
                    hazardous_materials TEXT,
                    action_plan TEXT,
                    reporter_name VARCHAR(100),
                    reporter_phone VARCHAR(20),
                    dispatcher_id INTEGER,
                    dispatched_at TIMESTAMP,
                    fire_front JSON,
                    wind_direction VARCHAR(50),
                    wind_speed DECIMAL(5, 2),
                    reported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    resolved_at TIMESTAMP,
                    closed_at TIMESTAMP
                )
            ''')

            # Incident assignments table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS incident_assignments (
                    id SERIAL PRIMARY KEY,
                    incident_id INTEGER NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    task VARCHAR(255),
                    status VARCHAR(50) DEFAULT 'assigned',
                    resources_used JSON,
                    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP
                )
            ''')

            # Communications table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS communications (
                    id SERIAL PRIMARY KEY,
                    incident_id INTEGER REFERENCES incidents(id) ON DELETE CASCADE,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    message_type VARCHAR(50) DEFAULT 'text',
                    content TEXT,
                    media_url VARCHAR(500),
                    thumbnail_url VARCHAR(500),
                    latitude DECIMAL(10, 8),
                    longitude DECIMAL(11, 8),
                    is_read BOOLEAN DEFAULT FALSE,
                    read_at TIMESTAMP,
                    is_template BOOLEAN DEFAULT FALSE,
                    template_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Message templates table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS message_templates (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    category VARCHAR(50),
                    content TEXT NOT NULL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Resources table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS resources (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    type VARCHAR(50),
                    quantity INTEGER DEFAULT 1,
                    available INTEGER DEFAULT 1,
                    team_id INTEGER REFERENCES teams(id) ON DELETE SET NULL,
                    water_capacity DECIMAL(10, 2),
                    current_water DECIMAL(10, 2),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Notifications table
            cur.execute('''
                CREATE TABLE IF NOT EXISTS notifications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title VARCHAR(255) NOT NULL,
                    message TEXT NOT NULL,
                    type VARCHAR(50),
                    is_read BOOLEAN DEFAULT FALSE,
                    incident_id INTEGER REFERENCES incidents(id) ON DELETE SET NULL,
                    data JSON,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    read_at TIMESTAMP
                )
            ''')

            # Create admin user if not exists
            admin_password = generate_password_hash('admin123')
            cur.execute('SELECT id FROM users WHERE username = %s', ('admin',))
            if not cur.fetchone():
                cur.execute('''
                    INSERT INTO users (email, username, password_hash, first_name, last_name, role)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', ('admin@gdpbzn.bg', 'admin', admin_password, 'System', 'Administrator', 'admin'))
                logging.info("✅ Admin user created: admin@gdpbzn.bg / admin123")

            # Create sample team
            cur.execute('SELECT id FROM teams WHERE code = %s', ('FD001',))
            if not cur.fetchone():
                cur.execute('''
                    INSERT INTO teams (name, code, station, vehicle_type, vehicle_registration, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', ('Пожарна София Център', 'FD001', 'София, ул. Опълченска 1', 'Пожарен автомобил',
                      'СА 1234 АА', 'available'))
                logging.info("✅ Sample team created: FD001")

            # Create additional sample teams
            cur.execute('SELECT id FROM teams WHERE code = %s', ('FD002',))
            if not cur.fetchone():
                cur.execute('''
                    INSERT INTO teams (name, code, station, vehicle_type, vehicle_registration, status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                ''', ('Пожарна София Запад', 'FD002', 'София, ул. Ботевградско шосе 1', 'Пожарен автомобил',
                      'СА 5678 ВВ', 'available'))
                logging.info("✅ Sample team created: FD002")

            conn.commit()
            logging.info("✅ Database tables initialized successfully")

    except Exception as e:
        logging.error(f"❌ Error initializing database: {e}")
        conn.rollback()
        raise