import http from "./http"


export async function querySQL(data) {
  const response = await http.post("/api/sql", data)
  return response.data
}