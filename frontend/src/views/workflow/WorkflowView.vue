<script setup>
import { computed, onMounted, ref } from "vue"
import * as api from "../../api/workflow"
import { run } from "../../api/engineering"
import EvidenceList from "../../components/EvidenceList.vue"
import JobProgress from "../../components/JobProgress.vue"
import { useJob } from "../../composables/useJob"
import { useOperation } from "../../composables/useOperation"

const month = ref("2026-09")
const departmentId = ref("")
const focus = ref("关注净销售额、退款与售后变化")
const reports = ref([])
const selected = ref(null)
const { job, busy, error, start, stop } = useJob()
const { error: pageError, execute } = useOperation()
const result = computed(() => selected.value || job.value?.result)
const labels = {
  sales_cents: "销售额",
  refund_cents: "退款额",
  net_sales_cents: "净销售额",
  order_count: "完成订单",
  ticket_count: "售后工单",
  attainment: "目标达成率",
  net_growth: "净销售额环比"
}
function format(key, value) {
  return value == null
    ? "无可比值"
    : key.endsWith("cents")
      ? `¥ ${(value / 100).toLocaleString("zh-CN", { maximumFractionDigits: 2 })}`
      : ["attainment", "net_growth"].includes(key)
        ? `${(value * 100).toFixed(2)}%`
        : value
}
onMounted(() =>
  execute(async () => {
    reports.value = await api.history()
  })
)
async function submit() {
  selected.value = null
  await start(() =>
    api.generate({
      month: month.value,
      department_id: departmentId.value ? Number(departmentId.value) : null,
      focus: focus.value
    })
  )
  await execute(async () => {
    reports.value = await api.history()
  })
}
async function open(id) {
  await execute(async () => {
    selected.value = (await run(id)).result
  })
}
</script>

<template>
  <p class="eyebrow">05 / CONTROLLED BUSINESS WORKFLOW</p>
  <h1>按统一口径，完成月度复盘</h1>
  <p class="intro">
    固定步骤计算指标、检索适用材料、生成报告并检查证据。核心数字来自确定性查询，支持历史报告回看。
  </p>
  <section class="panel">
    <form @submit.prevent="submit">
      <div class="controls">
        <label>
          报告月份
          <input v-model="month" type="month" min="2025-05" max="2026-09" :disabled="busy" />
        </label>
        <label>
          部门范围
          <select v-model="departmentId" :disabled="busy">
            <option value="">全部部门</option>
            <option v-for="(name, i) in ['华东', '华南', '华北', '华中']" :key="name" :value="i + 1">
              {{ name }}
            </option>
          </select>
        </label>
      </div>
      <label>
        关注事项
        <input v-model="focus" :disabled="busy" />
      </label>
      <button class="section-space" :disabled="busy">{{ busy ? "生成报告中…" : "生成经营复盘" }}</button>
    </form>
  </section>
  <p v-if="error || pageError" class="error" role="alert">{{ error || pageError }}</p>
  <JobProgress :job="job" :busy="busy" @cancel="stop" />
  <template v-if="result">
    <p v-if="!result.quality_checks.passed" class="notice">
      报告需核对：{{ result.quality_checks.issues.join("；") }}
    </p>
    <div class="metric-grid">
      <div v-for="(name, key) in labels" :key="key" class="metric">
        <p>{{ name }}</p>
        <strong>{{ format(key, result.metrics.current[key]) }}</strong>
      </div>
    </div>
    <section class="panel">
      <h2>{{ result.report.title }}</h2>
      <p class="answer">{{ result.report.summary }}</p>
      <h3>关键发现</h3>
      <ul>
        <li v-for="(item, i) in result.report.findings" :key="i">
          {{ labels[item.metric] }}：{{ format(item.metric, result.metrics.current[item.metric]) }} ·
          {{ item.interpretation }}
        </li>
      </ul>
      <h3>有依据的建议</h3>
      <ul>
        <li v-for="(item, i) in result.report.recommendations" :key="i">
          {{ item.action }}
          <small>{{ item.evidence_ids.join(" · ") }}</small>
        </li>
      </ul>
      <p v-for="item in result.report.uncertainties" :key="item" class="muted">{{ item }}</p>
      <EvidenceList :documents="result.documents" />
    </section>
  </template>
  <section v-if="reports.length" class="panel">
    <h2>历史报告</h2>
    <div v-for="item in reports" :key="item.id" class="row between evidence">
      <span>{{ JSON.parse(item.metadata).month }} · {{ item.status }}</span>
      <button class="link-button" :disabled="busy" @click="open(item.id)">查看报告</button>
    </div>
  </section>
</template>
