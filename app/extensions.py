"""
Flask extensions initialization.
Extensions are initialized here and imported by other modules.
"""

import flask_login
from apscheduler.schedulers.background import BackgroundScheduler
from flasgger import Swagger
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

# Initialize extensions without app binding
db = SQLAlchemy()
migrate = Migrate()
login_manager = flask_login.LoginManager()
scheduler = BackgroundScheduler()


def init_cors(app):
    """Initialize CORS with configuration."""
    CORS(
        app,
        resources={
            r"/*": {
                "origins": "*",
                "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                "allow_headers": ["Content-Type", "Authorization"],
                "supports_credentials": True,
            }
        },
    )


def init_swagger(app):
    """Initialize Swagger documentation with Pydantic models."""
    from app.schemas import (
        APIResponse,
        CustomerResponse,
        CustomerWithRepairCountResponse,
        PruefgeraetResponse,
        RepairCreate,
        RepairCreateResponse,
        RepairLogCreate,
        RepairLogListResponse,
        RepairLogResponse,
        RepairResponse,
        RepairUpdate,
        UserResponse,
        VdeTestCreate,
        VdeTestCreateResponse,
        VdeTestListResponse,
        VdeTestResponse,
    )
    from app.utils import pydantic_to_swagger

    swagger = Swagger(
        app,
        template={
            "openapi": "3.0.0",
            "info": {
                "title": "RepairCafe API",
                "description": "API for managing repair records",
                "version": app.config["VERSION"],
            },
            "servers": [
                {
                    "url": "http://localhost:" + str(app.config.get("PORT", "5000")),
                    "description": "Development server",
                }
            ],
            "components": {
                "schemas": {
                    "APIResponse": pydantic_to_swagger(APIResponse),
                    "CustomerResponse": pydantic_to_swagger(CustomerResponse),
                    "CustomerWithRepairCountResponse": pydantic_to_swagger(
                        CustomerWithRepairCountResponse
                    ),
                    "PruefgeraetResponse": pydantic_to_swagger(PruefgeraetResponse),
                    "RepairCreate": pydantic_to_swagger(RepairCreate),
                    "RepairUpdate": pydantic_to_swagger(RepairUpdate),
                    "RepairResponse": pydantic_to_swagger(RepairResponse),
                    "RepairCreateResponse": pydantic_to_swagger(RepairCreateResponse),
                    "RepairLogCreate": pydantic_to_swagger(RepairLogCreate),
                    "RepairLogResponse": pydantic_to_swagger(RepairLogResponse),
                    "RepairLogListResponse": pydantic_to_swagger(RepairLogListResponse),
                    "UserResponse": pydantic_to_swagger(UserResponse),
                    "VdeTestCreate": pydantic_to_swagger(VdeTestCreate),
                    "VdeTestResponse": pydantic_to_swagger(VdeTestResponse),
                    "VdeTestListResponse": pydantic_to_swagger(VdeTestListResponse),
                    "VdeTestCreateResponse": pydantic_to_swagger(VdeTestCreateResponse),
                }
            },
        },
    )
    return swagger
