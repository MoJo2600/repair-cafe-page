# API client and types

The backend describes its API in an OpenAPI (Swagger 2.0) spec, built from the Pydantic
models in `app/schemas.py` and the docstrings of the Flask routes. The frontend client is
generated from that spec, so request and response types always match the backend.

```
app/ (Pydantic + docstrings) ──► frontend/openapi.json ──► src/api/generated/
        python scripts/dump_openapi_spec.py      pnpm generate-api
```

## Using the API

```ts
import { api } from '@/api/client'
import type { Repair } from '@/api/types'

const { data } = await api.getRepairByQrToken({ token })
await api.updateRepair({ id: repair.id }, { status: 'In Bearbeitung', user_id: userId })
```

- Path parameters go in the first argument object, the request body in the second.
- Responses are the backend's envelopes (`{ reply, data, ... }`).
- Failures throw `ApiError` (`status`, parsed `body`; `message` is the backend's `error`).
  Use `errorMessage(err, fallback)` from `@/utils/errors` for toasts.
- 401 and 423 are handled centrally (login / PIN lock screen), see `session.ts`.
- Uploads: wrap the payload in `asFormData(...)` (multiple files, no "undefined" fields).
- Downloads: pass `{ format: 'blob' }` as request params.
- File URLs for links (`<a href>`, `<img src>`) and the PDF existence check live in
  `documents.ts`.

## Changing the API

1. Change the backend (route, Pydantic schema, docstring with `$ref: '#/definitions/...'`;
   register new schemas in `app/extensions.py`).
2. `python scripts/dump_openapi_spec.py` (from the project root, with backend deps;
   no running server or database needed)
3. `pnpm generate-api` (in `frontend/`)
4. Commit `frontend/openapi.json` and `src/api/generated/` together with the change.

CI fails when either file is out of date. `app/tests/test_api_contract.py` checks that
real responses match the declared schemas.
