import { post, request } from "./http"

export const generate = (data) => post("/api/workflow/reports", data)
export const history = () => request("/api/workflow/reports")
