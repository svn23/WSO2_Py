import os
from flask import Blueprint, redirect, url_for, session, request, jsonify, render_template, flash
from dotenv import load_dotenv
import requests
import jwt
from functools import wraps

load_dotenv()

google_bp = Blueprint('google', __name__)

# Configuration
GOOGLE_CLIENT_ID = os.getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = os.getenv('GOOGLE_CLIENT_SECRET')
GOOGLE_REDIRECT_URI = os.getenv('GOOGLE_REDIRECT_URI')
GOOGLE_DISCOVERY_URL = os.getenv('GOOGLE_DISCOVERY_URL')
GOOGLE_SCOPES = os.getenv('GOOGLE_SCOPES', 'openid email profile')

def get_google_config():
    """Fetch Google's OIDC configuration from the discovery URL."""
    return requests.get(GOOGLE_DISCOVERY_URL).json()

@google_bp.route('/login')
def login():
    # Check if user is already logged in
    if 'user_info' in session:
        return redirect(url_for('routes.user_home'))

    google_config = get_google_config()
    authorization_endpoint = google_config.get('authorization_endpoint')
    
    # Strip any extra spaces from scopes
    scopes = GOOGLE_SCOPES.strip() if GOOGLE_SCOPES else 'openid email profile'
    
    auth_url = (
        f"{authorization_endpoint}?response_type=code"
        f"&client_id={GOOGLE_CLIENT_ID}"
        f"&redirect_uri={GOOGLE_REDIRECT_URI}"
        f"&scope={scopes}"
        f"&access_type=offline"
    )
    
    print(f"Google Authorization URL: {auth_url}")
    return redirect(auth_url)

@google_bp.route('/authorized')
def authorized():
    code = request.args.get('code')
    if not code:
        flash('Authorization code not found.')
        return redirect(url_for('routes.login'))

    google_config = get_google_config()
    token_endpoint = google_config.get('token_endpoint')
    userinfo_endpoint = google_config.get('userinfo_endpoint')

    # Exchange the code for an access token
    token_payload = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': GOOGLE_REDIRECT_URI,
    }
    
    try:
        # Use HTTP Basic Auth for cleaner credential passing (supported by Google)
        token_response = requests.post(
            token_endpoint, 
            data=token_payload, 
            auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET)
        )
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            id_token = token_data.get('id_token')
            
            session['access_token'] = access_token
            session['id_token'] = id_token
            session['idp'] = 'google'
            
            # Fetch user information
            user_info_response = requests.get(
                userinfo_endpoint,
                headers={'Authorization': f'Bearer {access_token}'}
            )

            if user_info_response.status_code == 200:
                user_info = user_info_response.json()
                session['user_info'] = user_info
                return redirect(url_for('routes.user_home')) # Use the same unified dashboard
            else:
                flash('Failed to fetch user details from Google.')
        else:
            print("\n" + "!"*50)
            print("GOOGLE TOKEN EXCHANGE FAILED")
            print(f"Status Code: {token_response.status_code}")
            print(f"Response Body: {token_response.text}")
            print("!"*50 + "\n")
            flash(f'Failed to obtain access token from Google: {token_response.text}')
            
    except requests.RequestException as e:
        print(f"\nGOOGLE REQUEST ERROR: {e}\n")
        flash(f"Connection error to Google IDP: {e}")

    return redirect(url_for('routes.index'))

@google_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out from Google SSO locally.')
    return redirect(url_for('routes.index'))
