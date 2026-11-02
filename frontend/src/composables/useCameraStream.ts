import { nextTick, onScopeDispose, shallowRef, type Ref } from 'vue'

const DEFAULT_CONSTRAINTS: MediaStreamConstraints = {
  video: { facingMode: { ideal: 'environment' } },
  audio: false,
}

/**
 * Owns a camera MediaStream bound to a <video> element.
 * The stream is stopped on `stop()` and automatically when the owning
 * component/effect scope is disposed, so the camera never keeps running
 * after its UI is gone.
 */
export function useCameraStream(videoEl: Ref<HTMLVideoElement | null>) {
  const active = shallowRef(false)
  const permissionDenied = shallowRef(false)
  let stream: MediaStream | null = null
  // Invalidates a pending getUserMedia() when stop() runs before it resolves
  let startToken = 0

  async function start(constraints: MediaStreamConstraints = DEFAULT_CONSTRAINTS): Promise<boolean> {
    stop()
    const token = ++startToken
    permissionDenied.value = false
    try {
      const nextStream = await navigator.mediaDevices.getUserMedia(constraints)
      if (token !== startToken) {
        nextStream.getTracks().forEach((track) => track.stop())
        return false
      }
      stream = nextStream
      // The <video> is often rendered only while the camera is active
      active.value = true
      await nextTick()
      if (videoEl.value && token === startToken) {
        videoEl.value.srcObject = nextStream
        await videoEl.value.play().catch(() => {})
      }
      return token === startToken
    } catch (error) {
      if (token === startToken) {
        console.error('Error accessing camera:', error)
        permissionDenied.value = true
      }
      return false
    }
  }

  function stop() {
    startToken++
    stream?.getTracks().forEach((track) => track.stop())
    stream = null
    if (videoEl.value) videoEl.value.srcObject = null
    active.value = false
  }

  onScopeDispose(stop)

  return { active, permissionDenied, start, stop }
}
