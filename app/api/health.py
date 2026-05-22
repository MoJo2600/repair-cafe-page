"""
Health check API endpoint.
"""
from flask import Blueprint, Response
from app.extensions import db


health_bp = Blueprint('health', __name__)


@health_bp.route('/healthz', methods=['GET'])
def healthcheck():
    """
    Health check endpoint
    ---
    operationId: healthcheck
    tags:
      - Health
    responses:
      204:
        description: Database connection is healthy
      504:
        description: Database connection failed
    """
    try:
        # Try to execute a simple query to check database connectivity
        db.session.execute(db.text('SELECT 1'))
        return Response(status=204)
    except Exception:
        return Response(status=504)
