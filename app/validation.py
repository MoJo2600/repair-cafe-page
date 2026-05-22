"""
Helper utilities for API validation and error handling
"""

import json
import logging
from functools import wraps

from flask import Response, request
from pydantic import ValidationError

logger = logging.getLogger(__name__)


def parse_request(schema_class):
    """
    Parse and validate request JSON against a Pydantic schema.

    Returns a tuple (model_instance, None) on success or
    (None, error_Response) on failure.

    Usage:
        body, err = parse_request(MySchema)
        if err:
            return err
    """
    try:
        data = request.get_json()
        if data is None:
            return None, Response(
                json.dumps({"reply": "error", "error": "Request body must be JSON"}),
                status=400,
                mimetype="application/json",
            )
        return schema_class(**data), None
    except ValidationError as e:
        errors = [
            f"{' -> '.join(str(x) for x in err['loc'])}: {err['msg']}"
            for err in e.errors()
        ]
        return None, Response(
            json.dumps(
                {"reply": "error", "error": "Validation failed", "details": errors}
            ),
            status=400,
            mimetype="application/json",
        )
    except Exception as e:
        logger.error(f"Unexpected validation error: {e}", exc_info=True)
        return None, Response(
            json.dumps({"reply": "error", "error": str(e)}),
            status=500,
            mimetype="application/json",
        )


def validate_request(schema_class):
    """
    Decorator to validate Flask request JSON against a Pydantic schema

    Usage:
        @app.route('/api/endpoint', methods=['POST'])
        @validate_request(MySchema)
        def my_endpoint(validated_data):
            # validated_data is the Pydantic model instance
            return {"status": "ok"}
    """

    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get JSON data from request
                data = request.get_json()
                if data is None:
                    return Response(
                        json.dumps(
                            {"reply": "error", "error": "Request body must be JSON"}
                        ),
                        status=400,
                        mimetype="application/json",
                    )

                # Validate with Pydantic schema
                validated_data = schema_class(**data)

                # Pass validated data to the route handler
                return f(validated_data, *args, **kwargs)

            except ValidationError as e:
                logger.warning(f"Validation error in {f.__name__}: {e}")
                errors = []
                for error in e.errors():
                    field = " -> ".join(str(x) for x in error["loc"])
                    errors.append(f"{field}: {error['msg']}")

                return Response(
                    json.dumps(
                        {
                            "reply": "error",
                            "error": "Validation failed",
                            "details": errors,
                        }
                    ),
                    status=400,
                    mimetype="application/json",
                )
            except Exception as e:
                logger.error(
                    f"Unexpected error in validation decorator: {e}", exc_info=True
                )
                return Response(
                    json.dumps({"reply": "error", "error": str(e)}),
                    status=500,
                    mimetype="application/json",
                )

        return decorated_function

    return decorator


def serialize_response(data, schema_class=None, status=200):
    """
    Serialize response data using Pydantic schema

    Args:
        data: Data to serialize (dict, model instance, or list)
        schema_class: Pydantic schema class to use for serialization
        status: HTTP status code

    Returns:
        Flask Response object
    """
    try:
        if schema_class:
            if isinstance(data, list):
                # Serialize list of items
                serialized = [
                    schema_class.model_validate(item).model_dump(mode="json")
                    for item in data
                ]
            else:
                # Serialize single item
                serialized = schema_class.model_validate(data).model_dump(mode="json")
        else:
            serialized = data

        return Response(
            json.dumps(serialized), status=status, mimetype="application/json"
        )
    except Exception as e:
        logger.error(f"Error serializing response: {e}", exc_info=True)
        return Response(
            json.dumps({"reply": "error", "error": f"Serialization error: {str(e)}"}),
            status=500,
            mimetype="application/json",
        )
