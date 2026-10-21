<script setup>
import { ref } from "vue"
import { chat, extract, streamChat } from "../../api/llm"
import RunInfo from "../../components/RunInfo.vue"
import { useOperation } from "../../composables/useOperation"

const engine = ref("native")
const mode = ref("stream")
const input = ref("")
const systemPrompt = ref("你是一名 AI 应用工程老师，回答简洁准确。")
const temperature = ref(0.3)
const maxTokens = ref(1000)
const history = ref([])
const result = ref(null)
const answer = ref("")
const { busy, error, execute, stop } = useOperation()

async function submit() {
  if (!input.value.trim()) return
  const text = input.value.trim()
  result.value = null
  answer.value = ""
  await execute(async (signal) => {
    if (mode.value === "extract") {
      result.value = await extract(engine.value, { text }, signal)
      return
    }
    const messages = [...history.value, { role: "user", content: text }]
    const body = {
      messages,
      system_prompt: systemPrompt.value,
      temperature: temperature.value,
      max_tokens: maxTokens.value
    }
    if (mode.value === "chat") {
      result.value = await chat(engine.value, body, signal)
      answer.value = result.value.answer
    } else {
      await streamChat(
        engine.value,
        body,
        (event) => {
          if (event.type === "delta") answer.value += event.content
          if (event.type === "done") result.value = event
        },
        signal
      )
    }
    if (result.value) {
      history.value = [...messages, { role: "assistant", content: answer.value }]
      input.value = ""
    }
  })
}

function reset() {
  history.value = []
  result.value = null
  answer.value = ""
}
</script>

<template>
  <p class="eyebrow">01 / MODEL FUNDAMENTALS</p>
  <h1>理解一次模型调用</h1>
  <p class="intro">在同一个输入与界面中，对照原生 SDK 和 LangChain，观察普通、流式与结构化输出。</p>
  <div class="controls">
    <label>
      实现方式
      <select v-model="engine" :disabled="busy" @change="reset">
        <option value="native">原生 SDK · 理解机制</option>
        <option value="langchain">LangChain · 框架应用</option>
      </select>
    </label>
    <label>
      输出方式
      <select v-model="mode" :disabled="busy" @change="reset">
        <option value="chat">普通输出</option>
        <option value="stream">流式输出</option>
        <option value="extract">结构化输出</option>
      </select>
    </label>
    <button class="secondary" :disabled="busy" @click="reset">清空对话</button>
  </div>
  <div class="grid">
    <section class="panel">
      <h2>{{ mode === "extract" ? "任务信息抽取" : "输入与上下文" }}</h2>
      <label v-if="mode !== 'extract'">
        System Prompt
        <textarea v-model="systemPrompt" rows="2" :disabled="busy" />
      </label>
      <div v-if="mode !== 'extract'" class="controls section-space">
        <label>
          Temperature
          <input v-model.number="temperature" type="number" min="0" max="2" step="0.1" :disabled="busy" />
        </label>
        <label>
          Max Tokens
          <input v-model.number="maxTokens" type="number" min="16" max="8000" :disabled="busy" />
        </label>
      </div>
      <form @submit.prevent="submit">
        <label>
          {{ mode === "extract" ? "待抽取文本" : "你的问题" }}
          <textarea
            v-model="input"
            rows="5"
            :disabled="busy"
            :placeholder="
              mode === 'extract'
                ? '请高优先级安排明天使用 Vue 和 FastAPI 开发任务页面。'
                : '例如：流式响应和普通响应有什么区别？'
            "
          />
        </label>
        <div class="row section-space">
          <button :disabled="busy || !input.trim()">{{ busy ? "生成中…" : "运行模型" }}</button>
          <button v-if="busy" type="button" class="secondary" @click="stop">停止生成</button>
        </div>
      </form>
      <p v-if="error" class="error section-space" role="alert">{{ error }}</p>
    </section>
    <section class="panel">
      <h2>{{ mode === "extract" ? "经过校验的数据结构" : "模型输出" }}</h2>
      <pre v-if="result?.result">{{ JSON.stringify(result.result, null, 2) }}</pre>
      <div v-else-if="answer" class="answer">{{ answer }}</div>
      <p v-else class="empty">运行后在这里查看结果</p>
      <p v-if="result?.attempts" class="muted">结构化尝试次数：{{ result.attempts }}</p>
      <RunInfo :data="result" />
    </section>
  </div>
  <section v-if="history.length" class="panel">
    <h2>已完成的对话上下文</h2>
    <div v-for="(message, i) in history" :key="i" class="chat-message">
      <strong>{{ message.role }}</strong>
      <div class="preserve">{{ message.content }}</div>
    </div>
  </section>
</template>
