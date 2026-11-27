---
name: flask-backend-best-practices
description: MUST be used for Flask backend tasks in this repository. Covers Python 3.12, the application factory, Blueprints, Flask-SQLAlchemy, Alembic migrations, Pydantic v2 contracts, Flasgger/OpenAPI, Flask-Login, PIN sessions, services, and pytest.
license: MIT
metadata:
  author: RepairCafePage contributors
  scope: repository
  version: "1.0.0"
---

# Flask Backend Best Practices

Use this skill for all work in `app/`. It defines the repository's backend
conventions; framework-wide defaults do not override them.

## 1. Confirm the backend surface

Before editing, identify the responsible module and read it together with the
nearest tests:

- `app/__init__.py`: application factory, extensions, blueprints, auth guard,
  request hooks, and startup services.
- `app/api/`: JSON Blueprint endpoints.
- `app/auth/`: Flask-Login, OIDC, CSRF, PIN sessions, and authorization
  decorators.
- `app/models.py`: SQLAlchemy ORM models.
- `app/schemas.py`: Pydantic v2 request and response contracts.
- `app/services/`: domain services for PDFs, labels, exports, PINs, and mail.
- `app/migrations/versions/`: Alembic migrations.
- `app/tests/`: pytest coverage using the Flask test client.

Read `docs/ARCHITECTURE.md`, `docs/API.md`, and `docs/DEVELOPMENT.md`. Follow
the applicable `.github/instructions/*.md` file for schema, app-config,
dropdown, or settings-linked-field changes.

## 2. Preserve the architecture

- Keep the Flask application-factory pattern and deferred extension
  initialization.
- Organize routes by existing Blueprint/domain; keep handlers focused on
  boundary validation, service/model coordination, and response serialization.
- Reuse established services instead of embedding file, PDF, mail, label, or
  authentication logic in routes.
- Use Python 3.12 typing and existing SQLAlchemy 2.x mapped-model patterns.
- Avoid broad dependency changes and unrelated cleanup.

## 3. Enforce security and identity rules

Every `/api` endpoint is protected by the global auth/PIN request pipeline
unless intentionally marked `@public_endpoint`.

- Use `@admin_required` for administrator operations.
- Preserve the Flask-Login session-cookie and OIDC model; do not introduce JWT
  authentication.
- Preserve same-origin checks for `POST`, `PUT`, `PATCH`, and `DELETE`.
- Do not bypass PIN-session authorization or the 401/423 response semantics.
- Hash secrets and PINs with the existing services. Never log passwords, PINs,
  cookies, tokens, signatures, or uploaded sensitive content.
- Keep authorization checks in the backend, including object-level ownership
  or role checks.

## 4. Treat Pydantic as the API boundary

For every request or response contract:

1. Define request/response models in `app/schemas.py`.
2. Use `ConfigDict(from_attributes=True)` for ORM-backed response models.
3. Validate request bodies with `@validate_request(...)`.
4. Serialize ORM values with
   `Model.model_validate(value).model_dump(mode="json")`.
5. Register response schemas in `app/extensions.py` for Swagger.
6. Add the required Flasgger `operationId` and schema references to every
   documented successful response.

Do not replace Pydantic with Marshmallow, Flask-RESTful, or flask-smorest.
Preserve the existing `{ "reply": "done", ... }` and
`{ "reply": "error", "error": ... }` JSON envelopes.

## 5. Keep database changes safe

- Change persistent structure with a new Alembic revision; never rewrite an
  existing revision that may have reached production.
- Set `down_revision` to the current migration head and implement both
  `upgrade()` and `downgrade()`.
- Use nullable columns and existing `ON DELETE` behavior when required for safe
  rollout and deletion of user-managed settings.
- Keep multi-step model and log changes in the same transaction.
- Roll back failed database work using the established endpoint/session
  pattern.
- Eager-load relationships for list endpoints when needed; avoid N+1 queries.

## 6. Preserve coupled domain invariants

When changing repair workflows, inspect all coupled state:

- Status transitions and required status details.
- Required assignee/description rules.
- `closed_at` updates.
- Status and assignee log entries.
- Attachment and signed-document cleanup.
- VDE/cancellation behavior.

Repair rules may intentionally be represented in backend schemas, route logic,
and frontend domain code. The backend skill owns and edits only `app/`; report
any required frontend synchronization as a handoff instead of editing it.

## 7. Test observable behavior

Add focused pytest coverage in `app/tests/` for changed behavior. Prefer the
test module nearest the feature and cover:

- happy path;
- validation failure;
- unauthenticated and forbidden access;
- relevant domain invariant;
- OpenAPI/API response contract where applicable.

Use the Flask test client and in-memory SQLite fixtures for normal tests.
Never point migration or PIN concurrency checks at production data.

## 8. Validate before finishing

Run the narrowest applicable checks first:

```bash
python -m pytest app/tests/<relevant_test_file>.py -v
python -m pytest app/tests -v
git diff --check
```

For schema/route changes, verify Flasgger registration and the actual JSON
response shape. For migrations, test the upgrade and downgrade on a disposable
development database. Report any required OpenAPI/frontend regeneration as a
handoff because generated frontend artifacts are outside this skill's write
scope.
