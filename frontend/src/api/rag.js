import { apiURL, post, request } from "./http"

export const status = () => request("/api/rag/status")
export const documents = () => request("/api/rag/documents")
export const sourceURL = (id) => apiURL(`/api/rag/documents/${id}/source`)
export const upload = (data) => post("/api/rag/documents", data)
export const seed = () => post("/api/rag/seed")
export const remove = (id) => request(`/api/rag/documents/${id}`, { method: "DELETE" })
export const search = (data, signal) => post("/api/rag/search", data, { signal })
export const ask = (data, signal) => post("/api/rag/ask", data, { signal })
