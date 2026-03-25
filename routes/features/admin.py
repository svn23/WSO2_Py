from flask import Blueprint, session, render_template
from features.rbac import role_required
from features.feature_flags import get_all_flags, FEATURES

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/admin")
@role_required()
def admin_panel():
    user_info = session.get("user_info", {})

    audit_events = []
    audit_available = False
    try:
        from features.audit import get_events
        audit_events = get_events(limit=50)
        audit_available = True
    except Exception:
        pass

    return render_template(
        "admin_panel.html",
        user_info=user_info,
        features=get_all_flags(),
        all_features=FEATURES,
        audit_events=audit_events,
        audit_available=audit_available,
        **{k: str(v) if v is not None else "" for k, v in user_info.items()},
    )
