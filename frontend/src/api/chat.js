import http from "./http"


// 普通非流式接口
export async function sendChat(payload) {
  const response = await http.post(
    "/api/chat",
    payload
  )

  return response.data
}


// 流式接口
export async function streamChat(
  payload,
  onEvent,
) {
  const baseURL =
    import.meta.env.VITE_API_BASE_URL


  const response = await fetch(
    `${baseURL}/api/chat/stream`,
    {
      method: "POST",

      headers: {
        "Content-Type": "application/json",
      },

      body: JSON.stringify(payload),
    }
  )


  if (!response.ok) {
    throw new Error(
      `HTTP error: ${response.status}`
    )
  }


  if (!response.body) {
    throw new Error(
      "Streaming response body is empty"
    )
  }


  const reader = response.body.getReader()

  const decoder = new TextDecoder("utf-8")

  let buffer = ""


  while (true) {

    const { done, value } =
      await reader.read()


    if (done) {
      break
    }


    buffer += decoder.decode(
      value,
      {
        stream: true,
      }
    )


    const events = buffer.split("\n\n")

    buffer = events.pop() || ""


    for (const eventText of events) {

      if (!eventText.trim()) {
        continue
      }


      if (
        eventText.startsWith("event: error")
      ) {
        throw new Error(
          "LLM streaming failed"
        )
      }


      const dataLine =
        eventText
          .split("\n")
          .find(
            line =>
              line.startsWith("data: ")
          )


      if (!dataLine) {
        continue
      }


      const data = JSON.parse(
        dataLine.slice(6)
      )


      onEvent(data)
    }
  }
}