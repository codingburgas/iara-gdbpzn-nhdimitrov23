# GDPBZN Project
## About the project
The GDPBZN Information System is a comprehensive solution for managing operational activities of the Bulgarian fire department. The system provides real-time tools for:
- Incident registration and tracking
- GPS tracking of fire teams and vehicles
- Interactive operational map
- Communication center with chat
- Reports and analytics

## Technologies used
### Backend
- Python and flask - programming language and web framework
- PostgreSQL - database
- Docker - used to run the database
- Socket.IO - Real-time Communication
- Flask-Login - User authentication
- Flask-WTF - CSRF protection
### Frontend
- HTML + CSS - Structure and styling
- JavaScript - Dynamic functionality
- Leaflet.js - Interactive map

# Instalation
## Clone the repository
```
git clone https://github.com/codingburgas/iara-gdbpzn-nhdimitrov23.git
cd iara-gdbpzn-nhdimitrov23
```

## Create virtual enviroment
```
python -m venv .venv
source .venv/bin/activate # Linux/MacOS
.venv\Scripts\activate # Windows
```

## Install dependencies
```
pip install -r requirements.txt
```

## Configure the environment
rename .env.example as .env and enter your details
```
mv .env.example .env
```

## Start the database
```
docker-compose up
```

## Run the application
```
python run.py
```

## Default login credentials
```
Email: admin@gdpbzn.bg
Password: admin123
```