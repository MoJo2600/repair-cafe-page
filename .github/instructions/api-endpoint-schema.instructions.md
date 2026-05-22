---
description: "Use when creating or modifying API endpoints, Pydantic schemas, or frontend API service files. Enforces the strict schema-first pattern: all endpoint responses must have a Pydantic schema registered in the OpenAPI spec so frontend types can be code-generated. Never inline interface definitions for API data shapes."
applyTo:
  - "app/api/**/*.py"
  - "app/schemas.py"
  - "app/extensions.py"
  - "frontend/src/api/services/*.ts"
  - "frontend/src/api/types.ts"
---

# API Endpoint Schema Pattern

Every new endpoint **must** follow all four steps below. There are no exceptions.

---

## Step 1 — Define a Pydantic schema in `app/schemas.py`

One schema per response shape. Use `ConfigDict(from_attributes=True)` for ORM-backed schemas.

```python
# app/schemas.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class WidgetResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    model_config = ConfigDict(from_attributes=True)

# For list/paginated responses, wrap in APIResponse:
class WidgetListResponse(APIResponse):
    data: list[WidgetResponse] = []
```

**Rules:**
- Request bodies: `class WidgetCreate(BaseModel)` (no `from_attributes`)
- Response bodies that hold ORM objects: always `ConfigDict(from_attributes=True)`
- For `Optional[SomeModel]` fields, just use `Optional[SomeModel]` — the `$ref` rewriting in `pydantic_to_swagger` handles it correctly

---

## Step 2 — Register the schema in `app/extensions.py`

Add the new class to the import and to the `schemas` dict inside `init_swagger()`.

```python
# app/extensions.py — imports block
from app.schemas import (
    ...
    WidgetResponse,       # add here
    WidgetListResponse,   # add here
)

# inside init_swagger(), schemas dict:
schemas = {
    ...
    "WidgetResponse": pydantic_to_swagger(WidgetResponse),
    "WidgetListResponse": pydantic_to_swagger(WidgetListResponse),
}
```

---

## Step 3 — Use the schema in the endpoint

Serialize with `.model_validate(orm_obj).model_dump(mode="json")`. Reference the schema in the Flasgger YAML docstring.

```python
# app/api/widgets.py
from app.schemas import WidgetResponse, WidgetListResponse

@widgets_bp.route("/widgets", methods=["GET"])
def api_list_widgets():
    """
    List all widgets
    ---
    operationId: listWidgets
    tags:
      - Widgets
    responses:
      200:
        description: List of widgets
        schema:
          $ref: '#/components/schemas/WidgetListResponse'
      500:
        description: Internal Server Error
    """
    widgets = Widget.query.all()
    data = [WidgetResponse.model_validate(w).model_dump(mode="json") for w in widgets]
    return Response(
        WidgetListResponse(reply="done", data=data).model_dump_json(),
        status=200, mimetype="application/json",
    )
```

**Docstring rules:**
- `operationId` is required (used as the TypeScript method name after code-gen)
- Every `200` response must have `schema: $ref: '#/components/schemas/XxxResponse'`
- Error responses (`400`, `404`, `500`) do not need a schema ref

---

## Step 4 — Regenerate frontend types and re-export

After backend changes are deployed or the dev server is running:

```bash
cd frontend && pnpm run generate-api
```

Then add new types to `frontend/src/api/types.ts`:

```typescript
export type {
  ...
  WidgetResponse,        // add here
  WidgetListResponse,    // add here
} from "./generated/data-contracts";
```

---

## Frontend: consuming the types

**Always** import from `@/api/types`. **Never** write an inline interface for an API response shape.

```typescript
// ✅ Correct
import type { WidgetResponse } from '@/api/types'
const widgets = ref<WidgetResponse[]>([])

// ❌ Wrong — inline interface duplicates backend contract
interface Widget { id: number; name: string }
const widgets = ref<Widget[]>([])
```

UI-only state (form data, dialog state) is exempt — local interfaces are fine for data that never comes from the API:

```typescript
// ✅ Fine — purely client-side form state, not an API type
interface WidgetFormData {
  name: string          // always string, never null, for v-model binding
  description: string
}
```

---

## Checklist

Before marking a new endpoint as done:

- [ ] Schema class added to `app/schemas.py`
- [ ] Schema registered in `app/extensions.py` `init_swagger()` dict
- [ ] Endpoint uses `.model_validate().model_dump(mode="json")` for serialization
- [ ] Docstring has `schema: $ref: '#/components/schemas/XxxResponse'` on every 200 response
- [ ] `pnpm run generate-api` has been run
- [ ] New types added to `frontend/src/api/types.ts` exports
- [ ] Frontend code uses the generated type, not an inline interface
