import json
import os

FEATURES = [
    {"key": "pkce",               "name": "PKCE (Proof Key for Code Exchange)",   "description": "Adds code_verifier/code_challenge to the OIDC auth flow"},
    {"key": "token_introspection","name": "Token Introspection",                   "description": "Calls WSO2's introspect endpoint to validate token status"},
    {"key": "refresh_token",      "name": "Refresh Token Flow",                    "description": "Silently renews access tokens without re-login"},
    {"key": "rbac",               "name": "Role-Based Access Control (RBAC)",      "description": "Scope-based route gating — /admin requires 'admin' role"},
    {"key": "audit_log",          "name": "Session Audit Log",                     "description": "Records every login/logout event in PostgreSQL"},
    {"key": "token_inspector",    "name": "Token Inspector",                       "description": "Decodes and displays JWT claims from ID & Access Tokens"},
    {"key": "oidc_flow",          "name": "OIDC Flow Visualizer",                  "description": "Animated step-by-step diagram of the Authorization Code flow"},
    {"key": "token_timer",        "name": "Token Lifecycle Timer",                 "description": "Countdown timer on dashboard showing time until token expiry"},
    {"key": "debug_trace",        "name": "Debug / Trace Panel",                   "description": "Shows raw OIDC responses and decoded token data"},
]

_FLAGS_FILE = os.path.join(os.path.dirname(__file__), "enabled_features.json")
_enabled: set = set()


def load():
    global _enabled
    if os.path.exists(_FLAGS_FILE):
        try:
            with open(_FLAGS_FILE, "r") as f:
                _enabled = set(json.load(f).get("enabled", []))
        except Exception:
            _enabled = set()
    else:
        _enabled = set()


def save(enabled_keys: list):
    global _enabled
    _enabled = set(enabled_keys)
    with open(_FLAGS_FILE, "w") as f:
        json.dump({"enabled": list(enabled_keys)}, f, indent=2)


def is_enabled(key: str) -> bool:
    return key in _enabled


def get_all_flags() -> dict:
    return {f["key"]: (f["key"] in _enabled) for f in FEATURES}


load()
