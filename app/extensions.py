"""
Flask extensions initialization.
Extensions are initialized here and imported by other modules.
"""

import os

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
    """Enable CORS only for origins listed in CORS_ORIGINS (comma-separated).

    The frontend reaches the API through the Vite dev proxy or nginx (same
    origin), so CORS is off by default. A wildcard combined with credentials
    would let any website make authenticated requests on a user's behalf.
    """
    origins = [
        o.strip() for o in os.environ.get("CORS_ORIGINS", "").split(",") if o.strip()
    ]
    if not origins:
        return
    CORS(
        app,
        resources={
            r"/*": {
                "origins": origins,
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
        AppConfigResponse,
        AuthResponse,
        AuthConfigResponse,
        CustomerResponse,
        CustomerWithRepairCountResponse,
        FeaturesResponse,
        LoginRequest,
        PinStatusResponse,
        PinGenerateRequest,
        PinGeneratedResponse,
        PruefgeraetResponse,
        RepairAttachmentListResponse,
        RepairAttachmentResponse,
        RepairCreate,
        RepairCreateResponse,
        RepairLogCreate,
        RepairLogListResponse,
        RepairLogResponse,
        RepairResponse,
        RepairsTimelinePoint,
        RepairsTimelineResponse,
        RepairUpdate,
        SettingResponse,
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
            "info": {
                "title": "RepairCafe API",
                "description": "API for managing repair records",
                "version": app.config["VERSION"],
            },
            "host": "localhost:" + str(app.config.get("PORT", "5000")),
            "basePath": "/",
            "definitions": {
                "APIResponse": pydantic_to_swagger(APIResponse),
                "AppConfigResponse": pydantic_to_swagger(AppConfigResponse),
                "AuthResponse": pydantic_to_swagger(AuthResponse),
                "AuthConfigResponse": pydantic_to_swagger(AuthConfigResponse),
                "PinStatusResponse": pydantic_to_swagger(PinStatusResponse),
                "PinGenerateRequest": pydantic_to_swagger(PinGenerateRequest),
                "PinGeneratedResponse": pydantic_to_swagger(PinGeneratedResponse),
                "FeaturesResponse": pydantic_to_swagger(FeaturesResponse),
                "LoginRequest": pydantic_to_swagger(LoginRequest),
                "CustomerResponse": pydantic_to_swagger(CustomerResponse),
                "CustomerWithRepairCountResponse": pydantic_to_swagger(
                    CustomerWithRepairCountResponse
                ),
                "PruefgeraetResponse": pydantic_to_swagger(PruefgeraetResponse),
                "RepairCreate": pydantic_to_swagger(RepairCreate),
                "RepairUpdate": pydantic_to_swagger(RepairUpdate),
                "RepairResponse": pydantic_to_swagger(RepairResponse),
                "RepairCreateResponse": pydantic_to_swagger(RepairCreateResponse),
                "RepairAttachmentResponse": pydantic_to_swagger(RepairAttachmentResponse),
                "RepairAttachmentListResponse": pydantic_to_swagger(RepairAttachmentListResponse),
                "RepairsTimelinePoint": pydantic_to_swagger(RepairsTimelinePoint),
                "RepairsTimelineResponse": pydantic_to_swagger(RepairsTimelineResponse),
                "SettingResponse": pydantic_to_swagger(SettingResponse),
                "RepairLogCreate": pydantic_to_swagger(RepairLogCreate),
                "RepairLogResponse": pydantic_to_swagger(RepairLogResponse),
                "RepairLogListResponse": pydantic_to_swagger(RepairLogListResponse),
                "UserResponse": pydantic_to_swagger(UserResponse),
                "VdeTestCreate": pydantic_to_swagger(VdeTestCreate),
                "VdeTestResponse": pydantic_to_swagger(VdeTestResponse),
                "VdeTestListResponse": pydantic_to_swagger(VdeTestListResponse),
                "VdeTestCreateResponse": pydantic_to_swagger(VdeTestCreateResponse),
            },
        },
    )
    return swagger
