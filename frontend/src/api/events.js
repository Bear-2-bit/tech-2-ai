export async function consumeEvents(body, onEvent) {
  const reader = body.getReader()
  const decoder = new TextDecoder()
  let buffer = ""
  let completed = false
  function consume(final = false) {
    buffer = buffer.replace(/\r\n/g, "\n")
    const blocks = buffer.split("\n\n")
    buffer = blocks.pop() || ""
    if (final && buffer.trim()) blocks.push(buffer)
    for (const block of blocks) {
      const data = block
        .split("\n")
        .filter((line) => line.startsWith("data:"))
        .map((line) => line.slice(5).trimStart())
        .join("\n")
      if (!data) continue
      const event = JSON.parse(data)
      if (event.type === "error") throw new Error(event.detail || "流式请求失败")
      if (event.type === "done") completed = true
      onEvent(event)
    }
  }
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      consume()
    }
    buffer += decoder.decode()
    consume(true)
    if (!completed) throw new Error("连接提前结束，回答尚未完成")
  } finally {
    await reader.cancel().catch(() => {})
    reader.releaseLock()
  }
}
