from flask import Blueprint, session, render_template, redirect, url_for, flash
from features.audit import get_events
from features.feature_flags import get_all_flags

audit_log_bp = Blueprint("audit_log", __name__)


@audit_log_bp.route("/audit/log")
def audit_log():
    user_info = session.get("user_info")
    if not user_info:
        flash("Please log in.", "warning")
        return redirect(url_for("routes.index"))

    events = get_events(limit=200)
    logins   = sum(1 for e in events if e["event_type"] == "LOGIN")
    logouts  = sum(1 for e in events if e["event_type"] == "LOGOUT")

    safe_info = {k: str(v) if v is not None else "" for k, v in user_info.items()}
    return render_template(
        "audit_log.html",
        events=events,
        total=len(events),
        logins=logins,
        logouts=logouts,
        features=get_all_flags(),
        **safe_info,
    )
