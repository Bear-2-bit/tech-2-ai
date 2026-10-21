import { post, request } from "./http"
import { consumeEvents } from "./events"

export const chat = (engine, body, signal) => post(`/api/llm/${engine}/chat`, body, { signal })
export const extract = (engine, body, signal) => post(`/api/llm/${engine}/extract`, body, { signal })
export async function streamChat(engine, body, onEvent, signal) {
  const response = await request(`/api/llm/${engine}/stream`, { method: "POST", body, signal, stream: true })
  await consumeEvents(response.body, onEvent)
}
