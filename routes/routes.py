from functools import wraps
from flask import Blueprint, render_template, redirect, url_for, session, flash, current_app

routes_bp = Blueprint('routes', __name__)


def _get_features() -> dict:
    try:
        from features.feature_flags import get_all_flags
        return get_all_flags()
    except Exception:
        return {}


def login_required(f):
    """Decorator to ensure the user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function


def safe_value(value):
    if value is None:
        return ''
    return value


def _normalize_user(user_info: dict) -> dict:
    """Apply all claim normalizations in one place."""
    u = {k: safe_value(v) for k, v in user_info.items()}
    u.setdefault('given_name',   u.get('username', u.get('firstname', u.get('first_name', u.get('name', 'User')))))
    u.setdefault('family_name',  u.get('lastname', u.get('last_name', '')))
    u.setdefault('email',        'No email provided')
    u.setdefault('sub',          'N/A')
    u.setdefault('roles',        u.get('groups', u.get('http://wso2.org/claims/role', '')))
    u.setdefault('phone_number', u.get('mobile', u.get('phone', u.get('http://wso2.org/claims/mobile', ''))))
    u.setdefault('picture',      '')
    return u


@routes_bp.route('/')
def index():
    return render_template('index.html')


@routes_bp.route('/user_home')
def user_home():
    user_info = session.get('user_info')
    if not user_info:
        flash('User is not logged in.')
        return redirect(url_for('routes.index'))

    u = _normalize_user(user_info)
    token_expiry = session.get('token_expiry', 0)

    return render_template(
        'user_dash.html',
        features=_get_features(),
        token_expiry=token_expiry,
        **u,
    )


@routes_bp.route('/user_profile')
def user_profile():
    user_info = session.get('user_info')
    if not user_info:
        flash('User is not logged in.')
        return redirect(url_for('routes.index'))

    u = _normalize_user(user_info)
    return render_template(
        'user_profile.html',
        features=_get_features(),
        token_expiry=session.get('token_expiry', 0),
        **u,
    )


@routes_bp.route('/logout', methods=['GET'])
def logout():
    idp = session.get('idp')
    if idp == 'google':
        return redirect(url_for('google.logout'))
    elif idp == 'wso2':
        return redirect(url_for('wso2.logout'))
    session.clear()
    current_app.logger.info("User logged out successfully (fallback).")
    return redirect(url_for('routes.index'))


# ── Error handlers ────────────────────────────────────────────────────────────
@routes_bp.app_errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@routes_bp.app_errorhandler(500)
def internal_server_error(error):
    return render_template('500.html'), 500


@routes_bp.app_errorhandler(403)
def forbidden_error(error):
    return render_template('403.html'), 403


@routes_bp.app_errorhandler(503)
def service_unavailable_error(error):
    return render_template('503.html'), 503
