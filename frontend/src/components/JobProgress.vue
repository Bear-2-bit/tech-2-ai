<script setup>
defineProps({ job: Object, busy: Boolean })
defineEmits(["cancel"])
</script>

<template>
  <section v-if="job" class="panel progress-panel" aria-live="polite">
    <div class="row between">
      <strong>运行状态 · {{ job.status }}</strong>
      <button v-if="busy" class="secondary" @click="$emit('cancel')">取消任务</button>
    </div>
    <p class="muted mono">{{ job.id }}</p>
    <div class="steps">
      <span v-for="step in job.spans || []" :key="step.id" :class="['step', step.status]">
        {{ step.name }} · {{ step.status }}
      </span>
    </div>
    <RouterLink :to="`/engineering?run=${job.id}`">查看完整追踪 ↗</RouterLink>
  </section>
</template>
