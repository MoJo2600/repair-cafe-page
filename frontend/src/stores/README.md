# Pinia Stores

This directory contains Pinia stores for state management in the application.

## Repair Store

The `repairStore.ts` manages the state of repairs across the application.

### Type Definitions

The store uses **auto-generated types** from `/frontend/src/api/generated/`, which are automatically created from the backend Pydantic schemas using `swagger-typescript-api`. This ensures perfect type consistency between frontend and backend.

To regenerate types after backend changes:
```bash
npm run generate-api
```

Available types:
- `Repair` / `RepairResponse` - Full repair object
- `RepairCreate` - For creating new repairs
- `RepairUpdate` - For updating existing repairs
- `RepairListResponse` - API list response format

### Features

- **Auto-refresh**: Automatically refreshes repair data in the background every 10 seconds (configurable)
- **Centralized state**: All components can access the same repair data
- **Reactive updates**: Changes to repairs automatically update all components using the store
- **Performance**: Background refreshes don't show loading spinners to avoid UI flicker

### Usage

```typescript
import { useRepairStore } from '@/stores/repairStore'

// In your component
const repairStore = useRepairStore()

// Access reactive data
console.log(repairStore.nextRepair)
console.log(repairStore.openRepairsCount)
console.log(repairStore.openRepairs)

// Manually fetch repairs
await repairStore.fetchRepairs()

// Start auto-refresh (typically in onMounted)
repairStore.startAutoRefresh()

// Stop auto-refresh (typically in onUnmounted)
repairStore.stopAutoRefresh()

// Pause/resume auto-refresh without stopping the interval
repairStore.pauseAutoRefresh()
repairStore.resumeAutoRefresh()

// Change refresh interval (in milliseconds)
repairStore.setRefreshInterval(5000) // 5 seconds

// Update a repair
await repairStore.updateRepair(repairId, { status: 'In Bearbeitung' })

// Find specific repairs
const repair = repairStore.getRepairById(123)
const repair = repairStore.getRepairByQrToken('token123')
```

### Available State

- `repairs`: Array of all repairs
- `loading`: Boolean indicating if data is being loaded
- `error`: Error message if fetch failed
- `autoRefreshEnabled`: Boolean indicating if auto-refresh is enabled
- `refreshIntervalMs`: Current refresh interval in milliseconds

### Available Computed Properties

- `openRepairs`: Array of repairs with status 'Offen', sorted by ID
- `inProgressRepairs`: Array of repairs with status 'In Bearbeitung'
- `closedRepairs`: Array of repairs with status 'Repariert' or 'Nicht Repariert'
- `openRepairsCount`: Number of open repairs
- `inProgressRepairsCount`: Number of in-progress repairs
- `closedRepairsCount`: Number of closed repairs
- `nextRepair`: The next open repair (lowest ID)

### Available Actions

- `fetchRepairs(showLoading = true)`: Fetch repairs from API
- `startAutoRefresh()`: Start automatic refresh interval
- `stopAutoRefresh()`: Stop automatic refresh interval
- `pauseAutoRefresh()`: Temporarily pause refresh without clearing interval
- `resumeAutoRefresh()`: Resume paused auto-refresh
- `setRefreshInterval(intervalMs)`: Change refresh interval
- `updateRepair(id, updates)`: Update a repair and refresh the list
- `getRepairById(id)`: Find repair by ID
- `getRepairByQrToken(qrToken)`: Find repair by QR token

### Example: Using in Multiple Components

The beauty of Pinia is that multiple components can share the same state. Once you initialize the store in one component (like Dashboard), other components can access the same data without additional API calls:

```vue
<!-- OtherComponent.vue -->
<template>
  <div>
    <h3>Next Repair: {{ repairStore.nextRepair?.id }}</h3>
    <p>Open Repairs: {{ repairStore.openRepairsCount }}</p>
  </div>
</template>

<script setup lang="ts">
import { useRepairStore } from '@/stores/repairStore'

const repairStore = useRepairStore()
// No need to fetch - data is already managed by Dashboard
</script>
```

### Benefits Over Previous Approach

1. **No Page Reload**: Updates happen in the background without full page reload
2. **Better UX**: Loading states only show on initial load, not on every refresh
3. **Shared State**: Multiple components can use the same data
4. **Better Performance**: Single source of truth, less API calls
5. **Easier Testing**: State management is separate from components
6. **More Control**: Easy to pause/resume/adjust refresh behavior
