from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import User
from . import db
from .email_utils import generate_verification_token, confirm_verification_token, send_verification_email

auth = Blueprint('auth', __name__)

@auth.route('/signup', methods=['GET', 'POST'])
def signup():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user:
            flash('Email already registered. Please log in.', 'error')
            return render_template('signup.html')

        # Create new user
        hashed_password = generate_password_hash(password, method='scrypt')
        new_user = User(email=email, password=hashed_password, is_verified=False)
        
        db.session.add(new_user)
        db.session.commit()

        # Send Resend verification email
        token = generate_verification_token(new_user.email)
        send_verification_email(new_user.email, token)

        flash('Account created! Check your email to verify your account.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('signup.html')

@auth.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('views.home'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            if not user.is_verified:
                flash('Please verify your email address before logging in.', 'error')
                return render_template('login.html')

            login_user(user, remember=True)
            return redirect(url_for('views.home'))
        else:
            flash('Invalid email or password.', 'error')

    return render_template('login.html')

@auth.route('/verify-email/<token>')
def verify_email(token):
    email = confirm_verification_token(token)
    if not email:
        flash('The verification link is invalid or has expired.', 'error')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first_or_404()
    if user.is_verified:
        flash('Account already verified. Please log in.', 'info')
    else:
        user.is_verified = True
        db.session.commit()
        flash('Your email has been verified! You can now log in.', 'success')

    return redirect(url_for('auth.login'))

@auth.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('auth.login'))