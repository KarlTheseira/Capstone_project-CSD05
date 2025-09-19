from flask import Flask, session, render_template
from flask_wtf.csrf import CSRFProtect
from flask_talisman import Talisman
from models import db
from config import Config

# Import blueprints
from routes.public import public_bp
from routes.admin import admin_bp
from routes.auth import auth_bp

app = Flask(__name__)
app.config.from_object(Config)

# Session security settings
app.config['SESSION_COOKIE_SECURE'] = True  # Only send cookies over HTTPS
app.config['SESSION_COOKIE_HTTPONLY'] = True  # Prevent JavaScript access to session cookie
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'  # CSRF protection
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # Session timeout in seconds (1 hour)

# Initialize extensions
db.init_app(app)
csrf = CSRFProtect(app)

# Security headers configuration
csp = {
    'default-src': "'self'",
    'img-src': ['*', 'data:'],  # Allow images from any source and data URLs
    'script-src': [
        "'self'",
        'https://cdn.jsdelivr.net',  # For Bootstrap
    ],
    'style-src': [
        "'self'",
        'https://cdn.jsdelivr.net',  # For Bootstrap
    ],
    'font-src': ["'self'", 'https:', 'data:'],
}

Talisman(app,
         content_security_policy=csp,
         force_https=True,  # Force HTTPS
         strict_transport_security=True,  # Enable HSTS
         session_cookie_secure=True,
         feature_policy={  # Restrict dangerous features
             'geolocation': "'none'",
             'microphone': "'none'",
             'camera': "'none'",
             'payment': "'self'"
         })

# Register blueprints
app.register_blueprint(public_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(auth_bp)

# Context processor for templates
from models import User
@app.context_processor
def inject_user():
    current_user = None
    current_admin = None
    if session.get("user_id"):
        current_user = User.query.get(session["user_id"])
    if session.get("admin"):
        current_admin = True
    return dict(current_user=current_user, current_admin=current_admin)

# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def internal_server_error(e):
    return render_template('errors/500.html'), 500

@app.errorhandler(403)
def forbidden(e):
    return render_template('errors/403.html'), 403

if __name__ == "__main__":
    app.run(debug=True)
