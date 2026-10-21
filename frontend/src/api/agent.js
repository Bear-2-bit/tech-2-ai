import { post, request } from "./http"

export const sessions = () => request("/api/agent/sessions")
export const session = (id) => request(`/api/agent/sessions/${id}`)
export const investigate = (data) => post("/api/agent/runs", data)
