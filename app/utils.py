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
            swagger_schema["properties"][field_name] = _convert_field_schema(
                field_info)

    return swagger_schema


def _definition_ref(pydantic_ref: str) -> str:
    """Pydantic's "#/$defs/Model" -> Swagger 2.0 "#/definitions/Model"."""
    return pydantic_ref.replace("#/$defs/", "#/definitions/")


def _convert_field_schema(field_schema: dict) -> dict:
    """Convert a Pydantic field schema to Swagger format."""
    swagger_field = {}

    # Handle $ref (nested Pydantic model)
    if "$ref" in field_schema:
        return {"$ref": _definition_ref(field_schema["$ref"])}

    # Handle anyOf (Optional[T] or Union types)
    if "anyOf" in field_schema:
        variants = field_schema["anyOf"]
        nullable = any(item.get("type") == "null" for item in variants)
        refs = [item for item in variants if "$ref" in item]
        if refs:
            ref = {"$ref": _definition_ref(refs[0]["$ref"])}
            # Swagger 2.0 ignores siblings of $ref, so wrap it to mark it nullable
            return {"allOf": [ref], "x-nullable": True} if nullable else ref
        non_null = [item for item in variants if item.get("type") != "null"]
        if non_null:
            # Optional[list[T]] etc.: convert the non-null variant fully
            swagger_field.update(_convert_field_schema(non_null[0]))
        if nullable:
            # Swagger 2.0 has no null type; swagger-typescript-api reads x-nullable
            swagger_field["x-nullable"] = True

    # Handle type
    if "type" in field_schema:
        swagger_field["type"] = field_schema["type"]
    if "enum" in field_schema:
        swagger_field["enum"] = field_schema["enum"]

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
