"""
Centralized configuration for the Flask application.
"""

import os
import secrets
from pathlib import Path


class LokiConfig:
    """Configuration for Loki logging."""

    LOKI_ID = os.environ.get("GCLOUD_HOSTED_LOGS_ID", False)
    LOKI_TOKEN = os.environ.get("GCLOUD_PROM_API_KEY", False)
    LOKI_URL = os.environ.get("GCLOUD_HOSTED_LOGS_URL", False)
    # if any of LOKI_ID, LOKI_TOKEN, LOKI_URL is False, LOKI_ENABLED will be False
    LOKI_ENABLED = all(
        [LOKI_ID != False, LOKI_TOKEN != False, LOKI_URL != False])
    HTTPS_URL = f"https://{LOKI_ID}:{LOKI_TOKEN}@{LOKI_URL}"
    SOURCE = "repair"
    HOST = "repairCafe"


_PROJECT_ROOT = Path(__file__).parent.parent.resolve()


class BaseConfig:
    """Base configuration with common settings."""

    # Flask session secret — must be set via SECRET_KEY env var in production.
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY")

    # Flask
    DEBUG = False
    TESTING = False
    APP_HEADERS = {"Content-type": "application/json"}

    # Database
    HOST = os.environ.get("MYSQL_HOST", "db")
    DB = os.environ.get("MYSQL_DATABASE", "repaircafepage")
    TABLE = "repairs"
    USERNAME = os.environ.get("MYSQL_USER", "root")
    PASSWORD = os.environ.get("MYSQL_PASSWORD", "mariadb")
    DBPORT = "3306"

    # SQLAlchemy
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    # Email
    @property
    def EMAIL_ENABLED(self) -> bool:
        return os.environ.get("EMAIL_ENABLED", "false").lower() in (
            "true",
            "1",
            "yes",
        )

    MAIL_SENDER = os.environ.get("MAIL_SENDER")
    MAIL_SENDER_NAME = os.environ.get("MAIL_SENDER_NAME", "RepairCafe")
    EXPORT_MAIL_RECEIVER = os.environ.get("EXPORT_MAIL_RECEIVER")
    MAIL_TOKEN = os.environ.get("MAIL_TOKEN")
    ZIP_PASSWORD = os.environ.get("ZIP_PASSWORD")

    # Configurable storage and config directories
    # Defaults to <project_root>/data and <project_root>/config for local development;
    # set DATA_DIR=/data and CONFIG_DIR=/config in Docker.
    @property
    def DATA_DIR(self) -> Path:
        return Path(
            os.environ.get("DATA_DIR", str(_PROJECT_ROOT / "data"))
        ).resolve()

    @property
    def CONFIG_DIR(self) -> Path:
        return Path(
            os.environ.get("CONFIG_DIR", str(_PROJECT_ROOT / "config"))
        ).resolve()

    @property
    def IMPORT_EXCEL_PATH(self) -> str:
        return str(self.CONFIG_DIR / "import.xlsx")

    @property
    def SIGNED_PDF_STORAGE_PATH(self) -> str:
        return os.environ.get(
            "SIGNED_PDF_STORAGE_PATH",
            str(self.DATA_DIR / "signed_disclaimers"),
        )

    @property
    def SIGNED_CANCELLATION_STORAGE_PATH(self) -> str:
        return os.environ.get(
            "SIGNED_CANCELLATION_STORAGE_PATH",
            str(self.DATA_DIR / "signed_cancellations"),
        )

    # Public base URL as seen by the browser, e.g. https://reparaturen.repaircafe-hemau.de
    # (behind the TLS-terminating proxy the request scheme is not reliable).
    PUBLIC_URL = os.environ.get("PUBLIC_URL", "").rstrip("/")

    # OIDC login. Enabled when issuer, client id/secret and PUBLIC_URL are set.
    # While enabled, password login is restricted to local admin accounts (break-glass).
    OIDC_ISSUER = os.environ.get("OIDC_ISSUER", "")
    OIDC_CLIENT_ID = os.environ.get("OIDC_CLIENT_ID", "")
    OIDC_CLIENT_SECRET = os.environ.get("OIDC_CLIENT_SECRET", "")
    OIDC_SCOPES = os.environ.get("OIDC_SCOPES", "openid email profile")
    OIDC_PIN_CLAIM = os.environ.get("OIDC_PIN_CLAIM", "pin_code")
    OIDC_ADMIN_CLAIM = os.environ.get("OIDC_ADMIN_CLAIM", "repaircafe_admin")
    OIDC_GROUPS_CLAIM = os.environ.get("OIDC_GROUPS_CLAIM", "groups")
    PIN_MODE = os.environ.get("PIN_MODE", "oidc")
    PIN_MODE_RESET_ACK = os.environ.get("PIN_MODE_RESET_ACK", "")
    OIDC_DENIED_GROUPS = [
        g.strip()
        for g in os.environ.get("OIDC_DENIED_GROUPS", "").split(",")
        if g.strip()
    ]

    # Label printer (CUPS via mounted socket /run/cups/cups.sock)
    LABEL_PRINTER_ENABLED = os.environ.get(
        "LABEL_PRINTER_ENABLED", "false"
    ).lower() in ("true", "1", "yes")
    LABEL_PRINTER_NAME = os.environ.get("LABEL_PRINTER_NAME", "SLP650")

    @property
    def SQLALCHEMY_DATABASE_URI(self):
        # Full URL override, e.g. "sqlite://" for the test suite.
        if os.environ.get("DATABASE_URL"):
            return os.environ["DATABASE_URL"]
        return f"mysql+pymysql://{self.USERNAME}:{self.PASSWORD}@{self.HOST}:{self.DBPORT}/{self.DB}"


class DevelopmentConfig(BaseConfig):
    """Development configuration."""

    DEBUG = True
    PORT = os.environ.get("PORT", "5000")
    TEMPLATES_AUTO_RELOAD = True
    JSONIFY_PRETTYPRINT_REGULAR = True
    DELETE_LOG_OLDERTHANDAYS = "5"
    DELETE_AFTER_TRANSACTION = False
    ENVIRONMENT = "Development"


class ProductionConfig(BaseConfig):
    """Production configuration."""

    PORT = "80"
    DELETE_LOG_OLDERTHANDAYS = "14"
    DELETE_AFTER_TRANSACTION = True


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    flask_env = os.environ.get("FLASK_ENV", "prod").lower()

    if flask_env in ("dev", "development"):
        return DevelopmentConfig()
    elif flask_env in ("prod", "production"):
        return ProductionConfig()
    else:
        print(
            f"Unknown FLASK_ENV value: {flask_env}. Using production config.")
        return ProductionConfig()
