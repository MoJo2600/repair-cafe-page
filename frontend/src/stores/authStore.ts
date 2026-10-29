import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { AuthService } from '@/api/services/AuthService'
import type { UserResponse } from '@/api/types'

function messageFromError(error: unknown, fallback: string): string {
  if (!error || typeof error !== 'object') return fallback
  const candidate = error as { body?: { error?: unknown }; message?: unknown }
  if (typeof candidate.body?.error === 'string') return candidate.body.error
  if (typeof candidate.message === 'string') return candidate.message
  return fallback
}

export const useAuthStore = defineStore('auth', () => {
  const currentUser = ref<UserResponse | null>(null)
  const loading = ref(false)
  const pinSessionEligible = ref(false)
  const isLocked = ref(false)
  const sessionChecked = ref(false)

  const isAuthenticated = computed(() => currentUser.value !== null)
  const isAdmin = computed(() => currentUser.value?.is_admin ?? false)

  /** Called on app startup to restore session from cookie. */
  async function fetchMe(): Promise<boolean> {
    try {
      const data = await AuthService.pinSessionStatus()
      pinSessionEligible.value = data.eligible
      isLocked.value = data.locked
      currentUser.value = data.locked ? null : (data.user ?? null)
      sessionChecked.value = true
      return data.eligible
    } catch {
      currentUser.value = null
      pinSessionEligible.value = false
      isLocked.value = false
      sessionChecked.value = true
      return false
    }
  }

  async function login(
    username: string,
    password: string
  ): Promise<{ success: boolean; error?: string }> {
    loading.value = true
    try {
      const data = await AuthService.login({ username, password })
      currentUser.value = data.data ?? null
      pinSessionEligible.value = currentUser.value !== null
      isLocked.value = false
      sessionChecked.value = true
      return { success: true }
    } catch (err: unknown) {
      const message = messageFromError(err, 'Login failed')
      return { success: false, error: message }
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    await AuthService.logout()
    currentUser.value = null
    pinSessionEligible.value = false
    isLocked.value = false
    sessionChecked.value = true
  }

  async function lockSession(): Promise<boolean> {
    try {
      await AuthService.lockPinSession()
      currentUser.value = null
      isLocked.value = true
      return true
    } catch {
      await fetchMe()
      return isLocked.value
    }
  }

  async function recordActivity(): Promise<boolean> {
    try {
      await AuthService.recordPinActivity()
      return true
    } catch {
      await fetchMe()
      return !isLocked.value
    }
  }

  async function unlock(pin_code: string): Promise<{ success: boolean; error?: string }> {
    try {
      const data = await AuthService.unlockPinSession({ pin_code })
      currentUser.value = data.data ?? null
      pinSessionEligible.value = currentUser.value !== null
      isLocked.value = false
      sessionChecked.value = true
      return { success: currentUser.value !== null }
    } catch (err: unknown) {
      return {
        success: false,
        error: messageFromError(err, 'PIN ungültig'),
      }
    }
  }

  return {
    currentUser,
    loading,
    isAuthenticated,
    isAdmin,
    pinSessionEligible,
    isLocked,
    sessionChecked,
    fetchMe,
    login,
    logout,
    lockSession,
    recordActivity,
    unlock,
  }
})
