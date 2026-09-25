<script setup>
import { ref } from "vue"

import { runAgent } from "../api/agent"


const query = ref("")
const loading = ref(false)
const error = ref("")
const result = ref(null)


async function submit() {
  if (!query.value.trim()) return

  loading.value = true
  error.value = ""
  result.value = null

  try {
    result.value = await runAgent({
      query: query.value,
    })
  } catch (err) {
    error.value = err.response?.data?.detail || err.message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h1>Agent</h1>

    <textarea
      v-model="query"
      rows="4"
      placeholder="输入一个需要AI自主选择工具完成的任务"
    />

    <br>

    <button
      :disabled="loading"
      @click="submit"
    >
      {{ loading ? "运行中..." : "运行 Agent" }}
    </button>

    <p v-if="error">
      {{ error }}
    </p>

    <div v-if="result">
      <h2>Final Answer</h2>
      <p>{{ result.answer }}</p>

      <h2>Agent Steps</h2>

      <div
        v-for="(step, index) in result.steps"
        :key="index"
      >
        <h3>{{ index + 1 }}. {{ step.message_type }}</h3>

        <p v-if="step.tool_name">
          Tool: {{ step.tool_name }}
        </p>

        <pre v-if="step.tool_calls.length">{{ step.tool_calls }}</pre>

        <pre>{{ step.content }}</pre>
      </div>
    </div>
  </div>
</template>