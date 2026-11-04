import confetti from 'canvas-confetti'

/**
 * Confetti drawn on the main thread. The library's default instance renders in a
 * Web Worker loaded from a blob: URL, which the Content-Security-Policy blocks
 * (default-src 'self'), so nothing would appear.
 */
const fire = confetti.create(undefined, { resize: true, useWorker: false })

/** Fire confetti; never throws, so callers can carry on (e.g. play a sound). */
export function fireConfetti(options: confetti.Options) {
  try {
    void fire(options)
  } catch (err) {
    console.warn('Confetti failed', err)
  }
}
