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
    LOKI_ENABLED = all([LOKI_ID != False, LOKI_TOKEN != False, LOKI_URL != False])
    HTTPS_URL = f"https://{LOKI_ID}:{LOKI_TOKEN}@{LOKI_URL}"
    SOURCE = "repair"
    HOST = "repairCafe"


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
    EMAIL_ENABLED = bool(os.environ.get("EMAIL_ENABLED", False))
    MAIL_SENDER = os.environ.get("MAIL_SENDER")
    MAIL_SENDER_NAME = os.environ.get("MAIL_SENDER_NAME", "RepairCafe")
    EXPORT_MAIL_RECEIVER = os.environ.get("EXPORT_MAIL_RECEIVER")
    MAIL_TOKEN = os.environ.get("MAIL_TOKEN")
    ZIP_PASSWORD = os.environ.get("ZIP_PASSWORD")

    # Paths
    IMPORT_EXCEL_PATH = "config/import.xlsx"
    SIGNED_PDF_STORAGE_PATH = os.environ.get(
        "SIGNED_PDF_STORAGE_PATH",
        os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "data",
            "signed_disclaimers",
        ),
    )

    # Label printer
    LABEL_PRINT_METHOD = os.environ.get("LABEL_PRINT_METHOD", "file")
    LABEL_PRINTER_DEVICE = os.environ.get("LABEL_PRINTER_DEVICE", "/dev/usb/lp0")
    LABEL_PRINTER_NAME = os.environ.get("LABEL_PRINTER_NAME", "SLP650")
    LABEL_PRINTER_IP = os.environ.get("LABEL_PRINTER_IP") or None
    LABEL_PRINTER_PORT = int(os.environ.get("LABEL_PRINTER_PORT", "9100"))

    # Test data
    TEST_ROW = {
        "id": "123",
        "datum": "2022-04-01",
        "vorname": "John",
        "nachname": "Doe",
        "telefon": "123456789",
        "email": "john.doe@example.com",
        "geraet_art": "Laptop",
        "defekt_besch": "stumpfes Display",
        "reparatur_art": "Schleifarbeiten",
        "reparatur_sonstiges": "Bärchen",
        "din_pruef": 0,
        "status": "Repariert",
        "status_detail": None,
        "reparatur_besch": "gerubbelt",
        "reparateur": "",
        "reparatur_dauer": 15,
        "qr_token": "123456789",
    }
    TEST_TOKEN = "123456789"

    @property
    def SQLALCHEMY_DATABASE_URI(self):
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
    EMAIL_ENABLED = bool(os.environ.get("EMAIL_ENABLED"))


def get_config():
    """Get configuration based on FLASK_ENV environment variable."""
    flask_env = os.environ.get("FLASK_ENV", "prod").lower()

    if flask_env in ("dev", "development"):
        return DevelopmentConfig()
    elif flask_env in ("prod", "production"):
        return ProductionConfig()
    else:
        print(f"Unknown FLASK_ENV value: {flask_env}. Using production config.")
        return ProductionConfig()
