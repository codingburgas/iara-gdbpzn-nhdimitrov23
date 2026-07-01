from flask import Blueprint, render_template, request, flash, redirect, url_for, session, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from app.db import db
from app.models import User
from datetime import datetime
import re

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.get_by_email(email)

        if user and check_password_hash(user.password_hash, password):
            login_user(user)
            session['user_id'] = user.id
            session['user_email'] = user.email
            session['user_name'] = user.get_full_name()
            session['user_role'] = user.role

            # Update last login
            conn = db.get_connection()
            with conn.cursor() as cur:
                cur.execute('UPDATE users SET updated_at = CURRENT_TIMESTAMP WHERE id = %s', (user.id,))
                db.commit()

            if user.role == 'admin':
                return redirect(url_for('admin.dashboard'))
            elif user.role in ['admin', 'dispatcher']:
                return redirect(url_for('incidents.dashboard'))
            else:
                return redirect(url_for('main.index'))
        else:
            flash('Грешен имейл или парола', 'danger')

    return render_template('auth/login.html')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        email = request.form.get('email')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        phone = request.form.get('phone')

        # Validation
        if not all([email, username, password, confirm_password, first_name, last_name]):
            flash('Всички полета са задължителни', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Паролите не съвпадат', 'danger')
            return render_template('auth/register.html')

        if len(password) < 8:
            flash('Паролата трябва да бъде поне 8 символа', 'danger')
            return render_template('auth/register.html')

        # Validate email format
        if not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            flash('Невалиден имейл адрес', 'danger')
            return render_template('auth/register.html')

        # Check if user exists
        if User.get_by_email(email):
            flash('Този имейл вече е регистриран', 'danger')
            return render_template('auth/register.html')

        if User.get_by_username(username):
            flash('Това потребителско име вече е заето', 'danger')
            return render_template('auth/register.html')

        # Create user
        user = User()
        user.email = email
        user.username = username
        user.password_hash = generate_password_hash(password)
        user.first_name = first_name
        user.last_name = last_name
        user.phone = phone
        user.role = 'firefighter'
        user.team_id = None

        user.save()

        flash('Регистрацията е успешна! Моля, влезте.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Успешно излязохте от системата', 'info')
    return redirect(url_for('auth.login'))


@auth_bp.route('/profile')
@login_required
def profile():
    return render_template('auth/profile.html', user=current_user)


@auth_bp.route('/api/me')
@login_required
def api_me():
    return jsonify({
        'id': current_user.id,
        'username': current_user.username,
        'email': current_user.email,
        'full_name': current_user.get_full_name(),
        'role': current_user.role,
        'team_id': current_user.team_id
    })