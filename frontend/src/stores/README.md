# Pinia stores

Setup-style stores (`defineStore('id', () => { … })`). Types come from the generated
API client (`@/api/types`, see [`../api/API_TYPES.md`](../api/API_TYPES.md)); all
requests go through `api` from `@/api/client`.

| Store | File | Holds |
|---|---|---|
| `useAuthStore` | `authStore.ts` | current user, admin flag, PIN session (locked, auto-lock, idle timeout), login / logout / lock / unlock |
| `useRepairStore` | `repairStore.ts` | the repair list, auto-refresh, status actions |
| `useUserStore` | `userStore.ts` | users for assignee selects (`userOptions`), loaded once |

Pure status rules (allowed transitions, detail values, colors) are not in a store but
in `@/domain/repairStatus.ts`. Per-repair detail data (logs, VDE tests, attachments) is
loaded by the `useRepairDetail(qrToken)` composable, not stored globally.

## authStore

- `currentUser`, `isAuthenticated`, `isAdmin`
- `isLocked`, `pinSessionEligible`, `pinUnlockAvailable` (false outside the workshop
  network), `autoLockEnabled`, `idleTimeoutSeconds`
- `fetchMe()`, `login()`, `logout()`, `lockSession()`, `unlock(pin)`,
  `recordActivity()`, `setAutoLock(enabled)`
- `markLocked()` / `markSessionEnded()` — called by the API client on 423 / 401
- `canDeleteOwnedBy(ownerId)` — the single ownership rule: admins, or the owner

Idle lock, heartbeats and cross-tab sync are driven by `usePinSession()` in `App.vue`.

## repairStore

The list from `GET /api/list`; every item carries its latest log entry (`latest_log`).

```ts
import { useRepairStore } from '@/stores/repairStore'

const repairStore = useRepairStore()

onMounted(async () => {
  await repairStore.fetchRepairs()
  repairStore.startAutoRefresh()                  // background refresh every 10 s
})
onUnmounted(() => repairStore.stopAutoRefresh())

await repairStore.transitionRepairStatus({
  repairId: repair.id,
  fromStatus: 'Offen',
  toStatus: 'In Bearbeitung',
  user_id: userId,
})
```

**State:** `repairs`, `loading` (only for fetches with `showLoading`), `error`,
`autoRefreshEnabled`, `refreshIntervalMs` (default 10 000).

**Computed:** `openRepairs` (sorted by ID), `inProgressRepairs`, `closedRepairs`,
`repairedRepairs`, `notRepairedRepairs`, the matching `…Count`s, `totalRepairsCount`,
`nextRepair` (open repair with the lowest ID).

**Actions:**

| Action | Does |
|---|---|
| `fetchRepairs(showLoading = true)` | load the list; responses of older fetches are ignored |
| `startAutoRefresh()` / `stopAutoRefresh()` | start / stop the interval |
| `pauseAutoRefresh()` / `resumeAutoRefresh()` | skip refreshes without stopping the interval (e.g. while a dialog is open) |
| `setRefreshInterval(ms)` | change the interval |
| `clear()` | reset everything (logout, user change) |
| `updateRepair(id, updates)` | plain update, then refresh |
| `transitionRepairStatus(input)` | status change with client-side checks (allowed transition, assignee required); reopening from In Bearbeitung clears the assignee |
| `completeSuccessfulRepair(input)` | → Repariert with description and duration |
| `completeFailedRepair(input)` | → Nicht Repariert with detail and reason |
| `getRepairById(id)`, `getRepairByQrToken(token)` | look up in the loaded list |

The backend checks the same rules again and writes the status / assignee log entries
itself.
