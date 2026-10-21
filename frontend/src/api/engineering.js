import { post, request } from "./http"

export const runs = (module = "") => request(`/api/engineering/runs${module ? `?module=${module}` : ""}`)
export const run = (id, signal) => request(`/api/engineering/runs/${id}`, { signal })
export const cancel = (id) => post(`/api/engineering/runs/${id}/cancel`)
export const logs = () => request("/api/engineering/logs")
export const cases = () => request("/api/engineering/evaluations/cases")
export const evaluate = (data) => post("/api/engineering/evaluations", data)
