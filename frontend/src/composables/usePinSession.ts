import { computed, onScopeDispose, shallowRef, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/authStore'
import { useRepairStore } from '@/stores/repairStore'
import { useUserStore } from '@/stores/userStore'

/** Minimum gap between activity heartbeats sent to the server. */
const ACTIVITY_REQUEST_INTERVAL_MS = 5_000
/** Minimum gap between activity messages to other tabs. */
const ACTIVITY_BROADCAST_INTERVAL_MS = 1_000

const ACTIVITY_EVENTS = ['pointerdown', 'pointermove', 'keydown', 'touchstart', 'scroll'] as const

/** Remembered per device: personal devices in the workshop network can switch it off. */
const AUTO_LOCK_PREF_KEY = 'repaircafe.autoLock'

function deviceWantsAutoLockOff(): boolean {
  try {
    return localStorage.getItem(AUTO_LOCK_PREF_KEY) === 'off'
  } catch {
    return false
  }
}

function rememberAutoLockForDevice(enabled: boolean) {
  try {
    if (enabled) localStorage.removeItem(AUTO_LOCK_PREF_KEY)
    else localStorage.setItem(AUTO_LOCK_PREF_KEY, 'off')
  } catch {
    // Storage unavailable (private mode): the switch then lasts for this login only
  }
}

/**
 * PIN session lifecycle for the shared workshop PC: idle auto-lock, activity
 * heartbeats, cross-tab sync and clearing user data on lock or user change.
 * Use once, in the root component.
 */
export function usePinSession() {
  const router = useRouter()
  const route = useRoute()
  const authStore = useAuthStore()
  const repairStore = useRepairStore()
  const userStore = useUserStore()

  const canUseApp = computed(() => authStore.isAuthenticated && !authStore.isLocked)
  /** The PC locks itself when idle: only in the workshop network and unless switched off. */
  const autoLockActive = computed(
    () => canUseApp.value && authStore.pinUnlockAvailable && authStore.autoLockEnabled
  )
  /** Seconds until the auto-lock, for the countdown; null while there is none. */
  const secondsUntilLock = shallowRef<number | null>(null)

  let idleTimer: number | null = null
  let countdownTimer: number | null = null
  let lockAt = 0
  let lastActivityRequest = 0
  let lastActivityBroadcast = 0
  const channel =
    typeof BroadcastChannel !== 'undefined' ? new BroadcastChannel('repaircafe-pin-session') : null

  function clearIdleTimer() {
    if (idleTimer !== null) {
      window.clearTimeout(idleTimer)
      idleTimer = null
    }
    if (countdownTimer !== null) {
      window.clearInterval(countdownTimer)
      countdownTimer = null
    }
    secondsUntilLock.value = null
  }

  function updateCountdown() {
    secondsUntilLock.value = Math.max(0, Math.ceil((lockAt - Date.now()) / 1000))
  }

  function scheduleIdleLock() {
    clearIdleTimer()
    // No idle lock outside the workshop (the PIN pad only works there) or when switched off
    if (!autoLockActive.value) return
    const timeoutMs = authStore.idleTimeoutSeconds * 1000
    lockAt = Date.now() + timeoutMs
    idleTimer = window.setTimeout(() => void lockNow(), timeoutMs)
    updateCountdown()
    countdownTimer = window.setInterval(updateCountdown, 1000)
  }

  /** Switch the auto-lock for this device; remembered for later logins. */
  async function setAutoLockForDevice(enabled: boolean): Promise<boolean> {
    const ok = await authStore.setAutoLock(enabled)
    if (ok) {
      rememberAutoLockForDevice(enabled)
      // Other tabs of this browser share the session; let them re-read it
      channel?.postMessage('session-changed')
    }
    return ok
  }

  // A fresh login starts with the auto-lock on; apply this device's choice again
  watch(
    canUseApp,
    (active) => {
      if (active && authStore.pinUnlockAvailable && authStore.autoLockEnabled && deviceWantsAutoLockOff()) {
        void authStore.setAutoLock(false)
      }
    },
    { immediate: true }
  )

  watch(
    () => authStore.autoLockEnabled,
    () => scheduleIdleLock()
  )

  function handleUserActivity() {
    if (!canUseApp.value || document.visibilityState !== 'visible') return
    scheduleIdleLock()
    const now = Date.now()
    if (now - lastActivityBroadcast >= ACTIVITY_BROADCAST_INTERVAL_MS) {
      lastActivityBroadcast = now
      channel?.postMessage('activity')
    }
    if (now - lastActivityRequest < ACTIVITY_REQUEST_INTERVAL_MS) return
    lastActivityRequest = now
    void authStore.recordActivity().then((active) => {
      if (!active && authStore.isLocked) {
        void router.replace({ name: 'PinLock' })
      }
    })
  }

  async function lockNow() {
    clearIdleTimer()
    if (!authStore.pinSessionEligible || authStore.isLocked || !authStore.pinUnlockAvailable) return
    const locked = await authStore.lockSession()
    if (locked) {
      channel?.postMessage('session-changed')
      await router.replace({ name: 'PinLock' })
    } else {
      scheduleIdleLock()
    }
  }

  async function revalidate() {
    if (document.visibilityState !== 'visible') return
    const eligible = await authStore.fetchMe()
    if (!eligible) {
      await router.replace({ name: 'Login' })
    } else if (authStore.isLocked) {
      await router.replace({ name: 'PinLock' })
    } else {
      handleUserActivity()
      if (route.name === 'PinLock') {
        await router.replace({ name: 'Home' })
      }
    }
  }

  watch(
    () => authStore.isLocked,
    (locked) => {
      if (locked) {
        repairStore.clear()
        userStore.clear()
        channel?.postMessage('session-changed')
        if (authStore.pinSessionEligible && route.name !== 'PinLock') {
          void router.replace({ name: 'PinLock' })
        }
      } else if (canUseApp.value) {
        scheduleIdleLock()
      }
    }
  )

  watch(canUseApp, (active) => {
    if (active) {
      scheduleIdleLock()
    } else {
      clearIdleTimer()
    }
  })

  watch(
    () => authStore.currentUser?.id,
    (nextId, previousId) => {
      if (nextId === previousId) return
      repairStore.clear()
      userStore.clear()
      if (nextId && previousId) {
        void router.replace({ name: 'Home' })
      }
      if (nextId || previousId) {
        channel?.postMessage('session-changed')
      }
    }
  )

  channel?.addEventListener('message', (event: MessageEvent<string>) => {
    if (event.data === 'activity') {
      scheduleIdleLock()
      return
    }
    void revalidate()
  })

  for (const type of ACTIVITY_EVENTS) {
    document.addEventListener(type, handleUserActivity, { passive: true })
  }
  document.addEventListener('visibilitychange', revalidate)
  scheduleIdleLock()

  onScopeDispose(() => {
    clearIdleTimer()
    for (const type of ACTIVITY_EVENTS) {
      document.removeEventListener(type, handleUserActivity)
    }
    document.removeEventListener('visibilitychange', revalidate)
    channel?.close()
  })

  return { canUseApp, lockNow, autoLockActive, secondsUntilLock, setAutoLockForDevice }
}
