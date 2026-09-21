<script setup>
import { ref } from "vue"
import { streamChat } from "../api/chat"


// 当前输入框
const message = ref("")


// system prompt
const systemPrompt = ref(
  "你是一名AI应用工程老师，回答简洁准确。"
)


// 模型参数
const temperature = ref(0.7)
const maxTokens = ref(500)


// 这里保存完整聊天历史
const messages = ref([])


// 模型运行信息
const model = ref("")
const usage = ref(null)
const finishReason = ref("")
const latencyMs = ref(0)

// 页面状态
const loading = ref(false)
const error = ref("")


async function handleSubmit() {
  const text = message.value.trim()

  if (!text || loading.value) {
    return
  }


  const userMessage = {
    role: "user",
    content: text,
  }


  messages.value.push(userMessage)

  message.value = ""

  loading.value = true
  error.value = ""


  const assistantMessage = {
    role: "assistant",
    content: "",
  }

  messages.value.push(
    assistantMessage
  )

  const assistantIndex =
    messages.value.length - 1


  try {

    const requestMessages =
      messages.value.slice(0, -1)


    await streamChat(
      {
        messages: requestMessages,

        system_prompt:
          systemPrompt.value || null,

        temperature:
          temperature.value,

        max_tokens:
          maxTokens.value,
      },

      (data) => {

        if (data.type === "delta") {

          messages.value[
            assistantIndex
          ].content += data.content
        }


        if (data.type === "done") {

          model.value =
            data.model || ""

          finishReason.value =
            data.finish_reason || ""

          latencyMs.value =
            data.latency_ms || 0

          usage.value =
            data.usage
        }

      }
    )

  } catch (err) {

    console.error(err)

    error.value =
      "模型流式请求失败，请稍后重试。"

    // 删除没有成功完成的assistant消息
    messages.value.pop()

  } finally {

    loading.value = false

  }
}
</script>


<template>
  <main>
    <h1>tech-2-ai / Chat</h1>


    <!-- 模型配置 -->
    <section>
      <h2>Settings</h2>

      <div>
        <label>System Prompt</label>
        <br />

        <textarea
          v-model="systemPrompt"
          rows="3"
          cols="70"
        />
      </div>


      <div>
        <label>Temperature：</label>

        <input
          v-model.number="temperature"
          type="number"
          min="0"
          max="2"
          step="0.1"
        />
      </div>


      <div>
        <label>Max Tokens：</label>

        <input
          v-model.number="maxTokens"
          type="number"
          min="1"
        />
      </div>
    </section>


    <hr />


    <!-- 聊天历史 -->
    <section>
      <h2>Messages</h2>

      <p v-if="messages.length === 0">
        暂无消息
      </p>


      <div
        v-for="(item, index) in messages"
        :key="index"
      >
        <strong>
          {{ item.role === "user" ? "User" : "Assistant" }}
        </strong>

        <p>
          {{ item.content }}
        </p>
      </div>
    </section>


    <hr />


    <!-- 输入区域 -->
    <form @submit.prevent="handleSubmit">

      <textarea
        v-model="message"
        rows="4"
        cols="70"
        placeholder="请输入消息"
      />

      <br />

      <button
        type="submit"
        :disabled="loading"
      >
        {{ loading ? "请求中..." : "Send" }}
      </button>

    </form>


    <!-- 错误 -->
    <p v-if="error">
      {{ error }}
    </p>


    <!-- 模型运行信息 -->
    <section v-if="model">

      <hr />

      <h2>LLM Info</h2>

      <p>
        Model：{{ model }}
      </p>

      <p>
        Finish Reason：{{ finishReason }}
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

        <p>
          Latency：{{ latencyMs.toFixed(2) }} ms
        </p>  
              
      </div>

    </section>

  </main>
</template>