import os
import time
import requests
from flask import Blueprint, session, redirect, url_for, flash

token_refresh_bp = Blueprint("token_refresh", __name__)

TOKEN_URI     = os.getenv("TOKEN_URI", "")
CLIENT_ID     = os.getenv("CLIENT_ID", "")
CLIENT_SECRET = os.getenv("CLIENT_SECRET", "")
REDIRECT_URI  = os.getenv("REDIRECT_URI", "")


@token_refresh_bp.route("/token/refresh")
def refresh():
    user_info = session.get("user_info")
    if not user_info:
        flash("Please log in.", "warning")
        return redirect(url_for("routes.index"))

    refresh_token = session.get("refresh_token")
    if not refresh_token:
        flash("No refresh token in session. WSO2 may not have issued one.", "warning")
        return redirect(url_for("routes.user_home"))

    try:
        resp = requests.post(
            TOKEN_URI,
            data={
                "grant_type":    "refresh_token",
                "refresh_token": refresh_token,
                "client_id":     CLIENT_ID,
                "client_secret": CLIENT_SECRET,
                "redirect_uri":  REDIRECT_URI,
            },
            verify=False,
            timeout=8,
        )
        if resp.status_code == 200:
            data = resp.json()
            session["access_token"] = data.get("access_token", session.get("access_token"))
            if data.get("refresh_token"):
                session["refresh_token"] = data["refresh_token"]
            expires_in = int(data.get("expires_in", 3600))
            session["token_expiry"] = time.time() + expires_in
            flash("✔ Access token refreshed successfully!", "success")
        else:
            flash(f"Token refresh failed ({resp.status_code}): {resp.text[:200]}", "danger")
    except Exception as exc:
        flash(f"Token refresh error: {exc}", "danger")

    return redirect(url_for("routes.user_home"))
