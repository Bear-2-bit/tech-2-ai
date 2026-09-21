import http from "./http"


export async function extractTask(
  payload
) {
  const response = await http.post(
    "/api/extraction",
    payload
  )

  return response.data
}