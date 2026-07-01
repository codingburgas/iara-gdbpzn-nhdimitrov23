# run.py
import os
import sys
from dotenv import load_dotenv

# Add the current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Load environment variables
load_dotenv()

# Validate required environment variables
REQUIRED = ['SECRET_KEY', 'POSTGRES_HOST', 'POSTGRES_DB', 'POSTGRES_USER', 'POSTGRES_PASSWORD']
missing = [var for var in REQUIRED if not os.getenv(var)]

if missing:
    print(f"❌ ERROR: Missing required environment variables: {', '.join(missing)}")
    print("Please create a .env file with these variables set.")
    print("You can copy .env.example and fill in your values.")
    exit(1)

print("✅ All required environment variables are set.")

# Import app
from app import create_app, socketio
from app.init_db import init_database

app = create_app()

if __name__ == '__main__':
    # Initialize database
    with app.app_context():
        try:
            init_database()
            print("✅ Database initialized successfully")
        except Exception as e:
            print(f"❌ Database initialization failed: {e}")
            exit(1)

    debug = os.getenv('DEBUG', 'False').lower() == 'true'
    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', 5000))

    print(f"Server: http://localhost:{port}")
    print(f"Debug mode: {debug}")
    print(f"Admin: admin@gdpbzn.bg / admin123")


    # Run with socketio
    socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)