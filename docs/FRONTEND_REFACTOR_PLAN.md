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
   with a single `useToast()` (InjectionKey or small store).
9. **Split `App.vue`.** `useIdleLock()` (activity listeners, timer, BroadcastChannel) and a
   `QrScannerDialog` component owning its cleanup.
10. **Split `LogRepairWorkPage.vue` (~1500 lines).** `useRepairDetail(qrToken)`,
    `useRepairAttachments`, `useCameraCapture` (shared with `CreateRepairPage`) and a
    `LogEntryDialog` component.
11. **Status rules out of the store.** Move constants and pure helpers from
    `repairStore.ts` to `domain/repairStatus.ts`. The client writes the `status_change`
    log as a second request in three places — move that into the backend so status
    change + log are atomic.
12. **Smaller items.** `request.ts` mutates `authStore` directly → store actions
    (`markLocked()`, `markLoggedOut()`); `useRepairThread` should take
    `MaybeRefOrGetter` + `toValue`; `ref<any>` form refs → `useTemplateRef` with `VForm`;
    `setTimeout` form resets after dialog close → `@after-leave`.
13. **One `SignaturePad` component** with pointer events, replacing the duplicated
    mouse/touch code in `CreateRepairPage` and `AbbruchSignatureDialog`.

### Misc

- `shallowRef` for primitives and `<script>` before `<template>`: apply only in files
  touched anyway.
- Magnifier button in the app bar has no action; `/dashboard` renders `PinLockScreen`.
- Idle lock is 60 s (`IDLE_TIMEOUT_MS`) while the go-live plan states 30 s — confirm.

## Plan

| Phase | Work | Status |
|---|---|---|
| **P0 – bugs** | Items 1–5 | done – needs manual browser check (camera, QR, PIN lock) |
| **P1 – structure** | Items 7, 8, 9, 13, then 10 | open |
| **P2 – API layer** | Item 6, item 11 (backend writes the status log) | open |
| **P3 – checks** | Vitest + `@vue/test-utils` (status transitions, PIN/idle lock, dialogs); clear `any` warnings; lint rule for SFC block order | open |

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
