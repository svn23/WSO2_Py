# 🛡 SecureSphere (WSO2_Py version-3)

**SecureSphere** is an enterprise-grade Identity and Access Management (IAM) demonstration application built specifically to showcase the capabilities of modern OpenID Connect (OIDC) authentication flows. Engineered natively using **Python & Flask**, it provides an elegant and deep, high-fidelity lens into OAuth 2.0 standards, JSON Web Token (JWT) inspection, and dynamic Role-Based Access Control (RBAC).

This version leverages an integration capability allowing seamless switching between **WSO2 Identity Server / Asgardeo** and **Google Workspace**. It further expands into full telemetry with persistent Audit Logging powered by PostgreSQL and **Alembic migrations**.

---

## ✨ Core Features

* **Multi-Provider OIDC Flows**: Native Authorization Code with **PKCE** handling.
* **Introspection & Inspection Engine**: Visual tools to deconstruct encrypted Access, ID, and Refresh tokens in real-time.
* **Persistent Telemetry (Supabase/PG)**: Centralized database capturing every login, logoff, browser User Agent, unique IP, organizational role, and assigned Auth Methods (AMR).
* **Automated Alembic Database Workflows**: One-command database schema protection to spawn audit tables automatically.
* **Dynamic Frontend Pipeline**: Complete UI generation across 8 distinct internal template applications (Dashboards, Admin tools, Diagnostics, Introspectors) unified through a beautiful, static CSS framework architecture. 
* **Back-Channel Logout Handling (SID Tracking)**: Centralized revocation of tokens gracefully tracked across devices.

## 🚀 QuickStart Installation guide

### 1. Requirements
Ensure you have **Python 3.9+** and a running PostgreSQL instance (like Supabase, AWS RDS, or Render).

### 2. Sandbox Setup
```bash
git clone https://github.com/svn23/WSO2_Py.git
cd WSO2_Py
git checkout version-3

# Initialize your virtual environment
python -m venv venv
# Windows
venv\Scripts\activate
# MacOS / Linux
source venv/bin/activate

# Install the Python dependencies (Alembic natively included)
pip install -r requirements.txt
```

### 3. Environment Handshake
Copy the secure `.env.example` boilerplate to `.env` and plug in your client credentials:
```bash
cp .env.example .env
```
_Wait—what exactly do I put inside `.env`?_ Just match your Google or WSO2 Client IDs, Client Secrets, and your PostgreSQL `DATABASE_URL` string!

### 4. Database Migrations
Create your localized SecureSphere audit trails and RBAC telemetry maps by triggering Alembic:
```bash
alembic upgrade head
```

### 5. Launch the Reactor
Kick off your self-hosted instance and watch the magic unfold locally!
```bash
python app.py
```

## 👨‍💻 Developed By

**Sovan Sen**
* 🌐 **Portfolio**: [sovansen.in](https://sovansen.in/)
* 📧 **Email**: [sovanmstse@gmail.com](mailto:sovanmstse@gmail.com)
* 💼 **LinkedIn**: [sovan-sen-23dec](https://www.linkedin.com/in/sovan-sen-23dec/)
* 🐦 **X (Twitter)**: [@SovanSen23](https://x.com/SovanSen23)

Feel free to break it, test it, and clone it! Submit an issue or PR to this repo if you enhance any Identity routing protocols.
