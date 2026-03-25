from flask import Blueprint, session, render_template
from features.feature_flags import get_all_flags

oidc_flow_bp = Blueprint("oidc_flow", __name__)


@oidc_flow_bp.route("/learn/oidc_flow")
def oidc_flow():
    user_info = session.get("user_info") or {}
    safe_info = {k: str(v) if v is not None else "" for k, v in user_info.items()}
    # Provide defaults so template header doesn't crash when not logged in
    defaults = {"given_name": "", "family_name": "", "email": "", "sub": "",
                "roles": "", "phone_number": "", "picture": ""}
    defaults.update(safe_info)
    return render_template("oidc_flow.html", features=get_all_flags(), **defaults)
