#!/usr/bin/env python

from flask import Flask
from flask_cors import CORS
from routes.routes import routes_bp
from routes.OIDC.wso2 import wso2_bp
import os
import secrets
from dotenv import load_dotenv

app = Flask(__name__)

# Load existing environment variables from the .env file
load_dotenv()

# Generate a new secret key
new_secret_key = secrets.token_hex(32)

# Replace or add the secret key in the .env file
env_file_path = '.env'
if os.path.exists(env_file_path):
    with open(env_file_path, 'r') as env_file:
        lines = env_file.readlines()

    # Replace FLASK_SECRET_KEY if it exists
    with open(env_file_path, 'w') as env_file:
        key_replaced = False
        for line in lines:
            if line.startswith('FLASK_SECRET_KEY='):
                env_file.write(f"FLASK_SECRET_KEY={new_secret_key}\n")
                key_replaced = True
            else:
                env_file.write(line)
        
        # If FLASK_SECRET_KEY was not found, add it
        if not key_replaced:
            env_file.write(f"FLASK_SECRET_KEY={new_secret_key}\n")
else:
    # Create the .env file and add the secret key
    with open(env_file_path, 'w') as env_file:
        env_file.write(f"FLASK_SECRET_KEY={new_secret_key}\n")

# Set the secret key for the Flask app
app.secret_key = new_secret_key

app.config['SESSION_COOKIE_SECURE'] = False  # Use False when running on HTTP (localhost)
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Make cookies accessible only through HTTP
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # Helps with cross-site request handling
CORS(app)

# Register the blueprints
app.register_blueprint(routes_bp)
app.register_blueprint(wso2_bp, url_prefix='/OIDC/wso2')

if __name__ == '__main__':
    with app.app_context():
        app.run(debug=True, port=2312)
