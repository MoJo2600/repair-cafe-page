# Pydantic + OpenAPI Integration

## Overview

This project uses **Pydantic** models for both request validation and OpenAPI documentation generation, eliminating the need to define schemas twice.

## How It Works

### 1. Define Pydantic Models Once

In `app/schemas.py`, define your data models using Pydantic with all validation rules:

```python
from pydantic import BaseModel, EmailStr, Field

class RepairCreate(BaseModel):
    datum: date = Field(..., description="Date of repair intake")
    vorname: str = Field(..., min_length=1, max_length=100, description="First name")
    nachname: str = Field(..., min_length=1, max_length=100, description="Last name")
    email: Optional[EmailStr] = Field(None, max_length=100, description="Email address")
    # ... more fields
```

### 2. Register Models in Swagger

In `app/extensions.py`, the `init_swagger()` function automatically converts Pydantic models to OpenAPI definitions:

```python
def init_swagger(app):
    from app.utils import pydantic_to_swagger
    from app.schemas import RepairCreate, RepairUpdate, RepairResponse
    
    swagger = Swagger(app, template={
        "swagger": "2.0",
        "info": {...},
        "definitions": {
            "RepairCreate": pydantic_to_swagger(RepairCreate),
            "RepairUpdate": pydantic_to_swagger(RepairUpdate),
            "RepairResponse": pydantic_to_swagger(RepairResponse),
        }
    })
```

### 3. Reference Models in API Documentation

In your API endpoints, use `$ref` to reference the Pydantic models:

```python
@repairs_bp.route('/repairs', methods=['POST'])
@validate_request(RepairCreate)
def api_create_repair(validated_data: RepairCreate):
    """
    Create a new repair record
    ---
    operationId: createRepair
    tags:
      - Repairs
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/RepairCreate'
    responses:
      201:
        description: Repair record created successfully
        schema:
          $ref: '#/definitions/RepairCreateResponse'
    """
    # Your implementation here
```

## Benefits

1. **Single Source of Truth**: Define schema once in Pydantic
2. **Type Safety**: Full type hints and IDE support
3. **Validation**: Automatic request validation using Pydantic
4. **Documentation**: OpenAPI docs generated from the same models
5. **Maintainability**: Changes to models automatically update both validation and docs

## The Conversion Utility

The `pydantic_to_swagger()` function in `app/utils.py` handles the conversion:

- Converts Pydantic JSON Schema to Swagger 2.0 format
- Preserves field descriptions, constraints, and types
- Handles optional fields, arrays, nested objects
- Maintains validation rules (min/max length, patterns, etc.)

## Example: Before vs After

### Before (Duplicated)

```python
class RepairCreate(BaseModel):
    vorname: str = Field(..., min_length=1, max_length=100)

@repairs_bp.route('/repairs', methods=['POST'])
def api_create_repair():
    """
    ---
    parameters:
      - name: body
        schema:
          properties:
            vorname:
              type: string
              minLength: 1
              maxLength: 100
    """
```

### After (Single Definition)

```python
class RepairCreate(BaseModel):
    vorname: str = Field(..., min_length=1, max_length=100)

@repairs_bp.route('/repairs', methods=['POST'])
@validate_request(RepairCreate)
def api_create_repair(validated_data: RepairCreate):
    """
    ---
    parameters:
      - name: body
        schema:
          $ref: '#/definitions/RepairCreate'
    """
```

## Adding New Models

To add a new Pydantic model to the OpenAPI documentation:

1. Define the model in `app/schemas.py`
2. Add it to the `definitions` dict in `app/extensions.py` `init_swagger()`
3. Reference it using `$ref: '#/definitions/YourModel'` in endpoint docs

## Viewing the Documentation

Access the Swagger UI at: `http://localhost:5000/apidocs`

The UI will show all your Pydantic models with their full schemas, including:
- Field types
- Required vs optional fields
- Validation constraints
- Descriptions
- Examples
