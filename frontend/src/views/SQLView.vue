<script setup>
import { ref } from "vue"

import { querySQL } from "../api/sql"


const question = ref("")
const loading = ref(false)
const error = ref("")
const result = ref(null)


async function submit() {
  if (!question.value.trim()) return

  loading.value = true
  error.value = ""
  result.value = null

  try {
    result.value = await querySQL({
      question: question.value,
      max_rows: 100,
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
    <h1>NL2SQL</h1>

    <textarea
      v-model="question"
      placeholder="例如：查询销售额最高的三个部门"
      rows="4"
    />

    <br>

    <button
      :disabled="loading"
      @click="submit"
    >
      {{ loading ? "查询中..." : "查询" }}
    </button>

    <p v-if="error">
      {{ error }}
    </p>

    <div v-if="result">
      <h2>Generated SQL</h2>
      <pre>{{ result.sql }}</pre>

      <h2>Explanation</h2>
      <p>{{ result.explanation }}</p>

      <h2>Result</h2>

      <table border="1">
        <thead>
          <tr>
            <th
              v-for="column in result.columns"
              :key="column"
            >
              {{ column }}
            </th>
          </tr>
        </thead>

        <tbody>
          <tr
            v-for="(row, rowIndex) in result.rows"
            :key="rowIndex"
          >
            <td
              v-for="(value, valueIndex) in row"
              :key="valueIndex"
            >
              {{ value }}
            </td>
          </tr>
        </tbody>
      </table>

      <p>
        返回 {{ result.row_count }} 行
        <span v-if="result.truncated">（结果已截断）</span>
      </p>
    </div>
  </div>
</template>