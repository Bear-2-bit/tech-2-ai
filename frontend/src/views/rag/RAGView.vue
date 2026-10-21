<script setup>
import { onMounted, ref } from "vue"
import * as api from "../../api/rag"
import EvidenceList from "../../components/EvidenceList.vue"
import JobProgress from "../../components/JobProgress.vue"
import RunInfo from "../../components/RunInfo.vue"
import { useJob } from "../../composables/useJob"
import { useOperation } from "../../composables/useOperation"

const tab = ref("documents")
const overview = ref(null)
const documents = ref([])
const file = ref(null)
const category = ref("general")
const productCode = ref("")
const effectiveFrom = ref("2025-04-01")
const query = ref("机器人A的保修范围和退货要求是什么？")
const topK = ref(5)
const rerank = ref(false)
const rewrite = ref(false)
const result = ref(null)
const { job, busy: indexing, error: indexError, start, stop } = useJob()
const { busy, error, execute } = useOperation()

async function refresh() {
  ;[overview.value, documents.value] = await Promise.all([api.status(), api.documents()])
}
onMounted(() => execute(refresh))
function switchTab(key) {
  tab.value = key
  result.value = null
}
async function upload() {
  if (!file.value) return
  const data = new FormData()
  data.append("file", file.value)
  data.append("category", category.value)
  data.append("product_code", productCode.value)
  data.append("effective_from", effectiveFrom.value)
  await start(() => api.upload(data))
  await execute(refresh)
}
async function seed() {
  await start(api.seed)
  await execute(refresh)
}
async function remove(id) {
  await execute(async () => {
    await api.remove(id)
    await refresh()
  })
}
async function submit() {
  result.value = null
  await execute(async (signal) => {
    const payload = { query: query.value, top_k: topK.value, rerank: rerank.value, rewrite: rewrite.value }
    result.value = await (tab.value === "search" ? api.search(payload, signal) : api.ask(payload, signal))
  })
}
</script>

<template>
  <p class="eyebrow">02 / KNOWLEDGE LIFECYCLE</p>
  <h1>让知识成为可验证的依据</h1>
  <p class="intro">先管理文档与版本，再观察检索证据，最后生成有来源的回答。三个阶段共享同一条检索链。</p>
  <div class="metric-grid">
    <div class="metric">
      <p>已发布文档</p>
      <strong>{{ overview?.document_count ?? "—" }}</strong>
    </div>
    <div class="metric">
      <p>有效片段</p>
      <strong>{{ overview?.chunk_count ?? "—" }}</strong>
    </div>
    <div class="metric">
      <p>知识状态</p>
      <strong style="font-size: 17px">{{ overview?.status === "ready" ? "可检索" : "等待入库" }}</strong>
    </div>
  </div>
  <div class="tabs">
    <button
      v-for="[key, name] in [
        ['documents', '1. 知识管理'],
        ['search', '2. 检索实验'],
        ['ask', '3. 知识问答']
      ]"
      :key="key"
      :class="{ active: tab === key }"
      :disabled="busy"
      @click="switchTab(key)"
    >
      {{ name }}
    </button>
  </div>
  <p v-if="error || indexError" class="error" role="alert">{{ error || indexError }}</p>
  <template v-if="tab === 'documents'">
    <section class="panel">
      <h2>文档入库</h2>
      <p class="muted">支持 UTF-8 TXT、Markdown 与有文字层的 PDF。同名文档更新版本，相同内容与元数据不会重复入库。</p>
      <div class="controls">
        <label
          >选择文件<input
            type="file"
            accept=".txt,.md,.pdf"
            :disabled="indexing"
            @change="file = $event.target.files[0]" /></label
        ><label>分类<input v-model="category" maxlength="100" /></label
        ><label>产品编号<input v-model="productCode" placeholder="可选，如 ROBOT-A" /></label
        ><label>生效日期<input v-model="effectiveFrom" type="date" /></label>
      </div>
      <div class="row">
        <button :disabled="indexing || !file" @click="upload">{{ indexing ? "处理中…" : "上传并入库" }}</button
        ><button class="secondary" :disabled="indexing" @click="seed">导入项目示例知识</button
        ><button class="secondary" :disabled="busy" @click="execute(refresh)">刷新列表</button>
      </div>
    </section>
    <JobProgress :job="job" :busy="indexing" @cancel="stop" />
    <section class="panel table-wrap">
      <h2>文档与版本</h2>
      <table>
        <thead>
          <tr>
            <th>文档</th>
            <th>版本</th>
            <th>状态</th>
            <th>片段</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="doc in documents" :key="doc.id">
            <td>
              <a
                v-if="['ready', 'superseded'].includes(doc.status)"
                :href="api.sourceURL(doc.id)"
                target="_blank"
                rel="noreferrer"
                >{{ doc.filename }} ↗</a
              >
              <span v-else>{{ doc.filename }}</span
              ><small v-if="doc.error"><br />{{ doc.error }}</small>
            </td>
            <td>v{{ doc.version }}</td>
            <td>{{ doc.status }}</td>
            <td>{{ doc.chunk_count }}</td>
            <td>
              <button
                v-if="['ready', 'error', 'deleting'].includes(doc.status)"
                class="link-button"
                :disabled="busy || indexing"
                @click="remove(doc.document_id)"
              >
                删除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      <p v-if="!documents.length" class="empty">还没有知识文档，可以先导入项目示例。</p>
    </section>
  </template>
  <template v-else>
    <section class="panel">
      <form @submit.prevent="submit">
        <textarea v-model="query" rows="3" placeholder="输入与企业资料相关的问题" :disabled="busy" />
        <div class="controls section-space">
          <label>Top K<input v-model.number="topK" type="number" min="1" max="20" /></label
          ><label class="check"><input v-model="rerank" type="checkbox" />启用重排</label
          ><label class="check"><input v-model="rewrite" type="checkbox" />启用查询改写</label
          ><button :disabled="busy || !query.trim()">
            {{ busy ? "处理中…" : tab === "search" ? "检索证据" : "生成回答" }}
          </button>
        </div>
      </form>
      <p class="muted">重排按需加载本地模型；首次使用前需完成模型准备。</p>
    </section>
    <section v-if="result" class="panel">
      <h2>{{ tab === "search" ? "检索结果" : "基于证据的回答" }}</h2>
      <p v-if="result.answer" class="answer">{{ result.answer }}</p>
      <p v-if="result.status === 'incomplete'" class="notice">证据或引用校验不足，结果需要核对。</p>
      <p v-if="result.rewritten_query !== result.query" class="muted">改写查询：{{ result.rewritten_query }}</p>
      <h3 v-if="result.citations?.length">实际引用</h3>
      <EvidenceList :documents="result.citations || []" />
      <h3 class="section-space">候选证据</h3>
      <EvidenceList :documents="result.documents" />
      <p v-if="!result.documents.length" class="empty">当前没有符合条件的已发布知识。</p>
      <RunInfo :data="result" />
    </section>
  </template>
</template>
