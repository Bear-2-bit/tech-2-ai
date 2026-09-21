import http from "./http"

export async function sendChat(payload) {
  const response = await http.post("/api/chat", payload)
  return response.data
}