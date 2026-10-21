<script setup>
const modules = [
  ["01", "/llm", "LLM", "理解模型"],
  ["02", "/rag", "RAG", "管理知识"],
  ["03", "/nl2sql", "NL2SQL", "查询业务"],
  ["04", "/agent", "Agent", "调查问题"],
  ["05", "/workflow", "Workflow", "经营复盘"],
  ["06", "/engineering", "Engineering", "评估与追踪"]
]
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <RouterLink class="brand" to="/llm">
        <span class="brand-mark">t²</span>
        <span>
          tech-2-ai
          <small>AI APPLICATION WORKBENCH</small>
        </span>
      </RouterLink>
      <p class="nav-label">从模型能力，到业务闭环</p>
      <nav aria-label="功能模块">
        <RouterLink
          v-for="[number, path, name, description] in modules"
          :key="path"
          :to="path"
          class="nav-item"
        >
          <span class="nav-number">{{ number }}</span>
          <span>
            {{ name }}
            <small>{{ description }}</small>
          </span>
          <span class="nav-arrow">↗</span>
        </RouterLink>
      </nav>
      <div class="sidebar-foot">
        <span class="status-dot"></span>
        机器人企业运营 · 演示工作台
        <p>数据范围 2025.04 — 2026.09</p>
        <a href="http://127.0.0.1:8000/docs" target="_blank" rel="noreferrer">API 文档 ↗</a>
      </div>
    </aside>
    <main class="main-content"><RouterView /></main>
  </div>
</template>
