<script setup>
import { ref } from "vue"

import { runWorkflow } from "../api/workflow"


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
    result.value = await runWorkflow({
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
    <h1>Workflow</h1>

    <textarea
      v-model="query"
      rows="4"
      placeholder="例如：分析各部门销售情况，并结合知识库给出经营建议"
    />

    <br>

    <button
      :disabled="loading"
      @click="submit"
    >
      {{ loading ? "分析中..." : "运行 Workflow" }}
    </button>

    <p v-if="error">
      {{ error }}
    </p>

    <div v-if="result">
      <h2>Plan</h2>

      <p>SQL：{{ result.sql_question }}</p>
      <p>RAG：{{ result.rag_question }}</p>

      <h2>SQL Result</h2>
      <pre>{{ result.sql_result }}</pre>

      <h2>RAG Result</h2>
      <pre>{{ result.rag_result }}</pre>

      <h2>{{ result.report.title }}</h2>

      <p>{{ result.report.summary }}</p>

      <h3>Key Findings</h3>
      <ul>
        <li
          v-for="item in result.report.key_findings"
          :key="item"
        >
          {{ item }}
        </li>
      </ul>

      <h3>Recommendations</h3>
      <ul>
        <li
          v-for="item in result.report.recommendations"
          :key="item"
        >
          {{ item }}
        </li>
      </ul>
    </div>
  </div>
</template>