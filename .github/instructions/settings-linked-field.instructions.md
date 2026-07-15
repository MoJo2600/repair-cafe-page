---
description: "Use when adding a new FK field on a data model that links to a row in the settings table (e.g. repair_type_id on repairs). Covers the full path: migration → backend model/schema/API → frontend types, creation form, and display/edit card."
applyTo:
  - "app/models.py"
  - "app/schemas.py"
  - "app/api/repairs.py"
  - "app/api/**/*.py"
  - "app/migrations/versions/*.py"
  - "frontend/src/api/generated/data-contracts.ts"
  - "frontend/src/api/services/*.ts"
  - "frontend/src/views/CreateRepairPage.vue"
  - "frontend/src/components/RepairSummaryCard.vue"
---

# Linking a Data Entry to a Settings Row (FK pattern)

Use this pattern when a field on a data model (e.g. `Repair`) should be populated
from a user-managed list stored in the `settings` table — instead of a hardcoded
dropdown or a free-text string.

**Reference implementation:** `repair_type_id` on `Repair`, linking to
`settings` rows where `category = 'repair_type'`.

---

## Overview

```
settings (id, category='repair_type', name='Elektronik', ...)
    ▲
    │ FK (SET NULL on delete)
repairs.repair_type_id
```

The linked `name` is also mirrored into the legacy text column (`reparatur_art`)
for backward compatibility. New code always reads from the FK / relationship.

---

## Step 1 — Migration: add the FK column

Create a new migration in `app/migrations/versions/` (next revision number).
Use `nullable=True` and `ondelete="SET NULL"` so deleting a setting does not
cascade-delete repairs.

```python
# app/migrations/versions/008_repair_type_id.py
import sqlalchemy as sa
from alembic import op

revision = "008"
down_revision = "006"   # ← set to the actual previous revision

def upgrade():
    op.add_column(
        "repairs",
        sa.Column("repair_type_id", sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        "fk_repairs_repair_type_id",
        "repairs", "settings",
        ["repair_type_id"], ["id"],
        ondelete="SET NULL",
    )

def downgrade():
    op.drop_constraint("fk_repairs_repair_type_id", "repairs", type_="foreignkey")
    op.drop_column("repairs", "repair_type_id")
```

---

## Step 2 — Model: add FK column and relationship

```python
# app/models.py  (inside the Repair class, after customer_id)
repair_type_id: Mapped[Optional[int]] = mapped_column(
    db.Integer, db.ForeignKey("settings.id", ondelete="SET NULL"), nullable=True
)

# Relationship
repair_type = db.relationship("Setting", foreign_keys=[repair_type_id])
```

Also add `"repair_type_id": self.repair_type_id` to `to_dict()` so legacy code
that uses the dict representation still exposes the field.

---

## Step 3 — Schemas: add the field to Create / Update / Response

```python
# app/schemas.py

# RepairCreate — required FK, legacy text field becomes optional
class RepairCreate(RepairBase):
    repair_type_id: int = Field(..., description="FK to repair type setting")
    # override reparatur_art to optional; API auto-fills it from the setting name
    reparatur_art: Optional[str] = Field(None, min_length=1, max_length=100)

# RepairUpdate — optional FK
class RepairUpdate(BaseModel):
    repair_type_id: Optional[int] = Field(None, description="FK to repair type setting")
    # ... other fields

# RepairResponse — expose FK + nested object
class RepairResponse(RepairBase):
    repair_type_id: Optional[int] = Field(None, description="FK to repair type setting")
    repair_type: Optional["SettingResponse"] = Field(None, description="Linked repair type setting")
```

`SettingResponse` is already defined in `app/schemas.py`. Forward references are
resolved automatically by Pydantic's model rebuild.

---

## Step 4 — API endpoint: resolve FK and mirror to legacy text field

In the **create** handler, look up the setting and populate the legacy text column:

```python
# app/api/repairs.py — inside api_create_repair, before creating the ORM object
from app.models import Customer, Repair, Setting

repair_type_id = data.get("repair_type_id")
if repair_type_id:
    setting = Setting.query.get(repair_type_id)
    if setting is None:
        return Response(
            json.dumps({"reply": "error", "error": f"repair_type_id {repair_type_id} not found"}),
            status=400, mimetype="application/json",
        )
    data["reparatur_art"] = setting.name   # mirror for backward compat
```

In the **update** handler, sync the legacy column whenever the FK changes:

```python
# inside api_update_repair, after model_dump
if "repair_type_id" in update_data and update_data["repair_type_id"] is not None:
    setting = Setting.query.get(update_data["repair_type_id"])
    if setting:
        update_data["reparatur_art"] = setting.name
```

