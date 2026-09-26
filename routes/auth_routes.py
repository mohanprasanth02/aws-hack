from flask import Blueprint, redirect, url_for, request
from flask_login import login_user, logout_user, current_user
from models import db, User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    return redirect(url_for('main.dashboard'))

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            login_user(user)
    return redirect(url_for('main.dashboard'))

@auth_bp.route('/logout')
def logout():
    return redirect(url_for('main.dashboard'))
