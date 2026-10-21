const baseURL = (import.meta.env.VITE_API_BASE_URL || "").replace(/\/$/, "")
export const apiURL = (path) => `${baseURL}${path}`

export async function request(path, { method = "GET", body, signal, stream = false } = {}) {
  const headers = body instanceof FormData ? {} : { "Content-Type": "application/json" }
  const timeout = AbortSignal.timeout(stream ? 200000 : 60000)
  const response = await fetch(`${baseURL}${path}`, {
    method,
    headers,
    body: body instanceof FormData ? body : body === undefined ? undefined : JSON.stringify(body),
    signal: signal ? AbortSignal.any([signal, timeout]) : timeout
  })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `请求失败（${response.status}）`)
  }
  return stream ? response : response.json()
}

export const post = (path, body, options = {}) => request(path, { method: "POST", body, ...options })
