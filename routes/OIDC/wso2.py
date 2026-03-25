import os
import time
import hashlib
import base64
import secrets as _secrets
from flask import Blueprint, redirect, url_for, session, request, jsonify, render_template, flash, current_app
from dotenv import load_dotenv
import requests
import jwt
from functools import wraps

load_dotenv()

wso2_bp = Blueprint('wso2', __name__)

# Configuration
AUTHORIZATION_URI = os.getenv('AUTHORIZATION_URI')
TOKEN_URI         = os.getenv('TOKEN_URI')
USERINFO_URI      = os.getenv('USERINFO_URI')
LOGOUT_URI        = os.getenv('LOGOUT_URI')
CLIENT_ID         = os.getenv('CLIENT_ID')
CLIENT_SECRET     = os.getenv('CLIENT_SECRET')
REDIRECT_URI      = os.getenv('REDIRECT_URI')
POST_LOGOUT_REDIRECT_URI = os.getenv('POST_LOGOUT_REDIRECT_URI')
SCOPES            = os.getenv('OIDC_SCOPES', 'openid email phone profile roles')

# In-memory blacklist for Back-Channel Logout (Production: use Redis/DB)
BLACKLISTED_SIDS     = set()
USER_REVOCATION_TIMES = {}


def safe_value(value):
    return '' if value is None else value


def _flag(key: str) -> bool:
    """Safe feature flag check — returns False if feature_flags unavailable."""
    try:
        from features.feature_flags import is_enabled
        return is_enabled(key)
    except Exception:
        return False


# ── Middleware ───────────────────────────────────────────────────────────────
@wso2_bp.before_request
def check_blacklist():
    if 'oidc_sid' in session:
        if session['oidc_sid'] in BLACKLISTED_SIDS:
            session.clear()
            flash('Your session has been terminated by the identity provider (SID).', 'warning')
            return redirect(url_for('wso2.login'))

    if 'user_info' in session and 'sub' in session['user_info']:
        user_sub = session['user_info']['sub']
        if user_sub in USER_REVOCATION_TIMES:
            revocation_time = USER_REVOCATION_TIMES[user_sub]
            session_time = session.get('oidc_auth_time', session.get('oidc_iat', 0))
            if session_time < revocation_time:
                session.clear()
                flash('Your session has been terminated by the identity provider (Global Logout).', 'warning')
                return redirect(url_for('wso2.login', force=True))


# ── Login ────────────────────────────────────────────────────────────────────
@wso2_bp.route('/login')
def login():
    if 'user_info' in session and not request.args.get('force'):
        return redirect(url_for('routes.user_home'))

    force_login = request.args.get('force')

    auth_url = (
        f"{AUTHORIZATION_URI}?response_type=code"
        f"&client_id={CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope={SCOPES}"
    )

    if force_login:
        auth_url += "&prompt=login"

    # ── PKCE ────────────────────────────────────────────────────────────────
    if _flag("pkce"):
        code_verifier  = _secrets.token_urlsafe(64)
        digest         = hashlib.sha256(code_verifier.encode()).digest()
        code_challenge = base64.urlsafe_b64encode(digest).rstrip(b'=').decode()
        session['pkce_code_verifier'] = code_verifier
        auth_url += f"&code_challenge={code_challenge}&code_challenge_method=S256"
        print("PKCE: code_challenge appended to auth URL.")

    print(f"Authorization URL: {auth_url}")
    return redirect(auth_url)


