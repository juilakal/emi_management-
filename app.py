import os
from datetime import date, datetime
from decimal import Decimal
from flask import Flask, render_template, request
from config import config_by_name
from models import db
from routes import register_routes
from routes.auth_middleware import get_current_user, generate_csrf_token, validate_csrf


def create_app(config_name: str = None) -> Flask:
    """Application factory for the EMI Management System."""
    app = Flask(__name__)

    # Determine configuration
    if config_name is None:
        config_name = os.getenv("FLASK_ENV", "development").lower()

    config_class = config_by_name.get(config_name, config_by_name["default"])
    app.config.from_object(config_class)

    # Initialize instance folder
    os.makedirs(app.instance_path, exist_ok=True)

    # Check database connectivity
    app.config["DB_MODE"] = "mysql"
    if not app.config.get("TESTING"):
        from sqlalchemy import create_engine, text
        orig_uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
        if "mysql" in orig_uri:
            try:
                test_engine = create_engine(orig_uri, pool_pre_ping=False)
                with test_engine.connect() as conn:
                    conn.execute(text("SELECT 1"))
            except Exception as e:
                sqlite_path = os.path.join(app.instance_path, "emi_management.sqlite")
                app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{sqlite_path}"
                app.config["DB_MODE"] = "sqlite_fallback"
                print(f"\n[NOTICE] MySQL server not reachable ({e}). Using local fallback: {app.config['SQLALCHEMY_DATABASE_URI']}\n")

    # Initialize extensions
    db.init_app(app)

    # Ensure tables exist
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"[DB Init Notice]: {e}")

    # CSRF Protection Hook
    @app.before_request
    def csrf_protect():
        # Bypass CSRF checks in automated test runs or API endpoints with json
        if app.config.get("TESTING") or not app.config.get("WTF_CSRF_ENABLED", True):
            return
        if request.endpoint and request.endpoint.startswith("static"):
            return
        if request.is_json and request.path.startswith("/calculator/api"):
            return
        validate_csrf()

    # Template Context Processors
    @app.context_processor
    def inject_template_globals():
        return {
            "current_user": get_current_user(),
            "csrf_token": generate_csrf_token,
            "today_date": date.today(),
            "now_year": datetime.utcnow().year,
            "db_mode": app.config.get("DB_MODE", "mysql"),
        }

    # Custom Jinja Filters
    @app.template_filter("currency")
    def currency_filter(value):
        """Format numbers as Indian Rupee currency (e.g. ₹1,23,456.78 or standard format)."""
        if value is None:
            return "₹0.00"
        try:
            val = Decimal(str(value))
            return f"₹{val:,.2f}"
        except Exception:
            return f"₹{value}"

    @app.template_filter("date_format")
    def date_format_filter(value, fmt="%d %b %Y"):
        """Format date objects into readable strings."""
        if not value:
            return ""
        if isinstance(value, (date, datetime)):
            return value.strftime(fmt)
        return str(value)

    # Register Blueprints
    register_routes(app)

    # HTTP Error Handlers
    @app.errorhandler(400)
    def bad_request(error):
        return render_template("404.html", error_title="400 - Bad Request", error_message=getattr(error, "description", "The request could not be processed.")), 400

    @app.errorhandler(404)
    def page_not_found(error):
        return render_template("404.html", error_title="404 - Page Not Found", error_message="The page you requested does not exist or has been moved."), 404

    @app.errorhandler(500)
    def internal_server_error(error):
        return render_template("500.html", error_title="500 - Internal Server Error", error_message="An unexpected system error occurred. Please try again shortly."), 500

    # CLI command for table creation
    @app.cli.command("init-db")
    def init_db_command():
        """Initialize and create database tables."""
        with app.app_context():
            db.create_all()
            print("Database tables initialized successfully!")

    return app


# Create default instance for WSGI servers
app = create_app()

if __name__ == "__main__":
    # Create tables automatically on dev startup if needed
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Note on DB init: {e}")
    # Use port 5050 by default on macOS because port 5000 is occupied by Apple AirPlay Receiver
    port = int(os.getenv("PORT", 5050))
    print(f"\n=======================================================")
    print(f" EMI Management System is running!")
    print(f" Open in your browser: http://127.0.0.1:{port} or http://localhost:{port}")
    print(f"=======================================================\n")
    app.run(host="0.0.0.0", port=port, debug=True)
