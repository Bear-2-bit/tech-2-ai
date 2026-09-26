<script setup>
import { onMounted, ref } from "vue"

import { getTraces } from "../api/traces"


const traces = ref([])
const loading = ref(false)
const error = ref("")


async function loadTraces() {
  loading.value = true
  error.value = ""

  try {
    traces.value = await getTraces()
  } catch (err) {
    error.value = err.response?.data?.detail || err.message
  } finally {
    loading.value = false
  }
}


onMounted(loadTraces)
</script>

<template>
  <div>
    <h1>Traces</h1>

    <button
      :disabled="loading"
      @click="loadTraces"
    >
      {{ loading ? "加载中..." : "刷新" }}
    </button>

    <p v-if="error">
      {{ error }}
    </p>

    <table v-if="traces.length">
      <thead>
        <tr>
          <th>Trace ID</th>
          <th>Status</th>
          <th>Latency</th>
          <th>Tokens</th>
          <th>Input</th>
          <th>Error</th>
        </tr>
      </thead>

      <tbody>
        <tr
          v-for="trace in traces"
          :key="trace.trace_id"
        >
          <td>
            {{ trace.trace_id }}
          </td>

          <td>
            {{ trace.status }}
          </td>

          <td>
            {{ trace.latency_ms }} ms
          </td>

          <td>
            {{ trace.total_tokens }}
          </td>

          <td>
            {{ trace.input_preview }}
          </td>

          <td>
            {{ trace.error || "-" }}
          </td>
        </tr>
      </tbody>
    </table>

    <p v-else-if="!loading">
      暂无 Trace
    </p>
  </div>
</template>