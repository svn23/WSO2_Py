import os
from flask import Flask, Blueprint, redirect, url_for, session, request, jsonify, render_template, flash
from dotenv import load_dotenv
import requests

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

            # Pass this info to the template
            # return render_template('dashboard.html', userInfo=user_info, phone_number=phone_number, roles=roles)
            return render_template('dashboard.html', **user_info, user_info=user_info)
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
