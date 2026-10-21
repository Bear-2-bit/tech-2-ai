<script setup>
defineProps({ documents: { type: Array, default: () => [] } })
</script>

<template>
  <div class="evidence-list">
    <details v-for="document in documents" :key="document.id" class="evidence">
      <summary>
        {{ document.metadata?.filename || document.id }}
        <small v-if="document.score != null">{{ document.score_type }} {{ document.score.toFixed(3) }}</small>
      </summary>
      <p class="muted">
        {{ document.id }} <span v-if="document.metadata?.page">· 第 {{ document.metadata.page }} 页</span>
      </p>
      <p class="preserve">{{ document.content }}</p>
    </details>
  </div>
</template>
