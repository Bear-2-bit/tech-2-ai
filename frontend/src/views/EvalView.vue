<script setup>
import { ref } from "vue"

import { runEvaluation } from "../api/eval"


const loading = ref(false)
const error = ref("")
const report = ref(null)


async function runAll() {
  loading.value = true
  error.value = ""
  report.value = null

  try {
    report.value = await runEvaluation({
      types: null,
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
    <h1>Evaluation</h1>

    <button
      :disabled="loading"
      @click="runAll"
    >
      {{ loading ? "评估中..." : "运行全部评估" }}
    </button>

    <p v-if="error">
      {{ error }}
    </p>

    <div v-if="report">
      <h2>Summary</h2>

      <p>Total: {{ report.total }}</p>
      <p>Passed: {{ report.passed }}</p>
      <p>Failed: {{ report.failed }}</p>
      <p>Average Score: {{ report.average_score }}</p>

      <h2>Cases</h2>

      <div
        v-for="item in report.results"
        :key="item.case_id"
      >
        <hr>

        <p>
          {{ item.case_id }}
          -
          {{ item.type }}
          -
          {{ item.passed ? "PASS" : "FAIL" }}
        </p>

        <p>Score: {{ item.score }}</p>
        <p>Latency: {{ item.latency_ms }} ms</p>

        <p v-if="item.error">
          Error: {{ item.error }}
        </p>

        <pre>{{ item.details }}</pre>
      </div>
    </div>
  </div>
</template>