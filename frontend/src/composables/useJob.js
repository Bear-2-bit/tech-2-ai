import { onUnmounted, ref } from "vue"
import { run, cancel } from "../api/engineering"

export function useJob() {
  const job = ref(null)
  const busy = ref(false)
  const error = ref("")
  let controller
  async function start(submit) {
    if (busy.value) return
    busy.value = true
    error.value = ""
    job.value = null
    controller = new AbortController()
    try {
      const submitted = await submit()
      while (!controller.signal.aborted) {
        job.value = await run(submitted.run_id, controller.signal)
        if (!["running", "queued"].includes(job.value.status)) break
        await new Promise((resolve) => {
          const finish = () => {
            clearTimeout(timer)
            controller.signal.removeEventListener("abort", finish)
            resolve()
          }
          const timer = setTimeout(finish, 900)
          controller.signal.addEventListener("abort", finish, { once: true })
        })
      }
      if (job.value?.error) error.value = job.value.error
      return job.value
    } catch (exc) {
      if (exc.name !== "AbortError") error.value = exc.message
    } finally {
      busy.value = false
    }
  }
  async function stop() {
    if (job.value?.id) {
      try {
        await cancel(job.value.id)
      } catch (exc) {
        error.value = exc.message
      }
    }
  }
  onUnmounted(() => controller?.abort())
  return { job, busy, error, start, stop }
}
