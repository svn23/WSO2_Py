import os
from functools import wraps
from flask import session, abort, flash, redirect, url_for

ADMIN_ROLE = os.getenv("ADMIN_ROLE", "admin")


def role_required(role: str = None):
    """
    Decorator: user must be logged in AND possess the given role.
    Role string is checked against session['user_info']['roles']
    which may be a list or a comma-separated string.
    Falls back to ADMIN_ROLE env var if role is not passed.
    """
    _role = role or ADMIN_ROLE

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_info = session.get("user_info")
            if not user_info:
                flash("Please log in to continue.", "warning")
                return redirect(url_for("routes.index"))

            raw = user_info.get("roles", "") or ""
            if isinstance(raw, list):
                user_roles = [str(r).strip().lower() for r in raw]
            else:
                user_roles = [r.strip().lower() for r in str(raw).replace(",", " ").split() if r.strip()]

            if _role.lower() not in user_roles:
                abort(403)

            return f(*args, **kwargs)
        return decorated
    return decorator
