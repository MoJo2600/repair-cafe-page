# Pydantic Schemas Documentation

## Overview

The RepairCafe API now uses **Pydantic v2** for request validation and response serialization. This provides:

- **Type safety**: Automatic validation of request data
- **Better error messages**: Clear validation errors with field-level details
- **API documentation**: Self-documenting schemas
- **Data consistency**: Guaranteed data structure across the application

## Schemas

### RepairCreate

Used for creating new repairs via `POST /api/repairs`

**Required fields:**
- `datum` (date): Repair intake date
- `vorname` (str): First name (1-100 chars)
- `nachname` (str): Last name (1-100 chars)
- `reparatur_art` (str): Repair category (1-100 chars)
- `geraet_art` (str): Device type (1-100 chars)

**Optional fields:**
- `telefon` (str): Phone number (max 40 chars)
- `email` (EmailStr): Valid email address (max 100 chars)
- `reparatur_sonstiges` (str): Other repair category (max 100 chars)
- `defekt_besch` (str): Defect description (max 400 chars)
- `unterschrift` (str): Signature image as base64

**Example:**
```python
from schemas import RepairCreate
from datetime import date

repair_data = RepairCreate(
    datum=date(2025, 12, 1),
    vorname="Max",
    nachname="Mustermann",
    reparatur_art="Elektronik",
    geraet_art="Laptop",
    email="max@example.com",
    defekt_besch="Display defekt"
)
```

### RepairUpdate

Used for updating repairs via `PUT /api/repairs/<id>`

**All fields are optional** - only send fields you want to update:
- All fields from RepairCreate
- Additional fields: `unterschrift_haft`, `din_pruef`, `reparatur_erg`, `reparatur_besch`, `reparateur`, `reparatur_dauer`, `reparatur_ok`, `status`

**Status validation:**
- Must be one of: `"Offen"`, `"In Bearbeitung"`, `"Beendet"`

**Example:**
```python
from schemas import RepairUpdate

update_data = RepairUpdate(
    status="In Bearbeitung",
    reparateur="Thomas Schmidt",
    reparatur_dauer=45
)
```

### RepairResponse

Used for API responses containing repair data

Includes all fields from the database model, automatically serialized with proper types.

## API Endpoints with Pydantic

### POST /api/repairs

Create a new repair with automatic validation.

**Request:**
```json
{
  "datum": "2025-12-01",
  "vorname": "Max",
  "nachname": "Mustermann",
  "telefon": "0123456789",
  "email": "max@example.com",
  "reparatur_art": "Elektronik",
  "geraet_art": "Laptop",
  "defekt_besch": "Display shows no image",
  "unterschrift": "data:image/png;base64,..."
}
```

**Success Response (201):**
```json
{
  "reply": "done",
  "id": 123,
  "data": {
    "id": 123,
    "datum": "2025-12-01",
    "vorname": "Max",
    "nachname": "Mustermann",
    ...
  }
}
```

**Validation Error (400):**
```json
{
  "reply": "error",
  "error": "Validation failed",
  "details": [
    "vorname: Field required",
    "email: value is not a valid email address"
  ]
}
```

### PUT /api/repairs/<id>

Update a repair with partial data.

**Request:**
```json
{
  "status": "In Bearbeitung",
  "reparateur": "Thomas Schmidt",
  "reparatur_dauer": 45,
  "reparatur_ok": true
}
```

**Success Response (200):**
```json
{
  "reply": "done",
  "data": {
    "id": 123,
    "status": "In Bearbeitung",
    "reparateur": "Thomas Schmidt",
    ...
  }
}
```

### GET /api/list

List all repairs with validated response serialization.

**Response (200):**
```json
{
  "reply": "done",
  "data": [
    {
      "id": 1,
      "datum": "2025-12-01",
      "vorname": "Max",
      "status": "Offen",
      ...
    }
  ],
  "count": 1
}
```

## Validation Features

### Email Validation

Email addresses are automatically validated:
```python
# ✓ Valid
email="user@example.com"

# ✗ Invalid - raises ValidationError
email="invalid-email"
```

### Status Validation

Status must be one of the allowed values:
```python
# ✓ Valid
status="In Bearbeitung"

# ✗ Invalid - raises ValidationError
status="Unknown Status"
```

### String Length Validation

Fields have max length constraints:
```python
# ✓ Valid
vorname="Max"  # 1-100 chars

# ✗ Invalid - raises ValidationError
vorname=""  # Empty string not allowed for required fields
```

### Date Parsing

Dates are automatically parsed from multiple formats:
```python
# All valid:
datum="2025-12-01"
datum="01.12.2025"
datum="2025-12-01T10:30:00"
```

## Error Handling

The `@validate_request` decorator automatically handles validation errors:

```python
from validation import validate_request
from schemas import RepairCreate

@app.route('/api/repairs', methods=['POST'])
@validate_request(RepairCreate)
def create_repair(validated_data: RepairCreate):
    # validated_data is guaranteed to be valid
    # No need for manual validation!
    repair = Repair.from_dict(validated_data.model_dump())
    db.session.add(repair)
    db.session.commit()
    return {"reply": "done"}
```

## Migration from Manual Validation

**Before (manual validation):**
```python
data = request.get_json()
if not data.get('vorname'):
    return {"error": "vorname required"}, 400
if data.get('email') and '@' not in data['email']:
    return {"error": "invalid email"}, 400
# ... many more checks
```

**After (Pydantic):**
```python
@validate_request(RepairCreate)
def create_repair(validated_data: RepairCreate):
    # All validation done automatically!
    # validated_data is type-safe and guaranteed valid
    pass
```

## Benefits

1. **Less code**: No manual validation logic needed
2. **Type safety**: IDE autocomplete and type checking
3. **Better errors**: User-friendly validation messages
4. **Self-documenting**: Schemas serve as documentation
5. **Consistency**: Same validation everywhere
6. **Maintainability**: Single source of truth for data structure

## Testing

Test schemas in Python:
```python
from schemas import RepairCreate
from datetime import date

# Valid data
repair = RepairCreate(
    datum=date.today(),
    vorname="Max",
    nachname="User",
    reparatur_art="Elektronik",
    geraet_art="Laptop"
)

# Access validated data
print(repair.model_dump())  # Dict
print(repair.model_dump_json())  # JSON string
```

Test invalid data:
```python
from pydantic import ValidationError

try:
    repair = RepairCreate(datum=date.today())  # Missing required fields
except ValidationError as e:
    print(e.errors())
```
