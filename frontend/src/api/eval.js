import http from "./http"


export async function runEvaluation(data) {
  const response = await http.post("api/eval", data)
  return response.data
}