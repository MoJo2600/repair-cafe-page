import { onScopeDispose, shallowRef } from 'vue'
import confetti from 'canvas-confetti'

/**
 * Celebrates a successful repair: confetti plus a short fanfare.
 *
 * Browsers only allow sound after the first user interaction with the page, so the
 * audio context is unlocked on the first tap/click/key press (or via `enableSound`).
 * The mute switch is remembered per device.
 */
const SOUND_PREF_KEY = 'repaircafe.celebrationSound'

function readSoundPref(): boolean {
  try {
    return localStorage.getItem(SOUND_PREF_KEY) !== 'off'
  } catch {
    return true
  }
}

function writeSoundPref(enabled: boolean) {
  try {
    if (enabled) localStorage.removeItem(SOUND_PREF_KEY)
    else localStorage.setItem(SOUND_PREF_KEY, 'off')
  } catch {
    // Storage unavailable: the switch lasts until reload
  }
}

/** Rising major arpeggio (C5 E5 G5 C6), the last note held. */
const FANFARE: Array<[frequency: number, start: number, duration: number]> = [
  [523.25, 0, 0.14],
  [659.25, 0.14, 0.14],
  [783.99, 0.28, 0.14],
  [1046.5, 0.42, 0.6],
]

export function useCelebration() {
  const soundEnabled = shallowRef(readSoundPref())
  /** True once the browser lets this page play audio. */
  const soundUnlocked = shallowRef(false)

  let audio: AudioContext | null = null

  function context(): AudioContext | null {
    if (!audio && typeof AudioContext !== 'undefined') audio = new AudioContext()
    return audio
  }

  async function unlock() {
    const ctx = context()
    if (!ctx) return
    if (ctx.state === 'suspended') await ctx.resume().catch(() => {})
    soundUnlocked.value = ctx.state === 'running'
    if (soundUnlocked.value) removeUnlockListeners()
  }

  const onFirstInteraction = () => void unlock()
  const UNLOCK_EVENTS = ['pointerdown', 'keydown', 'touchstart'] as const
  function removeUnlockListeners() {
    for (const type of UNLOCK_EVENTS) document.removeEventListener(type, onFirstInteraction)
  }
  for (const type of UNLOCK_EVENTS) {
    document.addEventListener(type, onFirstInteraction, { passive: true })
  }

  function playFanfare() {
    const ctx = context()
    if (!ctx || ctx.state !== 'running') return
    const now = ctx.currentTime
    for (const [frequency, start, duration] of FANFARE) {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.type = 'triangle'
      osc.frequency.value = frequency
      // Short attack and decay so the notes don't click
      gain.gain.setValueAtTime(0.0001, now + start)
      gain.gain.exponentialRampToValueAtTime(0.35, now + start + 0.02)
      gain.gain.exponentialRampToValueAtTime(0.0001, now + start + duration)
      osc.connect(gain).connect(ctx.destination)
      osc.start(now + start)
      osc.stop(now + start + duration + 0.05)
    }
  }

  function celebrate() {
    confetti({ particleCount: 180, spread: 90, origin: { y: 0.6 } })
    if (soundEnabled.value) playFanfare()
  }

  /** Switch the sound on or off for this device; switching on also unlocks audio. */
  async function setSoundEnabled(enabled: boolean) {
    soundEnabled.value = enabled
    writeSoundPref(enabled)
    if (enabled) await unlock()
  }

  /** Play the fanfare once, e.g. to test the speakers. */
  async function testSound() {
    await unlock()
    playFanfare()
  }

  onScopeDispose(() => {
    removeUnlockListeners()
    void audio?.close()
  })

  return { soundEnabled, soundUnlocked, celebrate, setSoundEnabled, testSound }
}
