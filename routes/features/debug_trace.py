import jwt as pyjwt
from flask import Blueprint, session, render_template, redirect, url_for, flash
from features.feature_flags import get_all_flags

debug_trace_bp = Blueprint("debug_trace", __name__)


def _safe_decode(token: str):
    if not token:
        return None
    try:
        return pyjwt.decode(token, options={"verify_signature": False})
    except Exception:
        return None


@debug_trace_bp.route("/debug/trace")
def debug_trace():
    user_info = session.get("user_info")
    if not user_info:
        flash("Please log in.", "warning")
        return redirect(url_for("routes.index"))

    id_token     = session.get("id_token", "")
    access_token = session.get("access_token", "")

    # Build safe session snapshot (hide raw tokens)
    safe_session = {k: v for k, v in session.items()
                    if k not in ("access_token", "id_token", "refresh_token")}

    safe_info = {k: str(v) if v is not None else "" for k, v in user_info.items()}
    return render_template(
        "debug_trace.html",
        id_token=id_token,
        access_token=access_token,
        id_decoded=_safe_decode(id_token),
        access_decoded=_safe_decode(access_token),
        user_info=user_info,
        safe_session=safe_session,
        features=get_all_flags(),
        **safe_info,
    )
