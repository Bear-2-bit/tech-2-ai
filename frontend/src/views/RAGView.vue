<script setup>
import { ref } from "vue"

import {
  askRAG,
  indexRAGDocument,
} from "../api/rag"


const file = ref(null)
const indexResult = ref(null)

const query = ref("")
const topK = ref(3)

const rewrittenQuery = ref("")
const answer = ref("")
const documents = ref([])
const citations = ref([])

const indexing = ref(false)
const loading = ref(false)
const error = ref("")


function handleFileChange(event) {
  file.value = event.target.files?.[0] || null
}


async function handleIndex() {
  if (!file.value) return

  indexing.value = true
  error.value = ""
  indexResult.value = null

  try {
    indexResult.value = await indexRAGDocument(file.value)
  } catch (err) {
    error.value = err?.response?.data?.detail || err.message || "知识入库失败"
  } finally {
    indexing.value = false
  }
}


async function handleAsk() {
  if (!query.value.trim()) return

  loading.value = true
  error.value = ""

  rewrittenQuery.value = ""
  answer.value = ""
  documents.value = []
  citations.value = []

  try {
    const data = await askRAG(query.value, topK.value)

    rewrittenQuery.value = data.rewritten_query
    answer.value = data.answer
    documents.value = data.retrieved_documents
    citations.value = data.citations
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

    <h2>Knowledge Ingestion</h2>

    <input
      type="file"
      accept=".pdf,.txt,.md"
      @change="handleFileChange"
    />

    <button :disabled="indexing" @click="handleIndex">
      {{ indexing ? "入库中..." : "上传并入库" }}
    </button>

    <pre v-if="indexResult">{{ indexResult }}</pre>


    <h2>Question</h2>

    <input v-model="query" placeholder="输入问题" />

    <input v-model.number="topK" type="number" min="1" max="20" />

    <button :disabled="loading" @click="handleAsk">
      {{ loading ? "回答中..." : "提问" }}
    </button>

    <p v-if="error">{{ error }}</p>


    <h2>Rewritten Query</h2>
    <p>{{ rewrittenQuery }}</p>


    <h2>Answer</h2>
    <p>{{ answer }}</p>


    <h2>Citations</h2>

    <div v-for="citation in citations" :key="citation.index">
      <p>
        [{{ citation.index }}]
        {{ citation.source }}
        <span v-if="citation.page"> - 第 {{ citation.page }} 页</span>
        <span v-if="citation.chunk_index !== null">
          - Chunk {{ citation.chunk_index }}
        </span>
      </p>
    </div>


    <h2>Retrieved Documents</h2>

    <div v-for="(document, index) in documents" :key="index">
      <hr />

      <p>Rank: {{ index + 1 }}</p>
      <p>Rerank Score: {{ document.rerank_score }}</p>
      <p>{{ document.content }}</p>

      <pre>{{ document.metadata }}</pre>
    </div>
  </div>
</template>