---
description: "Use when adding new dropdown/list configuration categories to the settings table. Covers the full path: migration seed data → backend API → frontend SettingsPage card."
applyTo:
  - "app/models.py"
  - "app/migrations/versions/*.py"
  - "app/api/settings.py"
  - "frontend/src/views/SettingsPage.vue"
---

# Adding a New Settings Category (dropdown list)

Use the `settings` table when the new configuration is a **list of named items** that users can add, reorder, activate, or delete — for example repair types, test devices, or repairer names.

Do **not** use the `settings` table for singleton values (a single org name, a toggle, a URL). Use `app_config` for those instead.

---

## What the `settings` table provides out of the box

Each row has:

| Column | Purpose |
|---|---|
| `category` | String key that groups rows (e.g. `"repair_type"`) |
| `name` | Display value shown in dropdowns |
| `serial_number` | Optional extra string (only used by `test_device`) |
| `sort_order` | Integer controlling display order |
| `is_active` | Hide a row without deleting it |

All CRUD endpoints already exist at `GET/POST /api/settings` and `PUT/DELETE /api/settings/<id>`. You only need to seed initial data and wire up the frontend card.

---

## Step 1 — Seed default rows in the migration

Create a new migration file in `app/migrations/versions/` (next revision number):

```python
# app/migrations/versions/003_seed_my_category.py
import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

def upgrade():
    op.bulk_insert(
        sa.table(
            "settings",
            sa.column("category", sa.String),
            sa.column("name", sa.String),
            sa.column("serial_number", sa.String),
            sa.column("sort_order", sa.Integer),
            sa.column("is_active", sa.Boolean),
        ),
        [
            {"category": "my_category", "name": "Option A", "serial_number": None, "sort_order": 0, "is_active": True},
            {"category": "my_category", "name": "Option B", "serial_number": None, "sort_order": 1, "is_active": True},
        ],
    )

def downgrade():
    op.execute("DELETE FROM settings WHERE category = 'my_category'")
```

---

## Step 2 — Expose the category to the frontend (if needed for dropdowns)

The generic `GET /api/settings` already returns all active settings grouped by category. If the new category only needs to appear in a dropdown elsewhere in the app (not managed on the settings page), no backend change is needed — just read `byCategory('my_category')` on the frontend.

If you need a dedicated typed endpoint (like `GET /api/config/pruefgeraete`), follow the [api-endpoint-schema instructions](api-endpoint-schema.instructions.md).

---

## Step 3 — Add a management card to `SettingsPage.vue`

Copy the pattern from the existing "Reparaturarten" card. For a basic list (no extra column):

```vue
<!-- My Category -->
<v-card class="mb-6">
    <v-card-title class="d-flex align-center justify-space-between">
        <span>My Category Label</span>
        <v-btn size="small" color="primary" prepend-icon="mdi-plus"
            @click="openCreate('my_category')">Hinzufügen</v-btn>
    </v-card-title>
    <v-data-table :headers="headersBasic" :items="byCategory('my_category')"
        :loading="loading" item-value="id" hover density="comfortable">
        <template #item.is_active="{ item }">
            <v-chip :color="item.is_active ? 'success' : 'error'" size="small" variant="tonal">
                {{ item.is_active ? 'Aktiv' : 'Inaktiv' }}
            </v-chip>
        </template>
        <template #item.actions="{ item }">
            <v-btn icon="mdi-pencil" size="small" variant="text" density="compact" @click="openEdit(item)" />
            <v-btn icon="mdi-delete" size="small" variant="text" density="compact" color="error"
                @click="confirmDelete(item)" />
        </template>
    </v-data-table>
</v-card>
```

The existing `openCreate`, `openEdit`, `confirmDelete`, and `headersBasic` script logic in `SettingsPage.vue` handles all categories automatically — no script changes are required for a basic list.

If the category needs an extra column (like `serial_number` for `test_device`), add a new headers constant and use `headersDevice` as a reference.

---

## Checklist

- [ ] Migration file created with correct `revision` / `down_revision` chain
- [ ] Default rows seeded in `upgrade()` and removed in `downgrade()`
- [ ] `SettingsPage.vue` card added
- [ ] `python run_migrations.py` run locally to verify the migration applies cleanly
