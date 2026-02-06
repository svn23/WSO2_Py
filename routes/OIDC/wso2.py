import os
from flask import Blueprint, redirect, url_for, session, request, jsonify, render_template, flash, current_app
from dotenv import load_dotenv
import requests
import jwt
from functools import wraps

load_dotenv()

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

import time

# In-memory blacklist for Back-Channel Logout (Production should use Redis/DB)
# SID Blacklist: Invalidate specific sessions
BLACKLISTED_SIDS = set()
# User Revocation Times: sub -> timestamp (Global Logout with login loop protection)
USER_REVOCATION_TIMES = {}

# Helper to sanitize values for templates
def safe_value(value):
    if value is None:
        return ''
    return value

# Middleware to check for blacklisted sessions
@wso2_bp.before_request
def check_blacklist():
    # Check if Session ID is blacklisted
    if 'oidc_sid' in session:
        if session['oidc_sid'] in BLACKLISTED_SIDS:
            session.clear()
            flash('Your session has been terminated by the identity provider (SID match).', 'warning')
            return redirect(url_for('wso2.login'))
            
    # Check if User is globally revoked (Timestamp-based)
    if 'user_info' in session and 'sub' in session['user_info']:
        user_sub = session['user_info']['sub']
        
        # If user has a global revocation time
        if user_sub in USER_REVOCATION_TIMES:
            revocation_time = USER_REVOCATION_TIMES[user_sub]
            # Use 'auth_time' (Original Login Time) significantly better for SLO than 'iat'
            # Fallback to 'oidc_iat' if 'auth_time' is missing (but Keycloak usually sends it)
            session_time = session.get('oidc_auth_time', session.get('oidc_iat', 0))
            
            # If the original login happened BEFORE the revocation, we must kill it.
            # AND force a fresh login (prompt=login) to prevent silent SSO loops.
            if session_time < revocation_time:
                session.clear()
                flash('Your session has been terminated by the identity provider (Global Logout).', 'warning')
                # FORCE RE-AUTHENTICATION
                return redirect(url_for('wso2.login', force=True))

@wso2_bp.route('/login')
def login():
    force_login = request.args.get('force')
    
    auth_url = (
        f"{AUTHORIZATION_URI}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
    )
    
    # If forcing login, tell IdP to prompt for credentials
    if force_login:
        auth_url += "&prompt=login"
        
    print(f"Authorization URL: {auth_url}")
    return redirect(auth_url)

@wso2_bp.route('/dashboard')
def dashboard():
    user_info = session.get('user_info')
    if not user_info:
        flash('User is not logged in.')
        return redirect(url_for('wso2.login'))

    user_info = {key: safe_value(value) for key, value in user_info.items()}
    return render_template('dashboard.html', **user_info)

@wso2_bp.route('/user_home')
def user_home():
    user_info = session.get('user_info')
    if not user_info:
        flash('User is not logged in.')
        return redirect(url_for('wso2.login'))

    user_info = {key: safe_value(value) for key, value in user_info.items()}
    return render_template('user_dash.html', **user_info)

@wso2_bp.route('/user_profile')
def user_profile():
    user_info = session.get('user_info')
    if not user_info:
        flash('User is not logged in.')
        return redirect(url_for('wso2.login'))

    user_info = {key: safe_value(value) for key, value in user_info.items()}
    return render_template('user_profile.html', **user_info)

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
    
    try:
        # verify=False is for local testing with self-signed certs
        token_response = requests.post(TOKEN_URI, data=token_payload, verify=False)
        
        if token_response.status_code == 200:
            token_data = token_response.json()
            access_token = token_data.get('access_token')
            id_token = token_data.get('id_token')
            
            session['access_token'] = access_token
            session['id_token'] = id_token
            
            # Extract Session ID (sid) and Issued At (iat) from ID Token
            try:
                # Decode without verification just to get the 'sid' for session tracking
                decoded_id_token = jwt.decode(id_token, options={"verify_signature": False})
                session['oidc_sid'] = decoded_id_token.get('sid')
                session['oidc_iat'] = decoded_id_token.get('iat')
                session['oidc_auth_time'] = decoded_id_token.get('auth_time') # Critical for SLO
            except Exception as e:
                print(f"Error decoding ID token: {e}")

            # Fetch user information
            user_info_response = requests.get(
                USERINFO_URI,
                headers={'Authorization': f'Bearer {access_token}'},
                verify=False
            )

            if user_info_response.status_code == 200:
                user_info = user_info_response.json()
                session['user_info'] = user_info
                return redirect(url_for('wso2.user_home'))
            else:
                flash('Failed to fetch user details.')
        else:
            flash(f'Failed to obtain access token: {token_response.text}')
            
    except requests.RequestException as e:
        flash(f"Connection error: {e}")

    return redirect(url_for('wso2.login'))

@wso2_bp.route('/logout')
def logout():
    """
    Standard logout: Checks for ID token and redirects to IdP's logout endpoint (SLO).
    """
    id_token = session.get('id_token')
    
    # Store sid/sub locally before clearing, in case we want to blacklist our own session instantly
    # session.clear() removes it from cookie, but back-channel logic is separate.
    session.clear()

    if id_token:
        # Construct WSO2 logout URL
        logout_url = (
            f"{LOGOUT_URI}?"
            f"id_token_hint={id_token}&"
            f"post_logout_redirect_uri={url_for('routes.index', _external=True)}"
        )
        return redirect(logout_url)

    flash('You have been logged out successfully.')
    return redirect(url_for('routes.index'))

@wso2_bp.route('/frontchannel_logout', methods=['GET'])
def frontchannel_logout():
    """
    Handles Front-Channel Logout requests from the IdP.
    """
    session.clear()
    return "Local session cleared", 200

@wso2_bp.route('/backchannel_logout', methods=['POST'])
def backchannel_logout():
    """
    Handles Back-Channel Logout requests from the IdP.
    Received a Logout Token (JWT).
    """
    logout_token = request.form.get('logout_token')
    if logout_token:
        try:
            print(f"DEBUG: Received Back-Channel Logout Token: {logout_token[:20]}...")
            
            # In production, verify the signature!
            # decoded = jwt.decode(logout_token, public_key, algorithms=['RS256'], ...)
            decoded = jwt.decode(logout_token, options={"verify_signature": False})
            print(f"DEBUG: Decoded Token: {decoded}")
            
            sid = decoded.get('sid')
            sub = decoded.get('sub')
            
            if sid:
                BLACKLISTED_SIDS.add(sid)
                print(f"Back-Channel Logout: Blacklisted SID {sid}")
            
            if sub:
                # Use server time for revocation
                # Any session with iat < now will be invalid.
                USER_REVOCATION_TIMES[sub] = time.time()
                print(f"Back-Channel Logout: Revoked all sessions for User {sub} issued before {USER_REVOCATION_TIMES[sub]}")
            
        except Exception as e:
            print(f"Error processing logout token: {e}")
            return "Invalid token", 400

    return "Logout token received", 200
