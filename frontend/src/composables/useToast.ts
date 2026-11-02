import { ref } from 'vue'

export type ToastColor = 'success' | 'error' | 'warning' | 'info'

export interface ToastOptions {
  color?: ToastColor
  /** Milliseconds; defaults depend on the color (errors stay longer). */
  timeout?: number
}

export interface ToastMessage {
  text: string
  color: ToastColor
  timeout: number
}

const DEFAULT_TIMEOUT: Record<ToastColor, number> = {
  success: 3000,
  info: 4000,
  warning: 5000,
  error: 6000,
}

// App-wide queue, rendered once by <VSnackbarQueue> in App.vue.
// VSnackbarQueue takes messages off this array as it displays them.
const queue = ref<ToastMessage[]>([])

function show(text: string, options: ToastOptions = {}) {
  const color = options.color ?? 'info'
  queue.value.push({ text, color, timeout: options.timeout ?? DEFAULT_TIMEOUT[color] })
}

/** Show short status messages to the user from anywhere in the app. */
export function useToast() {
  return {
    show,
    success: (text: string, timeout?: number) => show(text, { color: 'success', timeout }),
    info: (text: string, timeout?: number) => show(text, { color: 'info', timeout }),
    warning: (text: string, timeout?: number) => show(text, { color: 'warning', timeout }),
    error: (text: string, timeout?: number) => show(text, { color: 'error', timeout }),
  }
}

/** The queue itself; only App.vue renders it. */
export function useToastQueue() {
  return queue
}
