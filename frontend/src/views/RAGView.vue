<script setup>
import { ref } from "vue"

import { askRAG } from "../api/rag"


const query = ref("")
const topK = ref(3)
const answer = ref("")
const documents = ref([])
const loading = ref(false)
const error = ref("")


async function handleAsk() {
  if (!query.value.trim()) return

  loading.value = true
  error.value = ""
  answer.value = ""
  documents.value = []

  try {
    const data = await askRAG(query.value, topK.value)

    answer.value = data.answer
    documents.value = data.retrieved_documents
  } catch (err) {
    error.value = err?.response?.data?.detail || err.message || "RAG请求失败"
  } finally {
    loading.value = false
  }
}
</script>


<template>
  <div>
    <h1>RAG</h1>

    <input v-model="query" placeholder="输入问题" />

    <input v-model.number="topK" type="number" min="1" max="20" />

    <button :disabled="loading" @click="handleAsk">
      {{ loading ? "回答中..." : "提问" }}
    </button>

    <p v-if="error">{{ error }}</p>

    <h2>Answer</h2>
    <p>{{ answer }}</p>

    <h2>Retrieved Documents</h2>

    <div v-for="(document, index) in documents" :key="index">
      <hr />
      <p>{{ document.content }}</p>
      <pre>{{ document.metadata }}</pre>
    </div>
  </div>
</template>