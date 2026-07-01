# app/__init__.py
from flask import Flask
from flask_login import LoginManager
from flask_socketio import SocketIO
from flask_cors import CORS
from flask_wtf.csrf import CSRFProtect
import os
from dotenv import load_dotenv
import logging
from logging.handlers import RotatingFileHandler

# Load environment variables FIRST
load_dotenv()

# Validate required environment variables
REQUIRED_ENV_VARS = [
    'SECRET_KEY',
    'POSTGRES_HOST',
    'POSTGRES_DB',
    'POSTGRES_USER',
    'POSTGRES_PASSWORD'
]

missing_vars = [var for var in REQUIRED_ENV_VARS if not os.getenv(var)]
if missing_vars:
    raise EnvironmentError(
        f"Missing required environment variables: {', '.join(missing_vars)}"
    )

# Initialize extensions
login_manager = LoginManager()
socketio = SocketIO()
csrf = CSRFProtect()


def create_app():
    app = Flask(__name__,
                static_folder='static',
                template_folder='templates')

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['UPLOAD_FOLDER'] = os.path.join('app', 'static', 'uploads')
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['WTF_CSRF_ENABLED'] = True
    app.config['WTF_CSRF_TIME_LIMIT'] = 3600  # 1 hour
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    # Initialize SocketIO with proper async mode
    # Try eventlet first, fallback to threading
    try:
        import eventlet
        socketio.init_app(app, cors_allowed_origins="*", async_mode='eventlet')
    except ImportError:
        try:
            import gevent
            socketio.init_app(app, cors_allowed_origins="*", async_mode='gevent')
        except ImportError:
            socketio.init_app(app, cors_allowed_origins="*", async_mode='threading')

    csrf.init_app(app)
    CORS(app, supports_credentials=True)

    from app.models import User

    @login_manager.user_loader
    def load_user(user_id):
        return User.get_by_id(int(user_id))

    from app.routes.auth import auth_bp
    from app.routes.incidents import incidents_bp
    from app.routes.teams import teams_bp
    from app.routes.map import map_bp
    from app.routes.communication import communication_bp
    from app.routes.admin import admin_bp
    from app.routes.main import main_bp
    from app.routes.api import api_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(incidents_bp, url_prefix='/incidents')
    app.register_blueprint(teams_bp, url_prefix='/teams')
    app.register_blueprint(map_bp, url_prefix='/map')
    app.register_blueprint(communication_bp, url_prefix='/communication')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp, url_prefix='/api')

    if not app.debug:
        if not os.path.exists('logs'):
            os.mkdir('logs')
        file_handler = RotatingFileHandler('logs/gdpbzn.log', maxBytes=10240, backupCount=10)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('GDPBZN application started')

    return app