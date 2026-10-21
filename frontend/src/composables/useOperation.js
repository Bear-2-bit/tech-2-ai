import { onUnmounted, ref } from "vue"

export function useOperation() {
  const busy = ref(false)
  const error = ref("")
  let controller
  async function execute(work) {
    if (busy.value) return
    controller = new AbortController()
    busy.value = true
    error.value = ""
    try {
      return await work(controller.signal)
    } catch (exc) {
      error.value = exc.name === "AbortError" ? "操作已停止" : exc.message
    } finally {
      busy.value = false
    }
  }
  const stop = () => controller?.abort()
  onUnmounted(stop)
  return { busy, error, execute, stop }
}
