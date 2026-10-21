import test from "node:test"
import assert from "node:assert/strict"
import { consumeEvents } from "../src/api/events.js"

function stream(chunks) {
  return new ReadableStream({
    start(controller) {
      for (const chunk of chunks) controller.enqueue(chunk)
      controller.close()
    }
  })
}

test("handles UTF-8 boundaries, CRLF and final event without delimiter", async () => {
  const bytes = new TextEncoder().encode('data: {"type":"delta","content":"你好"}\r\n\r\ndata: {"type":"done"}')
  const events = []
  await consumeEvents(stream(Array.from(bytes, (byte) => new Uint8Array([byte]))), (value) => events.push(value))
  assert.equal(events[0].content, "你好")
  assert.equal(events[1].type, "done")
})

test("rejects interrupted stream and server error event", async () => {
  const encoder = new TextEncoder()
  await assert.rejects(
    consumeEvents(stream([encoder.encode('data: {"type":"delta","content":"partial"}\n\n')]), () => {}),
    /提前结束/
  )
  await assert.rejects(
    consumeEvents(stream([encoder.encode('data: {"type":"error","detail":"模型超时"}\n\n')]), () => {}),
    /模型超时/
  )
})
