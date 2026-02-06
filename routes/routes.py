from flask import Blueprint, render_template, redirect, url_for, session, flash, current_app

routes_bp = Blueprint('routes', __name__)

def login_required(f):
    """Decorator to ensure the user is logged in."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_email' not in session:
            return redirect(url_for('routes.login'))
        return f(*args, **kwargs)
    return decorated_function

@routes_bp.route('/')
def index():
    return render_template('index.html')

@routes_bp.route('/logout', methods=['GET'])
def logout():
    try:
        session.clear()
        current_app.logger.info("User logged out successfully.")
        return redirect(url_for('routes.login'))
    except Exception as e:
        current_app.logger.error(f"Logout error: {e}")
        flash("An error occurred during logout. Please try again.", "error")
        return redirect(url_for('routes.login'))

# Custom error handlers
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
