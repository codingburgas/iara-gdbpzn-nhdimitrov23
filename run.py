# run.py
import os
from dotenv import load_dotenv
from app import create_app
from app.init_db import init_database

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
    print(f"Starting GDPBZN application on http://localhost:5000")
    print(f"Debug mode: {debug}")
    print(f"Admin credentials: admin@gdpbzn.bg / admin123")

    app.run(host='0.0.0.0', port=5000, debug=debug)