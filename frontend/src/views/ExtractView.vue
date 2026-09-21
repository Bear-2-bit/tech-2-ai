<script setup>
import { ref } from "vue"

import { extractTask } from "../api/extraction"


const text = ref("")

const result = ref(null)

const model = ref("")
const finishReason = ref("")
const usage = ref(null)
const latencyMs = ref(0)
const attempts = ref(0)

const loading = ref(false)
const error = ref("")


async function handleSubmit() {
  const inputText = text.value.trim()

  if (!inputText || loading.value) {
    return
  }


  loading.value = true

  error.value = ""

  result.value = null


  try {
    const data = await extractTask({
      text: inputText,
    })


    result.value = data.result

    model.value = data.model

    finishReason.value =
      data.finish_reason || ""

    usage.value = data.usage

    latencyMs.value =
      data.latency_ms

    attempts.value =
      data.attempts


  } catch (err) {
    console.error(err)


    const status =
      err.response?.status


    if (status === 504) {
      error.value =
        "LLM 请求超时。"

    } else if (status === 502) {
      error.value =
        "LLM 无法生成符合要求的结构化结果。"

    } else if (status === 422) {
      error.value =
        "输入数据格式错误。"

    } else {
      error.value =
        "请求失败，请稍后重试。"
    }


  } finally {
    loading.value = false
  }
}
</script>


<template>
  <main>

    <h1>
      tech-2-ai / Extract
    </h1>


    <section>
      <h2>
        Input
      </h2>


      <form
        @submit.prevent="handleSubmit"
      >

        <textarea
          v-model="text"
          rows="6"
          cols="70"
          placeholder="请输入需要抽取的任务描述"
        />


        <br />


        <button
          type="submit"
          :disabled="loading"
        >
          {{
            loading
              ? "抽取中..."
              : "Extract"
          }}
        </button>

      </form>
    </section>


    <p v-if="error">
      {{ error }}
    </p>


    <section v-if="result">

      <hr />

      <h2>
        Structured Result
      </h2>


      <p>
        Title：
        {{ result.title }}
      </p>


      <p>
        Priority：
        {{ result.priority }}
      </p>


      <p>
        Deadline：
        {{ result.deadline || "null" }}
      </p>


      <p>
        Technologies：
        {{
          result.technologies.length
            ? result.technologies.join(", ")
            : "[]"
        }}
      </p>

    </section>


    <section v-if="model">

      <hr />

      <h2>
        LLM Info
      </h2>


      <p>
        Model：
        {{ model }}
      </p>


      <p>
        Finish Reason：
        {{ finishReason }}
      </p>


      <p>
        Attempts：
        {{ attempts }}
      </p>


      <p>
        Latency：
        {{ latencyMs.toFixed(2) }} ms
      </p>


      <div v-if="usage">

        <p>
          Prompt Tokens：
          {{ usage.prompt_tokens }}
        </p>

        <p>
          Completion Tokens：
          {{ usage.completion_tokens }}
        </p>

        <p>
          Total Tokens：
          {{ usage.total_tokens }}
        </p>

      </div>

    </section>

  </main>
</template>