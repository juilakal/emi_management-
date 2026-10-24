from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from services.auth_service import register_user, authenticate_user
from routes.auth_middleware import get_current_user

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    """Handle new user registration."""
    if get_current_user():
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        full_name = request.form.get("full_name", "")
        email = request.form.get("email", "")
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")

        user, error = register_user(
            full_name=full_name,
            email=email,
            password=password,
            confirm_password=confirm_password
        )

        if error:
            flash(error, "danger")
            return render_template(
                "register.html",
                full_name=full_name,
                email=email
            )

        flash("Registration successful! You can now log in with your credentials.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    """Handle user login and authentication."""
    if get_current_user():
        return redirect(url_for("dashboard.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "")
        password = request.form.get("password", "")

        user, error = authenticate_user(email=email, password=password)

        if error:
            flash(error, "danger")
            return render_template("login.html", email=email)

        # Set session
        session.clear()
        session["user_id"] = user.user_id
        session["user_name"] = user.full_name
        session["user_email"] = user.email

        flash(f"Welcome back, {user.full_name}!", "success")

        next_url = request.args.get("next")
        # Ensure next_url is a safe relative URL
        if next_url and next_url.startswith("/"):
            return redirect(next_url)
        return redirect(url_for("dashboard.dashboard"))

    return render_template("login.html")


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    """Log out current user and clear session."""
    session.clear()
    flash("You have been successfully logged out.", "info")
    return redirect(url_for("auth.login"))
