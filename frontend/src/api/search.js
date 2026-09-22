import http from "./http"


export async function searchDocuments(query, topK = 3) {
  const response = await http.post("/api/search", {
    query,
    top_k: topK,
  })

  return response.data
}