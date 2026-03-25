#!/usr/bin/env python

from dotenv import load_dotenv
load_dotenv()

# ── Startup wizard (runs BEFORE Flask boots) ────────────────────────────────
from features.startup_wizard import run as run_wizard
run_wizard()

# Reload flags after wizard may have updated them
from features import feature_flags
feature_flags.load()
# ────────────────────────────────────────────────────────────────────────────

from flask import Flask
from flask_cors import CORS
from routes.routes import routes_bp
from routes.OIDC.wso2 import wso2_bp
from routes.OIDC.google import google_bp
import os
import secrets

app = Flask(__name__)

# ── Rotate Flask secret key on every boot ───────────────────────────────────
new_secret_key = secrets.token_hex(32)
env_file_path = '.env'
if os.path.exists(env_file_path):
    with open(env_file_path, 'r') as f:
        lines = f.readlines()
    if lines and not lines[-1].endswith('\n'):
        lines[-1] += '\n'
    with open(env_file_path, 'w') as f:
        replaced = False
        for line in lines:
            if line.startswith('FLASK_SECRET_KEY='):
                f.write(f"FLASK_SECRET_KEY={new_secret_key}\n")
                replaced = True
            else:
                f.write(line)
        if not replaced:
            f.write(f"FLASK_SECRET_KEY={new_secret_key}\n")
else:
    with open(env_file_path, 'w') as f:
        f.write(f"FLASK_SECRET_KEY={new_secret_key}\n")

app.secret_key = new_secret_key
app.config['SESSION_COOKIE_SECURE']   = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
CORS(app)

# ── Core blueprints ──────────────────────────────────────────────────────────
app.register_blueprint(routes_bp)
app.register_blueprint(wso2_bp,   url_prefix='/OIDC/wso2')
app.register_blueprint(google_bp, url_prefix='/OIDC/google')

# ── Optional feature blueprints (only registered when enabled) ───────────────
if feature_flags.is_enabled("token_introspection"):
    from routes.features.token_introspect import token_introspect_bp
    app.register_blueprint(token_introspect_bp)

if feature_flags.is_enabled("refresh_token"):
    from routes.features.token_refresh import token_refresh_bp
    app.register_blueprint(token_refresh_bp)

if feature_flags.is_enabled("rbac"):
    from routes.features.admin import admin_bp
    app.register_blueprint(admin_bp)

if feature_flags.is_enabled("audit_log"):
    from routes.features.audit_log import audit_log_bp
    app.register_blueprint(audit_log_bp)

if feature_flags.is_enabled("token_inspector"):
    from routes.features.token_inspector import token_inspector_bp
    app.register_blueprint(token_inspector_bp)

if feature_flags.is_enabled("oidc_flow"):
    from routes.features.oidc_flow import oidc_flow_bp
    app.register_blueprint(oidc_flow_bp)

if feature_flags.is_enabled("debug_trace"):
    from routes.features.debug_trace import debug_trace_bp
    app.register_blueprint(debug_trace_bp)

if __name__ == '__main__':
    app.run(debug=True, port=2312)
