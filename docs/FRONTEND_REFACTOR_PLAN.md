# Frontend Best-Practices Review & Refactor Plan

Review of `frontend/src` against the `vue-best-practices`, `vue-pinia-best-practices`
and `vue-router-best-practices` skills (2026-11-02).

**Baseline:** all SFCs use `<script setup lang="ts">`, strict TS, `vue-tsc` passes,
eslint 0 errors / 26 warnings (mostly `any`). Routes are lazy-loaded, stores use the
setup style, the router guard uses return values (no `next()`), stores guard against
stale fetches with a revision counter.

## Findings

### Bugs

1. **VDE switch in `RepairCompletionDialog` is usually on when it shouldn't be.**
   `watch(() => isVdeTestMandatory, …, { immediate: true })` watches the computed object,
   not `.value`. It fires once at mount with a truthy value, sets `localNeedsVdeTest = true`
   and never fires again. With a passed last VDE test the switch still shows on, and the
   "mandatory" rule only holds by accident.
2. **Camera keeps running after a dialog closes.** QR scanner (`App.vue`) and the log
   dialog (`LogRepairWorkPage.vue`) only stop the stream via the Cancel button; closing via
   scrim/Esc leaves the camera (and the QR scan loop) running. `LogRepairWorkPage` and
   `CreateRepairPage` don't stop the camera on unmount. In `CreateRepairPage` the camera
   preview never appeared at all: the `<video>` sits behind `v-if="cameraActive"`, but
   `cameraActive` was only set once the video element existed, so the stream was acquired,
   never shown and never stopped.
3. **Stale repair after QR scan on a repair page.** `/edit/:qrToken` loads only in
   `onMounted`; navigating `/edit/a → /edit/b` reuses the component, so data stays stale.
4. **Overview fetches logs N+1 every 10 s.** `RepairsOverview.vue` watches
   `inProgressRepairs`; each auto-refresh replaces the array, so logs are fetched
   sequentially per repair every refresh, and twice on mount.
5. **Raw `fetch()` bypasses 401/423 handling.** Session-expired / locked handling lives in
   the axios `request.ts`; ~15 raw `fetch()` calls (users, attachments, settings uploads,
   `VdeTestsService`, `SettingsService`) skip it.

### Structure

6. **One API client.** Three generators, hand-edited "generated – do not edit" services
   returning `CancelablePromise<any>`, raw `fetch()`, and an unused swagger-typescript-api
   `Api` class. Consolidate into one typed client with a single error / 401 / 423
   interceptor; drop unused generator deps.
7. **`defineModel` in dialogs.** Four dialogs copy props into local refs and sync with
   watchers in both directions (the root cause of bug 1).
8. **One typed toast.** Replace string-key `provide('showToast')` + per-page snackbars
   with a single `useToast()` that pushes onto one `VSnackbarQueue` in `App.vue`
   (rewritten in Vuetify 4 to show several messages at once).
9. **Split `App.vue`.** `useIdleLock()` (activity listeners, timer, BroadcastChannel) and a
   `QrScannerDialog` component owning its cleanup.
10. **Split `LogRepairWorkPage.vue` (~1500 lines).** `useRepairDetail(qrToken)`,
    `useRepairAttachments` and a `LogEntryDialog` component (camera via the existing
    `useCameraStream` from P0).
11. **Status rules out of the store.** Move constants and pure helpers from
    `repairStore.ts` to `domain/repairStatus.ts`. The client writes the `status_change`
    log as a second request in three places — move that into the backend so status
    change + log are atomic.
12. **Smaller items.** ~~`request.ts` mutates `authStore` directly~~ (done in P0:
    `markLocked()` / `markSessionEnded()`); `useRepairThread` should take
    `MaybeRefOrGetter` + `toValue`; `ref<any>` form refs → `useTemplateRef` typed as
    `VForm` from `vuetify/components`; `setTimeout` form resets after dialog close →
    `@after-leave`.
13. **One `SignaturePad` component** with pointer events, replacing the duplicated
    mouse/touch code in `CreateRepairPage` and `AbbruchSignatureDialog`.

### Misc

- `shallowRef` for primitives and `<script>` before `<template>`: apply only in files
  touched anyway.
