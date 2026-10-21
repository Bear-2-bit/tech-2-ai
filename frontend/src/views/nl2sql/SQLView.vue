<script setup>
import { onMounted, ref } from "vue"
import * as api from "../../api/nl2sql"
import RunInfo from "../../components/RunInfo.vue"
import { useOperation } from "../../composables/useOperation"

const definition = ref(null)
const question = ref("查询2026年9月各部门已完成订单的销售额，按销售额降序排列，金额以元显示。")
const result = ref(null)
const { busy, error, execute } = useOperation()
onMounted(() =>
  execute(async () => {
    definition.value = await api.schema()
  })
)
async function submit() {
  result.value = null
  await execute(async (signal) => {
    result.value = await api.query({ question: question.value }, signal)
  })
}
</script>

<template>
  <p class="eyebrow">03 / NATURAL LANGUAGE TO SQL</p>
  <h1>从业务问题，到数据事实</h1>
  <p class="intro">查询销售、订单、退款与售后数据。生成的 SQL 经过结构检查，在只读连接和执行预算内运行。</p>
  <details v-if="definition" class="panel">
    <summary>查看 {{ definition.tables.length }} 张业务表与指标口径</summary>
    <div class="steps">
      <details v-for="table in definition.tables" :key="table.name" class="evidence">
        <summary>{{ table.name }} · {{ table.row_count }} 行</summary>
        <p class="muted">{{ table.description }}</p>
        <p v-for="column in table.columns" :key="column.name" class="mono">
          {{ column.name }}
          <small>{{ column.type }}</small>
          <small v-if="column.values">
            ·
            {{
              Object.entries(column.values)
                .map(([key, text]) => `${key}=${text}`)
                .join("；")
            }}
          </small>
        </p>
      </details>
    </div>
    <p class="preserve muted">{{ definition.metric_definitions }}</p>
  </details>
  <section class="panel">
    <form @submit.prevent="submit">
      <label>
        你想了解什么？
        <textarea v-model="question" rows="3" :disabled="busy" />
      </label>
      <button class="section-space" :disabled="busy || !question.trim()">
        {{ busy ? "生成与查询中…" : "查询业务数据" }}
      </button>
    </form>
  </section>
  <p v-if="error" class="error" role="alert">{{ error }}</p>
  <section v-if="result" class="panel">
    <h2>查询依据</h2>
    <pre>{{ result.sql }}</pre>
    <p class="muted">{{ result.explanation }}</p>
    <h2 class="section-space">查询结果</h2>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th v-for="column in result.columns" :key="column">{{ column }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(row, i) in result.rows" :key="i">
            <td v-for="(value, j) in row" :key="j">{{ value ?? "NULL" }}</td>
          </tr>
        </tbody>
      </table>
    </div>
    <p class="muted section-space">
      返回 {{ result.row_count }} 行
      <span v-if="result.truncated">· 结果已截断，不能把它当作完整数据集</span>
    </p>
    <RunInfo :data="result" />
  </section>
</template>
