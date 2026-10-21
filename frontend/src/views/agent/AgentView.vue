<script setup>
import { onMounted, ref } from "vue"
import * as api from "../../api/agent"
import EvidenceList from "../../components/EvidenceList.vue"
import JobProgress from "../../components/JobProgress.vue"
import { useJob } from "../../composables/useJob"
import { useOperation } from "../../composables/useOperation"

const sessions = ref([])
const sessionId = ref("")
const turns = ref([])
const query = ref("调查2026年9月华东区域净销售额相对8月的变化，查看退款与售后情况，并结合制度给出核查建议。")
const { job, busy, error, start, stop } = useJob()
const { error: pageError, execute } = useOperation()
onMounted(() =>
  execute(async () => {
    sessions.value = await api.sessions()
  })
)
async function loadSession() {
  if (!sessionId.value) {
    turns.value = []
    return
  }
  await execute(async () => {
    turns.value = (await api.session(sessionId.value)).turns
  })
}
async function submit() {
  const current = await start(() =>
    api.investigate({ query: query.value, session_id: sessionId.value || null })
  )
  if (current?.result) {
    sessionId.value = current.result.session_id
    await loadSession()
    await execute(async () => {
      sessions.value = await api.sessions()
    })
    query.value = ""
  }
}
</script>

<template>
  <p class="eyebrow">04 / ADAPTIVE INVESTIGATION</p>
  <h1>带着证据，逐步调查问题</h1>
  <p class="intro">
    让 Agent 根据前一步结果选择查询、检索或计算。适合临时分析与连续追问，结论保留证据和不确定性。
  </p>
  <section class="panel">
    <div class="controls">
      <label>
        调查会话
        <select v-model="sessionId" :disabled="busy" @change="loadSession">
          <option value="">新建调查</option>
          <option v-for="item in sessions" :key="item.id" :value="item.id">{{ item.title }}</option>
        </select>
      </label>
      <span class="muted">工具调用上限 8 次 · 支持同一会话继续追问</span>
    </div>
    <form @submit.prevent="submit">
      <textarea
        v-model="query"
        rows="4"
        :disabled="busy"
        placeholder="说明调查对象、年份、月份和你关心的问题"
      />
      <button class="section-space" :disabled="busy || !query.trim()">
        {{ busy ? "调查中…" : "开始调查 / 继续追问" }}
      </button>
    </form>
  </section>
  <p v-if="error || pageError" class="error" role="alert">{{ error || pageError }}</p>
  <JobProgress :job="job" :busy="busy" @cancel="stop" />
  <section v-for="(turn, index) in turns" :key="turn.run_id" class="panel">
    <div class="row between">
      <h2>第 {{ index + 1 }} 轮 · {{ turn.query }}</h2>
      <span class="tag">{{ turn.status }}</span>
    </div>
    <p class="answer">{{ turn.answer }}</p>
    <ul>
      <li v-for="(finding, i) in turn.findings" :key="i">
        {{ finding.statement }}
        <small>{{ finding.evidence_ids.join(" · ") }}</small>
      </li>
    </ul>
    <template v-if="turn.uncertainties.length">
      <h3>不确定性</h3>
      <ul>
        <li v-for="item in turn.uncertainties" :key="item">{{ item }}</li>
      </ul>
    </template>
    <template v-if="turn.next_steps.length">
      <h3>下一步核查</h3>
      <ul>
        <li v-for="item in turn.next_steps" :key="item">{{ item }}</li>
      </ul>
    </template>
    <details>
      <summary>工具调用与证据</summary>
      <pre>{{ turn.steps }}</pre>
      <EvidenceList :documents="Object.values(turn.evidence).filter((item) => item.type === 'document')" />
      <details
        v-for="[key, item] in Object.entries(turn.evidence).filter(([, value]) => value.type !== 'document')"
        :key="key"
      >
        <summary>{{ key }} · {{ item.type }}</summary>
        <pre>{{ item }}</pre>
      </details>
    </details>
  </section>
</template>
