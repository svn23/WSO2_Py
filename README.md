# Flask OIDC Integration with WSO2 Identity Server 🚀

This project is a Flask-based application integrating OpenID Connect (OIDC) authentication with WSO2 Identity Server. The app demonstrates secure user login, access token handling, user information retrieval, and logout functionality.

## ✨ Features

- 🔒 **OIDC Authentication** using WSO2 Identity Server.
- 🛡️ **Secure Storage** of sensitive information using a `.env` file.
- 🗂️ **Session Management** with access and ID tokens.
- 🧩 **Flask Blueprints** for modular code organization.
- 🌐 HTTPS support for local testing.

---

## 🛠️ Getting Started

### 📋 Prerequisites

1. 🐍 Python 3.7+
2. 📦 [pip](https://pip.pypa.io/en/stable/installation/)
3. ⚙️ WSO2 Identity Server configured for OIDC.

---

### 📥 Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/svn23/WSO2_Py.git
   cd your-repo-name
   ```

2. **Set Up a Virtual Environment** *(optional but recommended)*
   ```bash
   python -m venv venv
   source venv/bin/activate   # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create a `.env` File**
   Create a `.env` file in the root directory and add the following:
   ```env
   AUTHORIZATION_URI=your-authorization-endpoint
   TOKEN_URI=your-token-endpoint
   USERINFO_URI=your-userinfo-endpoint
   LOGOUT_URI=your-logout-uri
   CLIENT_ID=your-client-id
   CLIENT_SECRET=your-client-secret
   REDIRECT_URI=https://your-IP:Port/OIDC/wso2/authorized
   OIDC_SCOPES=openid email phone profile roles
   ```

5. **Generate SSL Certificates** *(for local HTTPS testing)*
   Generate `server.crt` and `server.key` or use the `adhoc` SSL context in development:
   ```bash
   openssl req -x509 -newkey rsa:4096 -keyout server.key -out server.crt -days 365 -nodes
   ```

---

### ▶️ Usage

1. **Run the Application**
   ```bash
   python app.py
   ```

2. **Access the Application**
   Open your browser and navigate to:
   ```
   https://localhost:2312
   ```

3. **OIDC Authentication**
   - 🔑 Visit `/OIDC/wso2/login` to initiate login.
   - 👤 After successful login, user details are displayed.
   - 🚪 Logout using `/OIDC/wso2/logout`.

---

### 📂 Project Structure

```plaintext
├── app.py               # Main Flask application
├── routes/
│   ├── routes.py        # Additional app routes
│   ├── OIDC/
│       ├── wso2.py      # WSO2 OIDC Blueprint
├── templates/
│   ├── dashboard.html   # User dashboard template
├── requirements.txt     # Python dependencies
├── .env                 # Environment variables
├── README.md            # Project documentation
└── server.key / server.crt  # SSL certificates (optional)
```

---

### 🔐 Environment Variables

The `.env` file contains sensitive details like client ID, client secret, and URIs. Ensure the `.env` file is **not committed** to version control by adding it to `.gitignore`.

---

### 🛡️ Security Tips

1. Use strong, randomly generated `FLASK_SECRET_KEY`.
2. Avoid storing sensitive credentials in the codebase.
3. Use HTTPS in production for secure communication.

---

### 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

### 🤝 Contributions

Contributions are welcome! Please fork the repository and submit a pull request for review.

---

### 📧 Contact

For queries or support, feel free to contact:
- **Your Name**: [sovanmstse@example.com](sovanmstse@example.com)
- GitHub: [svn23](https://github.com/svn23)

