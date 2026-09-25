import http from "./http"


export async function runWorkflow(data) {
  const response = await http.post("api/workflow", data)
  return response.data
}