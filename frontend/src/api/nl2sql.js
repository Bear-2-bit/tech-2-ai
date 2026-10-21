import { post, request } from "./http"

export const schema = () => request("/api/nl2sql/schema")
export const query = (data, signal) => post("/api/nl2sql/query", data, { signal })
