import http from "./http"


export async function runAgent(data) {
  const response = await http.post("api/agent", data)
  return response.data
}