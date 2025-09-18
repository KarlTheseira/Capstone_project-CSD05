from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models import User, db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        flash("Email and password are required.", "danger")
        return redirect(url_for("auth.register"))

    if User.query.filter_by(email=email).first():
        flash("Email is already registered.", "danger")
        return redirect(url_for("auth.register"))

    hashed_pw = generate_password_hash(password)
    user = User(email=email, password_hash=hashed_pw)
    db.session.add(user)
    db.session.commit()

    flash("Registration successful. Please log in.", "success")
    return redirect(url_for("auth.login"))

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    user = User.query.filter_by(email=email).first()

    if not user or not check_password_hash(user.password_hash, password):
        flash("Invalid email or password.", "danger")
        return redirect(url_for("auth.login"))

    session["user_id"] = user.id
    flash("Logged in successfully.", "success")
    return redirect(url_for("public.index"))

@auth_bp.route("/logout")
def logout():
    session.pop("user_id", None)
    flash("You have been logged out.", "success")
    return redirect(url_for("public.index"))
