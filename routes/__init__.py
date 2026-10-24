from flask import Flask
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.loan_routes import loan_bp
from routes.emi_routes import emi_bp
from routes.payment_routes import payment_bp
from routes.report_routes import report_bp


def register_routes(app: Flask) -> None:
    """Register all modular application blueprints."""
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(loan_bp)
    app.register_blueprint(emi_bp)
    app.register_blueprint(payment_bp)
    app.register_blueprint(report_bp)