# ── Callback ─────────────────────────────────────────────────────────────────
@wso2_bp.route('/authorized')
def authorized():
    code = request.args.get('code')
    if not code:
        flash('Authorization code not found.')
        return redirect(url_for('wso2.login'))

    token_payload = {
        'grant_type':    'authorization_code',
        'code':          code,
        'redirect_uri':  REDIRECT_URI,
        'client_id':     CLIENT_ID,
        'client_secret': CLIENT_SECRET,
    }

    # ── PKCE — attach verifier ───────────────────────────────────────────────
    if _flag("pkce"):
        verifier = session.pop('pkce_code_verifier', None)
        if verifier:
            token_payload['code_verifier'] = verifier

    try:
        token_response = requests.post(TOKEN_URI, data=token_payload, verify=False)

        if token_response.status_code == 200:
            token_data   = token_response.json()
            access_token = token_data.get('access_token')
            id_token     = token_data.get('id_token')
            refresh_token = token_data.get('refresh_token')
            expires_in   = int(token_data.get('expires_in', 3600))

            session['access_token'] = access_token
            session['id_token']     = id_token
            session['idp']          = 'wso2'

            # Refresh token & expiry (always stored — timer/refresh features use them)
            if refresh_token:
                session['refresh_token'] = refresh_token
            session['token_expiry'] = time.time() + expires_in

            print("\n" + "=" * 50)
            print("WSO2 TOKEN EXCHANGE SUCCESSFUL")
            print(f"Access Token: {access_token}")
            print(f"ID Token:     {id_token}")
            print(f"Expires in:   {expires_in}s")
            print("=" * 50 + "\n")

            # Extract sid / iat / auth_time from ID Token
            try:
                decoded_id = jwt.decode(id_token, options={"verify_signature": False})
                session['oidc_sid']       = decoded_id.get('sid')
                session['oidc_iat']       = decoded_id.get('iat')
                session['oidc_auth_time'] = decoded_id.get('auth_time')
            except Exception as exc:
                print(f"Error decoding ID token: {exc}")

            # Fetch UserInfo
            user_info = {}
            user_info_resp = requests.get(
                USERINFO_URI,
                headers={'Authorization': f'Bearer {access_token}'},
                verify=False,
            )
            if user_info_resp.status_code == 200:
                user_info = user_info_resp.json()

            # Merge ID Token claims
            try:
                decoded_id = jwt.decode(id_token, options={"verify_signature": False})
                for k, v in decoded_id.items():
                    if k not in user_info:
                        user_info[k] = v
            except Exception as exc:
                print(f"Error merging ID token claims: {exc}")

            # Merge Access Token claims (if JWT)
            try:
                decoded_at = jwt.decode(access_token, options={"verify_signature": False})
                for k, v in decoded_at.items():
                    if k not in user_info:
                        user_info[k] = v
            except Exception:
                pass

            print("-" * 50)
            print("FINAL USERINFO (Merged):", user_info)
            print("-" * 50 + "\n")

            session['user_info'] = user_info

            # ── Audit: LOGIN event ───────────────────────────────────────────
            if _flag("audit_log"):
                try:
                    from features.audit import log_event
                    log_event("LOGIN", user_info)
                except Exception as exc:
                    print(f"Audit log error: {exc}")

            return redirect(url_for('routes.user_home'))
        else:
            flash(f'Failed to obtain access token: {token_response.text}')

    except requests.RequestException as exc:
        flash(f"Connection error: {exc}")

    return redirect(url_for('wso2.login'))


# ── Logout ───────────────────────────────────────────────────────────────────
@wso2_bp.route('/logout')
def logout():
    user_info = session.get('user_info', {})
    id_token  = session.get('id_token')
    session.clear()

    # ── Audit: LOGOUT event ─────────────────────────────────────────────────
    if _flag("audit_log"):
        try:
            from features.audit import log_event
            log_event("LOGOUT", user_info)
        except Exception as exc:
            print(f"Audit log error: {exc}")

    if id_token:
        post_logout_uri = POST_LOGOUT_REDIRECT_URI or url_for('routes.index', _external=True)
        logout_url = (
            f"{LOGOUT_URI}?"
            f"id_token_hint={id_token}&"
            f"post_logout_redirect_uri={post_logout_uri}"
        )
        return redirect(logout_url)

    flash('You have been logged out successfully.')
    return redirect(url_for('routes.index'))


# ── Front-Channel Logout ─────────────────────────────────────────────────────
@wso2_bp.route('/frontchannel_logout', methods=['GET'])
def frontchannel_logout():
    session.clear()
    return "Local session cleared", 200


# ── Back-Channel Logout ──────────────────────────────────────────────────────
@wso2_bp.route('/backchannel_logout', methods=['POST'])
def backchannel_logout():
    logout_token = request.form.get('logout_token')
    if logout_token:
        try:
            print(f"DEBUG: Back-Channel Logout Token received: {logout_token[:20]}...")
            decoded = jwt.decode(logout_token, options={"verify_signature": False})
            print(f"DEBUG: Decoded Token: {decoded}")

            sid = decoded.get('sid')
            sub = decoded.get('sub')

            if sid:
                BLACKLISTED_SIDS.add(sid)
                print(f"Back-Channel Logout: Blacklisted SID {sid}")

            if sub:
                USER_REVOCATION_TIMES[sub] = time.time()
                print(f"Back-Channel Logout: Revoked sessions for {sub}")

        except Exception as exc:
            print(f"Error processing logout token: {exc}")
            return "Invalid token", 400

    return "Logout token received", 200
