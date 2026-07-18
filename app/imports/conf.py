### Parameter-Doc
#   onPi --> Use PI USB for Reading Serial Data; If Not = Testdata
#   OVERRIDE --> ? scheint doppelt gemoppelt zu sein
#   REINIT --> Lösche die DB (Reinitialisiere), nur für Test/Dev!
#
#
#
import os

import yaml
from coolname import generate_slug
from flask.templating import Environment


class lokiConf(object):
    LOKI_ID = os.environ.get("GCLOUD_HOSTED_LOGS_ID", False)
    LOKI_TOKEN = os.environ.get("GCLOUD_PROM_API_KEY", False)
    LOKI_URL = os.environ.get("GCLOUD_HOSTED_LOGS_URL", False)
    # if any of LOKI_ID, LOKI_TOKEN, LOKI_URL is False, LOKI_ENABLED will be False
    LOKI_ENABLED = all([LOKI_ID != False, LOKI_TOKEN != False, LOKI_URL != False])
    HTTPS_URL = f"https://{LOKI_ID}:{LOKI_TOKEN}@{LOKI_URL}"
    SOURCE = "repair"
    HOST = "repairCafe"


class FlaskConfig(object):
    DEBUG = False
    TESTING = False
    APP_HEADERS = {
        "Content-type": "application/json",
    }
    # Dropdown data moved to app factory; placeholders here for attribute presence.
    DROPDOWN_ALL = {}
    DROPDOWN_ART = []
    DROPDOWN_ERG = []
    DROPDOWN_WHO = []


class DBConfig(object):
    HOST = os.environ.get("MYSQL_HOST", "db")
    DB = os.environ.get("MYSQL_DATABASE", "repaircafepage")
    TABLE = "repairs"
    USERNAME = os.environ.get("MYSQL_USER", "root")
    PASSWORD = os.environ.get("MYSQL_PASSWORD", "mariadb")
    DBPORT = "3306"
    IMPORT_EXCEL_PATH = "config/import.xlsx"
    TEST_ROW = {
        "id": "123",
        "datum": "2022-04-01",
        "vorname": "John",
        "nachname": "Doe",
        "telefon": "123456789",
        "email": "john.doe@example.com",
        "geraet_art": "Laptop",
        "defekt_besch": "stumpfes Display",
        "reparatur_ok": 1,
        "din_pruef": 0,
        "reparatur_erg": "ok",
        "reparatur_besch": "gerubbelt",
        "reparateur": "",
        "reparatur_dauer": 15,
        "qr_token": "123456789",
    }
    TEST_TOKEN = "123456789"


class ProdConfig(FlaskConfig, DBConfig):
    PORT = "80"
    DELETE_LOG_OLDERTHANDAYS = "14"
    DELETE_AFTER_TRANSACTION = True
    EMAIL_ENABLED = bool(os.environ.get("EMAIL_ENABLED"))
    MAIL_SENDER = os.environ.get("MAIL_SENDER")
    MAIL_SENDER_NAME = os.environ.get("MAIL_SENDER_NAME")
    EXPORT_MAIL_RECEIVER = os.environ.get("EXPORT_MAIL_RECEIVER")
    ZIP_PASSWORD = os.environ.get("ZIP_PASSWORD")
    MAIL_TOKEN = os.environ.get("MAIL_TOKEN")
    pass


class DevConfig(FlaskConfig, DBConfig):
    PORT = os.environ.get(
        "PORT",
    )
    TEMPLATES_AUTO_RELOAD = True
    JSONIFY_PRETTYPRINT_REGULAR = True
    DELETE_LOG_OLDERTHANDAYS = "5"
    Environment = "Development"
    DELETE_AFTER_TRANSACTION = False
    EMAIL_ENABLED = bool(os.environ.get("EMAIL_ENABLED", False))
    MAIL_SENDER = os.environ.get("MAIL_SENDER")
    MAIL_SENDER_NAME = os.environ.get("MAIL_SENDER_NAME", "RepairCafe")
    EXPORT_MAIL_RECEIVER = os.environ.get("EXPORT_MAIL_RECEIVER")
    ZIP_PASSWORD = os.environ.get("ZIP_PASSWORD")
    MAIL_TOKEN = os.environ.get("MAIL_TOKEN")
    DEBUG = True