---

## Step 5 — Frontend types: update data-contracts.ts

Manually edit `frontend/src/api/generated/data-contracts.ts` (auto-generation
may overwrite these — keep them until the OpenAPI spec is regenerated):

```typescript
// In RepairCreate: make legacy field optional, add required FK
reparatur_art?: string          // was: reparatur_art: string
repair_type_id: number          // NEW

// In RepairResponse: add optional FK + nested object
repair_type_id?: number         // NEW
repair_type?: SettingResponse   // NEW

// In RepairUpdate: add optional FK
repair_type_id?: number         // NEW
```

Also update the inline type in `frontend/src/api/services/RepairsService.ts` if
it has its own copy of the create-body shape.

---

## Step 6 — Creation form: load from API, bind to repair_type_id

Replace any hardcoded `categories` array with a reactive list loaded from the
settings API.

```typescript
// Load in onMounted (or alongside other config fetches)
const repairTypes = ref<Array<{ id: number; name: string }>>([])
try {
  const cfg = await ConfigService.getDropdownConfig()
  repairTypes.value = cfg.repair_type ?? []
} catch { repairTypes.value = [] }
```

`ConfigService.getDropdownConfig()` returns
`{ repair_type?: Array<{ id: number; name: string }> }`.

Store **both** the selected id and the name in `formData` so the summary/review
step can display the label without a separate API call:

```typescript
const formData = ref({
  repair_type_id: null as number | null,
  repair_type: null as { id: number; name: string } | null,
  // ... other fields
})

function onRepairTypeChange(id: number | null) {
  const found = repairTypes.value.find((t) => t.id === id) ?? null
  formData.value.repair_type = found
}
```

Template:

```vue
<v-select
  v-model="formData.repair_type_id"
  :items="repairTypes"
  item-value="id"
  item-title="name"
  label="Kategorie"
  :rules="[(v) => !!v || 'Kategorie ist erforderlich']"
  @update:model-value="onRepairTypeChange"
></v-select>
```

Submit payload sends `repair_type_id` (not `reparatur_art`):

```typescript
const repairData = {
  repair_type_id: formData.value.repair_type_id,
  // ... other fields
}
```

---

## Step 7 — Display and edit card (RepairSummaryCard)

**Display:** prefer the FK relationship name, fall back to the legacy text field:

```vue
<div>{{ repairData.repair_type?.name || repairData.reparatur_art }}</div>
```

**Edit dialog:** use an `item-value` / `item-title` select bound to `repair_type_id`:

```typescript
// editForm
const editForm = ref({ repair_type_id: null as number | null, /* other fields */ })

function openEditDialog() {
  editForm.value.repair_type_id = props.repairData.repair_type_id ?? null
  // load list lazily
  if (repairTypes.value.length === 0) {
    ConfigService.getDropdownConfig()
      .then((c) => { if (c.repair_type) repairTypes.value = c.repair_type })
      .catch(() => {})
  }
}
```

```typescript
// saveEdit
await RepairsService.updateRepair(props.repairData.id, {
  repair_type_id: editForm.value.repair_type_id ?? undefined,
  // ... other fields
})
// resolve name locally for immediate UI update
const foundType = repairTypes.value.find((t) => t.id === editForm.value.repair_type_id)
emit('updated', {
  repair_type_id: editForm.value.repair_type_id,
  reparatur_art: foundType?.name ?? props.repairData.reparatur_art ?? '',
  // ... other fields
})
```

**emit type** should include both the FK and the resolved name so parent
components can update the local copy of the repair record without a refetch:

```typescript
const emit = defineEmits<{
  updated: [fields: {
    repair_type_id: number | null
    reparatur_art: string
    // ... other fields
  }]
}>()
```

---

## Checklist

- [ ] Migration file created with correct `down_revision`
- [ ] `python run_migrations.py` executed successfully
- [ ] Model: FK column + relationship added
- [ ] Model: `to_dict()` includes the new FK id
- [ ] Schemas: `repair_type_id` in Create (required), Update (optional), Response (optional + nested object)
- [ ] API: setting looked up and legacy text column mirrored in create + update
- [ ] `data-contracts.ts`: FK field added to all three interfaces
- [ ] `RepairsService.ts` inline type updated if present
- [ ] Creation form: loads from API, no hardcoded list
- [ ] Display uses `repair_type?.name || reparatur_art` fallback
- [ ] Edit dialog binds to FK id and emits resolved name
