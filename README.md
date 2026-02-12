# Flask OIDC Integration with WSO2 Identity Server 🚀

This project is a Flask-based application integrating OpenID Connect (OIDC) authentication with WSO2 Identity Server (or other OIDC providers). The app demonstrates secure user login, access token handling, user information retrieval, and advanced logout functionality including Back-Channel Logout.

## ✨ Features

- 🔒 **OIDC Authentication**: Seamless login using WSO2 Identity Server.
- 🛡️ **Secure Configuration**: Sensitive credentials managed via `.env`.
- 🗂️ **Session Management**: Secure server-side session handling with access and ID tokens.
- 🚪 **Advanced Logout**:
  - **Standard Logout**: User-initiated Single Logout (SLO).
  - **Back-Channel Logout**: Support for OIDC Back-Channel Logout to invalidate sessions triggered by the IdP.
  - **Front-Channel Logout**: Support for OIDC Front-Channel Logout.
- 🧩 **Flask Blueprints**: Modular code structure.
- 🌐 **HTTPS Support**: Ready for local HTTPS testing.

---

## 🛠️ Getting Started

### 📋 Prerequisites

1. 🐍 Python 3.8+
2. 📦 [pip](https://pip.pypa.io/en/stable/installation/)
3. ⚙️ WSO2 Identity Server (or Keycloak/Auth0) configured for OIDC.

---

### 📥 Installation

1. **Clone the Repository**
   ```bash
   git clone [https://github.com/your-username/your-repo-name.git](https://github.com/svn23/WSO2_Py.git)
   cd WSO@_py
   ```

2. **Set Up a Virtual Environment** *(recommended)*
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Mac/Linux:
   source venv/bin/activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configuration**
   Create a `.env` file in the root directory:
   ```env
   # App Secret
   FLASK_SECRET_KEY=your_random_secret_string

   # OIDC Configuration
   AUTHORIZATION_URI=https://<idp-domain>/oauth2/authorize
   TOKEN_URI=https://<idp-domain>/oauth2/token
   USERINFO_URI=https://<idp-domain>/oauth2/userinfo
   LOGOUT_URI=https://<idp-domain>/oidc/logout
   
   CLIENT_ID=your_client_id
   CLIENT_SECRET=your_client_secret
   REDIRECT_URI=https://localhost:2312/OIDC/wso2/authorized
   
   # OIDC Scopes (Ensure 'openid' is included)
   OIDC_SCOPES=openid email profile roles
   ```

5. **SSL Certificates** (Required for OIDC flows)
   The app runs on HTTPS by default. You can generate self-signed certs:
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes
   ```
   *Or rely on the `adhoc` context if configured in `app.py`.*

---

### ▶️ Usage

1. **Run the Application**
   ```bash
   python app.py
   ```

2. **Access the App**
   Open your browser and navigate to: `https://localhost:2312`

3. **Authentication Flow**
   - **Login**: Click "Login with SSO" to redirect to the Identity Provider.
   - **Dashboard**: Access protected routes like `/OIDC/wso2/dashboard`.
   - **Logout**: 
     - Click "Logout" for standard logout.
     - The app also listens on `/OIDC/wso2/backchannel_logout` for logout tokens from the IdP.

---

### 📂 Project Structure

```plaintext
├── app.py               # Main Flask application entry point
├── routes/
│   ├── routes.py        # General application routes
│   ├── OIDC/
│       ├── wso2.py      # OIDC Logic (Login, Callback, Logout, Back-Channel)
├── templates/           # HTML Templates
│   ├── dashboard.html
│   ├── user_dash.html
│   ├── ...
├── requirements.txt     # Python dependencies
├── .env                 # Configuration (Not committed)
└── README.md            # Documentation
```

---

### ⚙️ Identity Provider Configuration (Keycloak Example)
To ensure Back-Channel Logout works correctly, configure your Client in Keycloak as follows:

1. **Client Settings**:
   - **Client ID**: `python_sp` (match your `.env`).
   - **Client Protocol**: `openid-connect`.
   - **Access Type**: `confidential` (Required for Back-Channel).

2. **Advanced Settings / OpenID Connect Compatibility**:
   - ✅ **Backchannel Logout Session Required**: **ON** (Critical: sends SID/SUB in token).
   - ✅ **Backchannel Logout Revoke Offline Sessions**: **ON**.

3. **URLs**:
   | Setting | Value | Note |
   |---------|-------|------|
   | **Valid Redirect URIs** | `https://localhost:2312/OIDC/wso2/authorized` | Frontend callback. |
   | **Web Origins** | `https://localhost:2312` | CORS compliance. |
   | **Backchannel Logout URL** | `https://host.docker.internal:2312/OIDC/wso2/backchannel_logout` | **Must be reachable by Keycloak!** If running Keycloak in Docker, use `host.docker.internal` or your LAN IP. |

> [!WARNING]
> **"Connection Refused" Error?**
> If you see `java.net.ConnectException: Connection refused` in Keycloak logs, it means Keycloak cannot reach `localhost:2312`.
> **Fix**: Change the **Backchannel Logout URL** to `https://host.docker.internal:2312/...` (for Docker Desktop) or `https://<YOUR_LAN_IP>:2312/...`.

### 🛡️ Back-Channel Logout
This application implements a **Robust OIDC Back-Channel Logout** mechanism.

- **Endpoint**: `/OIDC/wso2/backchannel_logout`
- **Mechanism**: 
  1.  **Global Revocation**: When the IdP sends a logout token, the app records a **Revocation Timestamp** for that user.
  2.  **Auth Time Verification**: 
      - On every request, the app checks the user's `auth_time` (original login time) from their token.
      - If `auth_time` is **older** than the Revocation Timestamp, the session is considered stale.
  3.  **Forced Re-Authentication**:
      - Stale sessions are redirected to the IdP with `prompt=login`.
      - This forces the user to enter their password again, breaking "Silent SSO" loops and ensuring true logout across all browsers.

---

### 📧 Contact

For support, please create an issue in the repository.
