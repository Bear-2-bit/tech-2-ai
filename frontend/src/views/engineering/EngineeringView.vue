<script setup>
import { onMounted, ref } from "vue"
import { useRoute } from "vue-router"
import * as api from "../../api/engineering"
import JobProgress from "../../components/JobProgress.vue"
import { useJob } from "../../composables/useJob"
import { useOperation } from "../../composables/useOperation"

const route = useRoute()
const tab = ref(route.query.run ? "traces" : "eval")
const cases = ref([])
const types = ref(["sql"])
const limit = ref(5)
const runs = ref([])
const logs = ref([])
const detail = ref(null)
const { job, busy, error, start, stop } = useJob()
const { error: pageError, execute } = useOperation()
async function refresh() {
  ;[runs.value, logs.value, cases.value] = await Promise.all([api.runs(), api.logs(), api.cases()])
}
async function open(id) {
  await execute(async () => {
    detail.value = await api.run(id)
  })
}
function showRun(id) {
  tab.value = "traces"
  return open(id)
}
onMounted(async () => {
  await execute(refresh)
  if (route.query.run) await open(route.query.run)
})
async function evaluate() {
  await start(() => api.evaluate({ types: types.value, limit: limit.value }))
  await execute(refresh)
}
</script>

<template>
  <p class="eyebrow">06 / EVALUATE · TRACE · OBSERVE</p>
  <h1>让质量有标准，让过程可追溯</h1>
  <p class="intro">使用版本化用例验证能力，用执行树定位瓶颈与失败，用脱敏事件记录观察运行。</p>
  <div class="tabs">
    <button
      v-for="[key, name] in [
        ['eval', '评估'],
        ['traces', '追踪'],
        ['logs', '日志']
      ]"
      :key="key"
      :class="{ active: tab === key }"
      @click="tab = key"
    >
      {{ name }}
    </button>
    <button @click="execute(refresh)">刷新 ↻</button>
  </div>
  <p v-if="error || pageError" class="error" role="alert">{{ error || pageError }}</p>
  <template v-if="tab === 'eval'">
    <section class="panel">
      <h2>运行回归评估</h2>
      <p class="muted">
        共 {{ cases.length }} 条用例。评估会调用模型；RAG、Agent 与 Workflow
        用例需要已入库知识。先选少量用例确认环境。
      </p>
      <div class="controls">
        <label v-for="type in ['llm', 'sql', 'rag', 'agent', 'workflow']" :key="type" class="check">
          <input v-model="types" type="checkbox" :value="type" :disabled="busy" />
          {{ type.toUpperCase() }}
        </label>
        <label>
          最多用例数
          <input v-model.number="limit" type="number" min="1" max="60" />
        </label>
        <button :disabled="busy || !types.length" @click="evaluate">
          {{ busy ? "评估中…" : "开始评估" }}
        </button>
      </div>
    </section>
    <JobProgress :job="job" :busy="busy" @cancel="stop" />
    <section v-if="job?.result || job?.eval_results?.length" class="panel">
      <h2>{{ job.result ? `通过 ${job.result.passed} / ${job.result.total}` : "已完成用例（部分结果）" }}</h2>
      <table>
        <thead>
          <tr>
            <th>用例</th>
            <th>结果</th>
            <th>分数</th>
            <th>检查与错误</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in job.result?.results || job.eval_results" :key="item.case_id">
            <td>{{ item.case_id }}</td>
            <td>{{ item.passed ? "通过" : "未通过" }}</td>
            <td>{{ item.score.toFixed(2) }}</td>
            <td>
              {{ item.error || JSON.stringify(item.checks) }}
              <details>
                <summary>详情</summary>
                <pre>{{ item.details }}</pre>
              </details>
            </td>
          </tr>
        </tbody>
      </table>
    </section>
    <details class="panel">
      <summary>用例目录</summary>
      <div v-for="item in cases" :key="item.id" class="evidence">
        <strong>{{ item.id }}</strong>
        <p class="muted">{{ item.input }}</p>
      </div>
    </details>
  </template>
  <template v-if="tab === 'traces'">
    <section class="panel table-wrap">
      <h2>运行记录</h2>
      <table>
        <thead>
          <tr>
            <th>模块 / 名称</th>
            <th>状态</th>
            <th>耗时</th>
            <th>输入 / 输出 Token</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="item in runs" :key="item.id">
            <td>{{ item.module }} / {{ item.name }}</td>
            <td>{{ item.status }}</td>
            <td>{{ item.latency_ms == null ? "—" : `${(item.latency_ms / 1000).toFixed(2)}s` }}</td>
            <td>{{ item.input_tokens ?? "未知" }} / {{ item.output_tokens ?? "未知" }}</td>
            <td><button class="link-button" @click="open(item.id)">详情</button></td>
          </tr>
        </tbody>
      </table>
      <p v-if="!runs.length" class="empty">尚无运行记录</p>
    </section>
    <section v-if="detail" class="panel">
      <h2>{{ detail.name }} · {{ detail.status }}</h2>
      <p class="muted mono">{{ detail.id }}</p>
      <p v-if="detail.error" class="error">{{ detail.error }}</p>
      <table>
        <thead>
          <tr>
            <th>执行步骤</th>
            <th>状态</th>
            <th>耗时</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="step in detail.spans" :key="step.id">
            <td>{{ step.name }}</td>
            <td>{{ step.status }}</td>
            <td>{{ step.latency_ms == null ? "—" : `${step.latency_ms} ms` }}</td>
          </tr>
        </tbody>
      </table>
      <details class="section-space">
        <summary>运行结果与版本</summary>
        <pre>{{ detail.result || detail.metadata }}</pre>
      </details>
    </section>
  </template>
  <section v-if="tab === 'logs'" class="panel table-wrap">
    <h2>脱敏运行事件</h2>
    <table>
      <thead>
        <tr>
          <th>时间</th>
          <th>等级</th>
          <th>事件</th>
          <th>关联运行</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in logs" :key="item.id">
          <td>{{ new Date(item.created_at).toLocaleString() }}</td>
          <td>{{ item.level }}</td>
          <td>{{ item.message }}</td>
          <td>
            <button v-if="item.run_id" class="link-button" @click="showRun(item.run_id)">
              {{ item.run_id.slice(0, 8) }} ↗
            </button>
          </td>
        </tr>
      </tbody>
    </table>
  </section>
</template>