- Magnifier button in the app bar has no action; `/dashboard` renders `PinLockScreen`.
- Idle lock stays at 60 s (`IDLE_TIMEOUT_MS`), confirmed 2026-11-02.

## Plan

| Phase | Work | Status |
|---|---|---|
| **P0 – bugs** | Items 1–5 | done – needs manual browser check (camera, QR, PIN lock) |
| **Build fixes** | Lockfile + Docker after Dependabot bumps (see below) | done |
| **Vuetify 4** | Upgrade 3.13.7 → 4.3.1 on `feat/vuetify-4` (see below) | done – needs page-by-page browser check |
| **P1 – structure** | Items 8 → 7 → 9 → 13 → 10 (toast first; later steps use it) | done (+ VForm refs and `markLocked` from 12), checked in the browser |
| **UI rework** | Workshop/touch focus (shared PC + tablets); consistent look via docs/STYLEGUIDE.md | done: overview, repair page, app shell, style guide + shared ui components applied to all pages, new repair flow, dashboard / lock screen with PIN keypad, lint rules; checked in the browser |
| **P2 – API layer** | Item 6, item 11 (backend writes the status log); see P2 plan below | done, checked in the browser |
| **P3 – checks** | Vitest + `@vue/test-utils` (status transitions, PIN/idle lock, dialogs) — configure `server.deps.inline: ['vuetify']`; clear `any` warnings; lint rule for SFC block order | open |
| **Housekeeping** | Dependabot: group frontend npm updates into one PR so the lockfile is updated once; run CI on Node 26 like the Docker image | open |

## P0 changes

- **1** `RepairCompletionDialog` uses `defineModel` for `modelValue`, `description`,
  `duration`, `needsVdeTest`; the mandatory-VDE rule is a real watcher on
  `[open, isVdeTestMandatory]`.
- **2** New `composables/useCameraStream.ts` owns the stream, stops it on `stop()` and on
  scope dispose, and discards a `getUserMedia()` that resolves after `stop()`. Used by the
  QR scanner (`App.vue`), the log dialog and `CreateRepairPage`; both dialogs stop the
  camera whenever they close, however they are closed.
- **3** `LogRepairWorkPage` loads via `watch(route.params.qrToken, …, { immediate: true })`,
  resets per-repair state on change and ignores responses for a previous repair.
- **4** `RepairsOverview` fetches logs in parallel, once per store refresh, and drops stale
  results. Still N requests per refresh — the real fix is in P2 (latest log in the list
  response).
- **5** New `api/session.ts` (`handleSessionStatus`, `sessionFetch`) shared by
  `core/request.ts` and every former raw `fetch()`; `authStore` got `markLocked()` /
  `markSessionEnded()` instead of being mutated from outside. `userStore.fetchUsers`
  no longer marks users as loaded on an error response.

## Build fixes

- `frontend/pnpm-lock.yaml` regenerated: separately merged Dependabot PRs left a dangling
  `vite@8.3.5` entry, so `pnpm install --frozen-lockfile` failed.
- `Dockerfile.frontend`: `node:26-alpine` no longer bundles corepack; it is installed via
  npm so pnpm still follows `packageManager`.
- Vite 8, vue-router 5 and `@types/node` 26 needed no code changes.

## Vuetify 4 upgrade

Goal: working app on Vuetify 4 defaults; the look changes and is reworked afterwards.

- `VIconBtn` / `VFileUpload` are core components; labs imports removed.
- VAutocomplete `#item` / `#selection` slots: `item` is the raw item (`item.raw.x` → `item.x`).
- MD2 typography classes no longer exist; all 144 usages mapped with the official table
  (`text-h5` → `text-headline-small`, `text-caption` → `text-body-small`, …).
- VRow: deprecated `dense` / `align` / `justify` → `density="compact"` and
  `align-*` / `justify-*` classes.
- Elevation is 0–5 (PinLockScreen 8 → 5).
- `vite.config.ts`: `optimizeDeps.include` for overlay components (upgrade-guide
  workaround for duplicate `useStack` instances in dev).
- Accepted defaults: no uppercase buttons, gap-based grid, smaller breakpoints, no global
  CSS reset (no raw `<button>`/`<input>` or Sass overrides affected), theme stays `light`.
