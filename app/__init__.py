"""
Flask application factory.
"""

import logging
import os
import secrets
import sys
import traceback
from pathlib import Path

from flask import Flask

from app.config import LokiConfig, get_config
from app.extensions import (
    db,
    init_cors,
    init_swagger,
    login_manager,
    migrate,
    scheduler,
)
from app.imports.lokilogger import lokilog


def create_app(config_name=None):
    """
    Application factory for creating Flask app instance.

    Args:
        config_name: Optional config name ('dev' or 'prod').
                    If None, will use FLASK_ENV environment variable.

    Returns:
        Configured Flask application instance
    """
    app = Flask(__name__)

    # Load configuration
    if config_name:
        os.environ["FLASK_ENV"] = config_name

    config = get_config()
    app.config.from_object(config)

    # Ensure SECRET_KEY is always set; in development a random key is acceptable.
    if not app.config.get("SECRET_KEY"):
        if config.DEBUG:
            app.config["SECRET_KEY"] = secrets.token_hex(32)
        else:
            raise RuntimeError(
                "SECRET_KEY environment variable must be set in production. "
                "Set FLASK_SECRET_KEY in your .env file."
            )

    # Configure logging
    log_level = logging.DEBUG if config.DEBUG else logging.INFO
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    root_logger = logging.getLogger()
    if not root_logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(logging.Formatter(log_format))
        root_logger.addHandler(handler)
    root_logger.setLevel(log_level)
    app.logger.setLevel(log_level)

    # Load version
    version = load_version(app)
    app.config["VERSION"] = version

    # Initialize Loki logging
    loki_config = LokiConfig()
    config_mode = "dev" if config.DEBUG else "prod"

    if loki_config.LOKI_ENABLED:
        print("Loki enabled")
    else:
        print("Loki disabled")

    loki = lokilog(
        loki_config.HTTPS_URL,
        loki_config.HOST,
        loki_config.SOURCE,
        config_mode,
        version,
        loki_config.LOKI_ENABLED,
    )

    try:
        loki.info({"Message": "Application starting"})
    except Exception:
        pass

    # Store loki instance in app for access by routes
    app.loki = loki  # type: ignore

    # Print email status
    if app.config["EMAIL_ENABLED"]:
        print("Mail enabled")
    else:
        print("Mail disabled")

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.session_protection = "strong"
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    # Allow the operator to override via env var so plain-HTTP deployments
    # (e.g. Raspberry Pi on a local network behind nginx without TLS) still work.
    _secure_env = os.environ.get("SESSION_COOKIE_SECURE", "").lower()
    if _secure_env in ("true", "1", "yes"):
        app.config["SESSION_COOKIE_SECURE"] = True
    elif _secure_env in ("false", "0", "no"):
        app.config["SESSION_COOKIE_SECURE"] = False
    else:
        app.config["SESSION_COOKIE_SECURE"] = not config.DEBUG
    app.config["REMEMBER_COOKIE_HTTPONLY"] = True
    init_cors(app)

    # Initialize PDF service and attach to app
    from app.services.pdf_service import PDFService

    app.pdf_service = PDFService(  # type: ignore
        storage_dir=app.config.get("SIGNED_PDF_STORAGE_PATH")
    )

    # Initialize Label service and attach to app
    from app.services.label_service import LabelService

    app.label_service = LabelService(  # type: ignore
        default_device=app.config.get("LABEL_PRINTER_DEVICE", "/dev/usb/lp0"),
        default_method=app.config.get("LABEL_PRINT_METHOD", "file"),
        default_cups_name=app.config.get("LABEL_PRINTER_NAME", "SLP650"),
        default_network_ip=app.config.get("LABEL_PRINTER_IP"),
        default_network_port=app.config.get("LABEL_PRINTER_PORT", 9100),
    )

    # Initialize Swagger
    swagger = init_swagger(app)
    app.swagger = swagger  # type: ignore

    # Configure login manager
    login_manager.unauthorized_handler(unauthorized_callback)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Optionally create tables on startup (disabled by default)
    if os.environ.get("CREATE_TABLES_ON_STARTUP") == "1":
        with app.app_context():
            db.create_all()

    # Ensure at least one admin user exists on every startup.
    # Safe to run repeatedly — is a no-op when an admin already exists.
    with app.app_context():
        ensure_admin_user(app)

    return app


def load_version(app):
    """Load version from VERSION file."""
    version = "unknown"
    try:
        version_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)), "VERSION"
        )
        with open(version_path) as ver:
            version = ver.readline().strip()
    except Exception as e:
        print(f"Error loading version: {e}")

    return version


def unauthorized_callback():
    """Return 401 JSON for API requests; redirect to the SPA login page for browser requests."""
    import json

    from flask import Response, redirect, request

    if request.path.startswith("/api/"):
        return Response(
            json.dumps({"reply": "error", "error": "Authentication required"}),
            status=401,
            mimetype="application/json",
        )
    return redirect("/login")


def register_blueprints(app):
    """Register Flask blueprints."""
    # Import blueprints here to avoid circular imports
    from app.api.config import config_bp
    from app.api.customers import customers_bp
    from app.api.health import health_bp
    from app.api.repair_logs import repair_logs_bp
    from app.api.repairs import repairs_bp
    from app.api.settings import settings_bp
    from app.api.users import users_bp
    from app.api.vde_tests import vde_tests_bp
    from app.auth.routes import auth_bp
    from app.web.routes import web_bp

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(web_bp, url_prefix="/api")
    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(repairs_bp, url_prefix="/api")
    app.register_blueprint(repair_logs_bp, url_prefix="/api")
    app.register_blueprint(vde_tests_bp, url_prefix="/api")
    app.register_blueprint(config_bp, url_prefix="/api")
    app.register_blueprint(customers_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api")
    app.register_blueprint(settings_bp, url_prefix="/api")


def register_error_handlers(app):
    """Register error handlers."""

    @app.after_request
    def add_header(response):
        """Add cache control headers."""
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        response.headers["Cache-Control"] = "public, max-age=0"
        return response


def ensure_admin_user(app):
    """Create a default admin user if no admin exists, logging the generated password prominently."""
    try:
        from werkzeug.security import generate_password_hash

        from app.models import User

        if User.query.filter_by(is_admin=True).first():
            return  # at least one admin already exists

        password = secrets.token_urlsafe(16)
        admin = User(
            username="admin",
            vorname="Admin",
            nachname="",
            email="admin@repaircafe.local",
            password_hash=generate_password_hash(password),
            is_admin=True,
        )
        db.session.add(admin)
        db.session.commit()

        border = "=" * 72
        app.logger.warning(border)
        app.logger.warning("  INITIAL ADMIN USER CREATED")
        app.logger.warning("  Username: admin")
        app.logger.warning("  Password: %s", password)
        app.logger.warning("  Change this password immediately after first login!")
        app.logger.warning(border)
    except Exception as e:
        app.logger.error(f"Could not ensure admin user: {e}")
