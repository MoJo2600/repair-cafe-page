---
description: "Use when adding new scalar application configuration values (single strings, booleans, URLs) to the app_config table. Covers the full path: migration seed → backend schema & endpoint → frontend SettingsPage card."
applyTo:
  - "app/models.py"
  - "app/migrations/versions/*.py"
  - "app/api/config.py"
  - "app/schemas.py"
  - "app/extensions.py"
  - "frontend/src/views/SettingsPage.vue"
  - "frontend/src/api/services/ConfigService.ts"
---

# Adding a New App Config Value (scalar key-value)

Use the `app_config` table when the new configuration is a **single value** — a string, URL, boolean flag, etc. — that has exactly one current value at any time.

Do **not** use `app_config` for lists of items that users manage (add/remove/reorder). Use the `settings` table for those instead.

---

## What the `app_config` table provides

| Column | Type | Notes |
|---|---|---|
| `key` | String(100) PK | Stable identifier, never changes |
| `value` | Text | The stored value; always a string (cast on read if needed) |
| `updated_at` | DateTime | Updated automatically on write |

The shared helper `_get_app_config()` in `app/api/config.py` reads all known keys and returns an `AppConfigResponse` with defaults for any missing rows.

---

## Step 1 — Add the key to `AppConfigResponse` and `AppConfigUpdate` in `app/schemas.py`

```python
class AppConfigResponse(BaseModel):
    org_name: str = Field("Repair Café", description="Organisation display name")
    org_website: str = Field("", description="Organisation website URL")
    my_new_key: str = Field("default value", description="What this setting does")

class AppConfigUpdate(BaseModel):
    org_name: Optional[str] = Field(None, max_length=200)
    org_website: Optional[str] = Field(None, max_length=200)
    my_new_key: Optional[str] = Field(None, max_length=200)
```

Both classes must be kept in sync — every key in `AppConfigResponse` must have a corresponding optional field in `AppConfigUpdate`.

---

## Step 2 — Update `_get_app_config()` in `app/api/config.py`

```python
def _get_app_config() -> AppConfigResponse:
    defaults = AppConfigResponse()
    org_name_row = db.session.get(AppConfig, "org_name")
    org_website_row = db.session.get(AppConfig, "org_website")
    my_new_key_row = db.session.get(AppConfig, "my_new_key")
    return AppConfigResponse(
        org_name=org_name_row.value if org_name_row else defaults.org_name,
        org_website=org_website_row.value if org_website_row else defaults.org_website,
        my_new_key=my_new_key_row.value if my_new_key_row else defaults.my_new_key,
    )
```

Also extend `update_app_config()` with the corresponding upsert block:

```python
if body.my_new_key is not None:
    row = db.session.get(AppConfig, "my_new_key")
    if row:
        row.value = body.my_new_key
        row.updated_at = now
    else:
        db.session.add(AppConfig(key="my_new_key", value=body.my_new_key, updated_at=now))
```

---

## Step 3 — Seed the default value in a migration

```python
# app/migrations/versions/003_seed_my_new_key.py
import sqlalchemy as sa
from alembic import op

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None

def upgrade():
    op.bulk_insert(
        sa.table(
            "app_config",
            sa.column("key", sa.String),
            sa.column("value", sa.Text),
        ),
        [{"key": "my_new_key", "value": "default value"}],
    )

def downgrade():
    op.execute("DELETE FROM app_config WHERE key = 'my_new_key'")
```

Seeding the default in the migration is optional but recommended so existing deployments get a sensible value without requiring a manual admin action.

---

## Step 4 — Update the frontend type in `data-contracts.ts` and `types.ts`

Add the field to `AppConfigResponse` in `frontend/src/api/generated/data-contracts.ts`:

```typescript
export interface AppConfigResponse {
  /** @default "Repair Café" */
  org_name: string;
  /** @default "" */
  org_website: string;
  /**
   * What this setting does
   * @default "default value"
   */
  my_new_key: string;
}
```

`AppConfigResponse` is already exported from `frontend/src/api/types.ts` — no change needed there.

---

## Step 5 — Add a field to the Organisation card in `SettingsPage.vue`

Add the new field to `orgForm` and the template. The existing `loadOrgConfig` / `saveOrg` functions in `SettingsPage.vue` will pick it up automatically because they spread the full `AppConfigResponse`.

```vue
<v-text-field v-model="orgForm.my_new_key" label="My New Setting"
    variant="outlined" density="comfortable" hide-details="auto" />
```

```typescript
const orgForm = ref({ org_name: '', org_website: '', my_new_key: '' })
```

---

## Checklist

- [ ] Field added to `AppConfigResponse` (with default) and `AppConfigUpdate` (optional) in `app/schemas.py`
- [ ] `_get_app_config()` reads the new key with fallback to default
- [ ] `update_app_config()` upserts the new key
- [ ] Migration created to seed the default value
- [ ] `frontend/src/api/generated/data-contracts.ts` `AppConfigResponse` interface updated
- [ ] `SettingsPage.vue` `orgForm` ref and template updated
- [ ] `python run_migrations.py` run locally to verify the migration applies cleanly
