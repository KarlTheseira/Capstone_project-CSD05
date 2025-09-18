from flask import Flask, session
from models import db
from config import Config

# Import blueprints
from routes.public import public_bp
from routes.admin import admin_bp
from routes.auth import auth_bp

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

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

if __name__ == "__main__":
    app.run(debug=True)
