import http from "./http"


export async function askRAG(query, topK = 3) {
  const response = await http.post("/api/rag", {
    query,
    top_k: topK,
  })

  return response.data
}