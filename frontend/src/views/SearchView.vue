<script setup>
import { ref } from "vue"

import { searchDocuments } from "../api/search"


const query = ref("")
const topK = ref(3)
const documents = ref([])
const loading = ref(false)
const error = ref("")


async function handleSearch() {
  if (!query.value.trim()) return

  loading.value = true
  error.value = ""
  documents.value = []

  try {
    const data = await searchDocuments(query.value, topK.value)
    documents.value = data.documents
  } catch (err) {
    error.value = err?.response?.data?.detail || err.message || "搜索失败"
  } finally {
    loading.value = false
  }
}
</script>


<template>
  <div>
    <h1>Semantic Search</h1>

    <input v-model="query" placeholder="输入查询内容" />

    <input v-model.number="topK" type="number" min="1" max="20" />

    <button :disabled="loading" @click="handleSearch">
      {{ loading ? "搜索中..." : "搜索" }}
    </button>

    <p v-if="error">{{ error }}</p>

    <div v-for="(document, index) in documents" :key="index">
      <hr />
      <p>{{ document.content }}</p>
      <pre>{{ document.metadata }}</pre>
    </div>
  </div>
</template>