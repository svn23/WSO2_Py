import jwt as pyjwt
from flask import Blueprint, session, render_template, redirect, url_for, flash
from features.feature_flags import get_all_flags

token_inspector_bp = Blueprint("token_inspector", __name__)


def _safe_decode(token: str) -> dict:
    if not token:
        return {}
    try:
        return pyjwt.decode(token, options={"verify_signature": False})
    except Exception:
        return {}


@token_inspector_bp.route("/token/inspect")
def inspect():
    user_info = session.get("user_info")
    if not user_info:
        flash("Please log in.", "warning")
        return redirect(url_for("routes.index"))

    id_token     = session.get("id_token", "")
    access_token = session.get("access_token", "")

    id_claims     = _safe_decode(id_token)
    access_claims = _safe_decode(access_token)

    safe_info = {k: str(v) if v is not None else "" for k, v in user_info.items()}
    return render_template(
        "token_inspector.html",
        id_token=id_token,
        access_token=access_token,
        id_claims=id_claims,
        access_claims=access_claims,
        features=get_all_flags(),
        **safe_info,
    )
