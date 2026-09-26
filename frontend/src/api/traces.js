import http from "./http"


export async function getTraces() {
  const response = await http.get("api/traces")
  return response.data
}