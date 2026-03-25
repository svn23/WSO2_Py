import os
import requests
from flask import Blueprint, session, render_template, redirect, url_for, flash
from features.feature_flags import get_all_flags

token_introspect_bp = Blueprint("token_introspect", __name__)

INTROSPECT_URI  = os.getenv("INTROSPECT_URI", "")
CLIENT_ID       = os.getenv("CLIENT_ID", "")
CLIENT_SECRET   = os.getenv("CLIENT_SECRET", "")


@token_introspect_bp.route("/token/introspect")
def introspect():
    user_info = session.get("user_info")
    if not user_info:
        flash("Please log in.", "warning")
        return redirect(url_for("routes.index"))

    access_token = session.get("access_token", "")
    result, error = None, None

    if not INTROSPECT_URI:
        error = "INTROSPECT_URI is not configured in .env — add it to use this feature."
    elif not access_token:
        error = "No access token found in session."
    else:
        try:
            resp = requests.post(
                INTROSPECT_URI,
                data={"token": access_token},
                auth=(CLIENT_ID, CLIENT_SECRET),
                verify=False,
                timeout=5,
            )
            result = resp.json()
        except Exception as exc:
            error = f"Introspection request failed: {exc}"

    safe_info = {k: v or "" for k, v in user_info.items()}
    return render_template(
        "token_introspect.html",
        result=result,
        error=error,
        features=get_all_flags(),
        **safe_info,
    )
