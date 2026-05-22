/**
 * Composable for using the repair store with common patterns
 * 
 * This composable provides convenient methods for working with the repair store
 * in Vue components, including lifecycle management for auto-refresh.
 */

import { onMounted, onUnmounted } from 'vue'
import { useRepairStore } from '@/stores/repairStore'

interface UseRepairStoreOptions {
  autoRefresh?: boolean
  fetchOnMount?: boolean
}

/**
 * Use repair store with automatic lifecycle management
 * 
 * This composable will:
 * - Initialize the store and fetch repairs on mount
 * - Start auto-refresh on mount
 * - Stop auto-refresh on unmount
 * 
 * Perfect for pages that need live updates (like Dashboard)
 * 
 * @param options Configuration options
 * @param options.autoRefresh Whether to enable auto-refresh (default: true)
 * @param options.fetchOnMount Whether to fetch on mount (default: true)
 * @returns The repair store instance
 */
export function useRepairStoreWithLifecycle(options: UseRepairStoreOptions = {}) {
  const { autoRefresh = true, fetchOnMount = true } = options
  
  const repairStore = useRepairStore()

  onMounted(async () => {
    if (fetchOnMount) {
      await repairStore.fetchRepairs()
    }
    
    if (autoRefresh) {
      repairStore.startAutoRefresh()
    }
  })

  onUnmounted(() => {
    if (autoRefresh) {
      repairStore.stopAutoRefresh()
    }
  })

  return repairStore
}

/**
 * Use repair store without auto-refresh
 * 
 * Perfect for components that just need to read the current state
 * without managing refreshes (e.g., detail pages, modals)
 * 
 * @returns The repair store instance
 */
export function useRepairStoreReadOnly() {
  return useRepairStore()
}

/**
 * Use repair store with manual refresh control
 * 
 * Perfect for list pages where users can manually trigger refresh
 * 
 * @returns Object with store and refresh function
 */
export function useRepairStoreManual() {
  const repairStore = useRepairStore()
  
  const refresh = async () => {
    await repairStore.fetchRepairs()
  }
  
  return {
    repairStore,
    refresh
  }
}
