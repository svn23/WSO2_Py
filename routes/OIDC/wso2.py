import os
from flask import Flask, Blueprint, redirect, url_for, session, request, jsonify, render_template, flash
from jinja2 import Undefined
from dotenv import load_dotenv
import requests
from jinja2 import Undefined
import json

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('APP_SECRET_KEY')

wso2_bp = Blueprint('wso2', __name__)

# Configuration
AUTHORIZATION_URI = os.getenv('AUTHORIZATION_URI')
TOKEN_URI = os.getenv('TOKEN_URI')
USERINFO_URI = os.getenv('USERINFO_URI')
LOGOUT_URI = os.getenv('LOGOUT_URI')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
REDIRECT_URI = os.getenv('REDIRECT_URI')
SCOPES = os.getenv('OIDC_SCOPES', 'openid email phone profile roles')

# Redirect user to WSO2 authorization endpoint
@wso2_bp.route('/login')
def login():
    auth_url = (
        f"{AUTHORIZATION_URI}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
    )
    return redirect(auth_url)


@wso2_bp.route('/dashboard')
def dashboard():
    # Fetch user info from session
    user_info = session.get('user_info')
    if not user_info:
        flash('User is not logged in.')
        return redirect(url_for('wso2.login'))

    # Ensure that all keys are present and no Undefined or None values exist
    def safe_value(value):
        # Check if the value is Undefined or None and return a safe value (empty string or None)
        if isinstance(value, Undefined):
            return ''
        return value if value is not None else ''

    # Apply safe_value to all user_info items
    user_info = {key: safe_value(value) for key, value in user_info.items()}

    # Pass the sanitized user_info to the template
    return render_template('dashboard.html', **user_info)

@wso2_bp.route('/user_home')
def user_home():
    # Fetch user info from session
    user_info = session.get('user_info')
    if not user_info:
        flash('User is not logged in.')
        return redirect(url_for('wso2.login'))

    # Ensure that all keys are present and no Undefined or None values exist
    def safe_value(value):
        if isinstance(value, Undefined):
            return ''
        return value if value is not None else ''

    # Apply safe_value to all user_info items
    user_info = {key: safe_value(value) for key, value in user_info.items()}

    # Pass the sanitized user_info to the template
    return render_template('user_dash.html', **user_info)

@wso2_bp.route('/user_profile')
def user_profile():
    # Fetch user info from session again if necessary
    user_info = session.get('user_info')
    if not user_info:
        flash('User is not logged in.')
        return redirect(url_for('wso2.login'))

    # Ensure all values are safe to pass into template
    def safe_value(value):
        if isinstance(value, Undefined):
            return ''
        return value if value is not None else ''

    # Apply safe_value to all user_info items
    user_info = {key: safe_value(value) for key, value in user_info.items()}

    # Render user profile page with sanitized data
    return render_template('user_profile.html', **user_info)

# Handle the callback from WSO2
@wso2_bp.route('/authorized')
def authorized():
    code = request.args.get('code')
    if not code:
        flash('Authorization code not found.')
        return redirect(url_for('wso2.login'))

    # Exchange the code for an access token
    token_payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': REDIRECT_URI,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }
    token_response = requests.post(TOKEN_URI, data=token_payload, verify=False)

    if token_response.status_code == 200:
        token_data = token_response.json()
        access_token = token_data.get('access_token')
        session['access_token'] = access_token
        session['id_token'] = token_data.get('id_token')

        # Fetch user information
        user_info_response = requests.get(
            USERINFO_URI,
            headers={'Authorization': f'Bearer {access_token}'},
            verify=False
        )

        if user_info_response.status_code == 200:
            user_info = user_info_response.json()


            # Store the user info in session
            session['user_info'] = user_info


            # Redirect to the user_home page
            return redirect(url_for('wso2.user_home'))

        else:
            flash('Failed to fetch user details.')
    else:
        flash('Failed to obtain access token.')

    return redirect(url_for('wso2.login'))



@wso2_bp.route('/logout')
def logout():
    id_token = session.get('id_token')

    # Clear the session
    session.clear()

    if id_token:
        logout_url = (
            f"{LOGOUT_URI}?"
            f"id_token_hint={id_token}&"
            f"post_logout_redirect_uri={url_for('wso2.login', _external=True)}&"
            f"client_id={CLIENT_ID}"
        )
        return redirect(logout_url)

    flash('You have been logged out successfully.')
    return redirect(url_for('wso2.login'))

# Register the blueprint
app.register_blueprint(wso2_bp, url_prefix='/OIDC/wso2')

if __name__ == "__main__":
    app.run(ssl_context='adhoc')  # Enable HTTPS for local testing
