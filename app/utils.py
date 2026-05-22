"""
Utility functions for the application.
"""

from typing import Type, get_args, get_origin

from pydantic import BaseModel


def pydantic_to_swagger(model: Type[BaseModel]) -> dict:
    """
    Convert a Pydantic model to a Swagger/OpenAPI schema definition.

    Args:
        model: Pydantic model class

    Returns:
        Dictionary with OpenAPI schema definition
    """
    schema = model.model_json_schema()

    # Convert Pydantic schema format to Swagger 2.0 format
    swagger_schema = {
        "type": "object",
        "properties": {},
    }

    if "required" in schema:
        swagger_schema["required"] = schema["required"]

    if "properties" in schema:
        for field_name, field_info in schema["properties"].items():
            swagger_schema["properties"][field_name] = _convert_field_schema(field_info)

    return swagger_schema


def _convert_field_schema(field_schema: dict) -> dict:
    """Convert a Pydantic field schema to Swagger format."""
    swagger_field = {}

    # Handle $ref (nested Pydantic model) — rewrite Pydantic $defs path to OpenAPI components path
    if "$ref" in field_schema:
        ref = field_schema["$ref"].replace("#/$defs/", "#/components/schemas/")
        return {"$ref": ref}

    # Handle anyOf (Optional[T] or Union types)
    if "anyOf" in field_schema:
        # Optional[SomeModel] produces anyOf: [{$ref: ...}, {type: null}]
        refs = [item for item in field_schema["anyOf"] if "$ref" in item]
        if refs:
            ref = refs[0]["$ref"].replace("#/$defs/", "#/components/schemas/")
            return {"$ref": ref}
        types = [item.get("type") for item in field_schema["anyOf"] if "type" in item]
        if types:
            swagger_field["type"] = types[0]

    # Handle type
    if "type" in field_schema:
        swagger_field["type"] = field_schema["type"]

    # Handle format (e.g., date, email)
    if "format" in field_schema:
        swagger_field["format"] = field_schema["format"]

    # Handle description
    if "description" in field_schema:
        swagger_field["description"] = field_schema["description"]

    # Handle string constraints
    if "minLength" in field_schema:
        swagger_field["minLength"] = field_schema["minLength"]
    if "maxLength" in field_schema:
        swagger_field["maxLength"] = field_schema["maxLength"]
    if "pattern" in field_schema:
        swagger_field["pattern"] = field_schema["pattern"]

    # Handle number constraints
    if "minimum" in field_schema:
        swagger_field["minimum"] = field_schema["minimum"]
    if "maximum" in field_schema:
        swagger_field["maximum"] = field_schema["maximum"]

    # Handle default
    if "default" in field_schema:
        swagger_field["default"] = field_schema["default"]

    # Handle arrays — recurse into items (preserves $ref for typed arrays)
    if "items" in field_schema:
        swagger_field["items"] = _convert_field_schema(field_schema["items"])

    return swagger_field