- Form slot values are unwrapped in v4 (`isValid.value` → `isValid`); not used in our templates.

## P1 changes

- **8** `useToast()` + one `VSnackbarQueue` in `App.vue`; page-local snackbars and
  `provide('showToast')` removed; toasts cleared and hidden while locked.
- **7** `defineModel` in all dialogs; drafts stay local and are sent on confirm. All
  `v-form` refs typed as `VForm`.
- **9** `usePinSession()` (idle lock, heartbeats, cross-tab sync, clearing on lock/user
  change) and `QrScannerDialog`; `App.vue` ~480 → 191 lines.
- **13** `SignaturePad` (pointer events, `v-model` = data URL or null) replaces the
  duplicated canvas code in `CreateRepairPage` and `AbbruchSignatureDialog`.
- **10** `LogRepairWorkPage` ~1470 → 464 lines, now coordinating status transitions, the
  VDE flow and label printing:
  - `useRepairDetail(qrToken)` loads and owns repair, logs, VDE tests, attachments and
    documents (reload on token change, stale responses ignored)
  - `AttachmentsService` (list/upload/delete, document existence) replaces raw `fetch()`
  - `RepairActivityTimeline`, `RepairAttachmentsPanel`, `RepairAssigneeSelect`,
    `LogEntryDialog`, `EditLogDialog`
  - `authStore.canDeleteOwnedBy()` is the single ownership rule
  - deleting a log entry now asks for confirmation (the old confirmation dialog was
    never opened); a failed photo upload after a saved entry is reported as a warning
    instead of "save failed"

## P2 plan (API layer)

Findings (2026-11-03): the backend spec (flasgger, Swagger 2.0, schemas converted from
Pydantic) types only 27 of 52 operations, including none of `GET /api/list`,
`GET /api/repairs/by-token/{token}`, `POST /api/repairs/{id}/logs`, `GET /api/settings`.
The Pydantic→Swagger converter drops nullability and rewrites nested `$ref`s to the
OpenAPI 3 path `#/components/schemas/…`, which doesn't exist in a 2.0 document.

Decisions: stay on Swagger 2.0 (OpenAPI 3 would mean rewriting every docstring); keep
`swagger-typescript-api` (supports 2.0 and `x-nullable`); drop `openapi-typescript-codegen`
(unmaintained, its `core/` + axios), `openapi-typescript` and `axios`.

1. **Backend spec:** converter emits `x-nullable` and `#/definitions/` refs; response
   schemas for all JSON endpoints (binary/redirect ones stay untyped); a script dumps the
   spec without a running server; CI fails when the generated client is out of date.
2. **Backend behavior:** `PUT /api/repairs/{id}` writes the `status_change` /
   `assignee_change` log in the same transaction; `GET /api/list` returns each repair's
   latest log. Tests for both.
3. **Frontend client:** regenerate; one `api` instance with session handling (401/423)
   built in; replace hand-written services with it; delete `core/`, axios and the
   `RepairUpdate` nullability workaround.
4. **Frontend domain:** status constants/helpers from `repairStore.ts` to
   `domain/repairStatus.ts`; remove the client-side log writes; overview uses the
   latest log from the list instead of N requests per refresh.

## P2 changes

- **Spec:** all 66 operations documented with operationIds and typed responses (except
  file downloads, redirects, the 204 health check); nullability (`x-nullable`) and
  Swagger 2.0 refs fixed; `frontend/openapi.json` is dumped by
  `scripts/dump_openapi_spec.py` and checked in CI; contract tests
  (`app/tests/test_api_contract.py`) validate real responses against the schemas.
- **Backend:** status/assignee changes are logged in the same transaction as the
  update; `GET /api/list` includes `latest_log`; fixed log creation without
  `reparatur_dauer` and customer search on SQLite.
- **Frontend:** one generated client (`api` from `api/client.ts`) with 401/423 handling,
  `ApiError` and `asFormData`; hand-written services, `core/`, axios and the extra
  generators removed; status rules in `domain/repairStatus.ts`; overview uses
  `latest_log`. How-to: `frontend/src/api/API_TYPES.md`.
