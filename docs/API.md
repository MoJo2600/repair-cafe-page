# API

The backend is a JSON API under `/api`. The full, typed description is the OpenAPI
(Swagger 2.0) spec, committed as [`frontend/openapi.json`](../frontend/openapi.json)
and browsable in development at http://localhost:5000/apidocs/. This page gives the
conventions and an overview.

## Conventions

**Authentication.** Session cookie (HTTP-only). Every endpoint requires login unless
listed as *public* below. Admin endpoints return 403 for other users. A locked PIN
session gets 423 on everything except the PIN session endpoints. Details:
[ARCHITECTURE.md](ARCHITECTURE.md#request-pipeline).

**Same origin.** `POST`, `PUT`, `PATCH` and `DELETE` from another origin are rejected
with 403.

**Envelope.** JSON responses are wrapped:

```json
{ "reply": "done", "data": { … } }
{ "reply": "done", "data": [ … ], "count": 12 }
{ "reply": "error", "error": "Validation failed", "details": ["vorname: Field required"] }
```

**Validation.** Request bodies are Pydantic models from `app/schemas.py`, applied
with `@validate_request`. Invalid bodies return 400 with `details`; violated business
rules (e.g. an invalid status transition) return 400 or 422 with a German `error`
message meant for the UI.

**Dates** are ISO strings (`2026-11-24`, `2026-11-24T16:09:00`).

## Endpoints

### Auth

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/auth/config` | public | login options (password, SSO) |
| POST | `/api/auth/login` | public | password login |
| GET | `/api/auth/oidc/login` | public | start SSO (redirect) |
| GET | `/api/auth/oidc/callback` | public | SSO callback |
| GET | `/api/auth/me` | login | current user |
| POST | `/api/auth/logout` | login | log out |
| GET / POST | `/api/auth/me/pin` | login | PIN status / generate or replace PIN (local mode) |
| GET | `/api/auth/pin-session` | session | lock state of this browser session |
| POST | `/api/auth/pin-session/lock` | session | lock |
| POST | `/api/auth/pin-session/unlock` | session | switch to the helper with this PIN |
| POST | `/api/auth/pin-session/activity` | session | activity heartbeat (idle lock) |
| PUT | `/api/auth/pin-session/auto-lock` | login | switch idle lock on/off for this session |
| GET | `/api/auth/pin-session/dashboard` | session | dashboard figures for the lock screen |

*session* = needs a primary login, also works while locked.

### Repairs

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/list` | login | all repairs, each with its latest log entry |
| POST | `/api/repairs` | login | create (intake, optional signature) |
| GET | `/api/repairs/by-token/<token>` | login | repair by QR token |
| PUT | `/api/repairs/<id>` | login | update; status rules in [ARCHITECTURE.md](ARCHITECTURE.md#repair-status-model) |
| DELETE | `/api/repairs/<id>` | admin | delete with all files |
| GET / POST | `/api/repairs/<id>/disclaimer` | login | download / upload signed waiver PDF |
| GET / POST | `/api/repairs/<id>/cancellation` | login | download / sign or upload cancellation PDF |
| POST | `/api/repairs/<id>/print-label` | login | print the QR label (if enabled) |
| GET | `/api/repairs/stats/timeline` | login | repairs per week and status, last 12 months |

### Logs, attachments, VDE tests

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET / POST | `/api/repairs/<id>/logs` | login | list / add work log entries |
| GET / PUT / DELETE | `/api/repairs/<id>/logs/<log_id>` | login | one entry |
| GET / POST | `/api/repairs/<id>/attachments` | login | list / upload files (`attachment_type`: `device_photo`, `log_entry`, `disclaimer`, `cancellation`, `misc`) |
| GET / DELETE | `/api/repairs/<id>/attachments/<attachment_id>` | login | download; owners can delete ordinary attachments, only admins can delete `disclaimer` or `cancellation` documents |
| GET / POST | `/api/repairs/<id>/vde-tests` | login | list / record VDE tests |
| GET | `/api/repairs/<id>/vde-tests/<test_id>` | login | one test |
| GET | `/api/repairs/<id>/vde-tests/<test_id>/pdf` | login | Prüfprotokoll PDF |

### Customer documents

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/document-templates` | admin | list the fixed `disclaimer` and `cancellation` templates |
| GET / PUT | `/api/document-templates/<id>` | admin | read or rename a template |
| POST | `/api/document-templates/<id>/versions` | admin | create an immutable draft version |
| POST | `/api/document-templates/<id>/versions/<version_id>/publish` | admin | publish and activate a version |
| POST | `/api/document-templates/<id>/preview` | login | render an HTML preview with a pinned version |
| POST | `/api/document-templates/<id>/render` | login | render a PDF with a pinned published version |
| POST | `/api/settings/document-templates/<id>/blank-print` | login | render a blank PDF without storing an attachment |

Template HTML is sanitized server-side. Only the documented WYSIWYG placeholders
(`customer_name`, `customer_first_name`, `customer_last_name`, `customer_phone`,
`customer_email`, `date`, `repair_number`, `repair_type`, `device`,
`defect_description`, `signature`, `template_version`) are accepted. Rendered customer
values are HTML-escaped, and the server adds the template title and version footer.
The two fixed `disclaimer` and `cancellation` template roles cannot be deleted.

### Customers and users

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET / POST | `/api/customers` | login | list (with repair counts) / create |
| GET | `/api/customers/search?q=` | login | search by name, phone, e-mail |
| GET / PUT | `/api/customers/<id>` | login | read / update |
| DELETE | `/api/customers/<id>` | admin | delete (repairs keep, unlinked) |
| GET | `/api/users`, `/api/users/<id>` | login | list / read |
| POST, PUT, DELETE | `/api/users`, `/api/users/<id>` | admin | create / update / deactivate |

### Settings and configuration

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/settings` | login | active dropdown values by category |
| GET | `/api/settings/all` | admin | all values incl. inactive |
| POST, PUT, DELETE | `/api/settings`, `/api/settings/<id>` | admin | manage values |
| GET | `/api/config/dropdowns`, `/api/config/pruefgeraete` | login | dropdown data, test devices |
| GET / PUT | `/api/config/app-config` | login / admin | organisation name, website, app URL |
| GET | `/api/config/features` | login | feature flags (e.g. label printer enabled) |
| GET / POST | `/api/config/disclaimer`, `/api/config/cancellation` | login / admin | PDF templates |
| GET / POST | `/api/config/logo` | public / admin | logo |
| GET / POST / DELETE | `/api/config/celebration-sound` | public / admin | success sound (MP3) |

### Statistics, export, health

| Method | Path | Access | Purpose |
|---|---|---|---|
| GET | `/api/stat-data/<type>` | login | chart data |
| GET | `/api/export` | admin | all repairs as XLSX |
| GET | `/api/mailexport` | admin | send the CSV export by e-mail (needs `EMAIL_ENABLED`) |
| GET | `/api/healthz` | public | health check |

`/api/export` and `/api/mailexport` are not in the OpenAPI spec and have no button in
the UI yet.

## Generated client

The frontend never writes request code by hand; it uses a client generated from the
spec:

```bash
python scripts/dump_openapi_spec.py     # app → frontend/openapi.json (no server or database needed)
cd frontend && pnpm generate-api        # openapi.json → src/api/generated/
```

Commit both together with the backend change; CI fails if they are out of date.
Usage in the frontend and the full workflow:
[`frontend/src/api/API_TYPES.md`](../frontend/src/api/API_TYPES.md). Steps for a new
endpoint: [DEVELOPMENT.md](DEVELOPMENT.md#adding-or-changing-an-endpoint).

### How the spec is built

Schemas are defined once, in Pydantic (`app/schemas.py`). `init_swagger()` in
`app/extensions.py` converts each registered model to a Swagger definition with
`pydantic_to_swagger()` (`app/utils.py`), keeping types, constraints, descriptions and
nullability (`x-nullable`). Route docstrings reference them:

```python
@repairs_bp.route("/repairs", methods=["POST"])
@validate_request(RepairCreate)
def api_create_repair(validated_data: RepairCreate):
    """
    Create a new repair record
    ---
    operationId: createRepair
    tags: [Repairs]
    parameters:
      - name: body
        in: body
        required: true
        schema:
          $ref: '#/definitions/RepairCreate'
    responses:
      201:
        schema:
          $ref: '#/definitions/RepairCreateResponse'
    """
```

`app/tests/test_api_contract.py` checks real responses against these schemas.
