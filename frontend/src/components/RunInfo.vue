<script setup>
defineProps({ data: Object })
</script>

<template>
  <div v-if="data" class="run-info">
    <span v-if="data.model">{{ data.model }}</span>
    <span v-if="data.latency_ms != null">{{ (data.latency_ms / 1000).toFixed(2) }} 秒</span>
    <span v-if="data.usage">{{ data.usage.total_tokens }} tokens</span>
    <span v-if="data.finish_reason">{{ data.finish_reason }}</span>
    <RouterLink v-if="data.run_id" :to="`/engineering?run=${data.run_id}`">查看执行记录 ↗</RouterLink>
  </div>
</template>
