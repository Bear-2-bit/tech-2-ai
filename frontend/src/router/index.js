import { createRouter, createWebHistory } from "vue-router"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/llm" },
    { path: "/llm", component: () => import("../views/llm/LLMView.vue") },
    { path: "/rag", component: () => import("../views/rag/RAGView.vue") },
    { path: "/nl2sql", component: () => import("../views/nl2sql/SQLView.vue") },
    { path: "/agent", component: () => import("../views/agent/AgentView.vue") },
    { path: "/workflow", component: () => import("../views/workflow/WorkflowView.vue") },
    { path: "/engineering", component: () => import("../views/engineering/EngineeringView.vue") },
    ...["/chat", "/extract"].map((path) => ({ path, redirect: "/llm" })),
    { path: "/search", redirect: "/rag" },
    { path: "/sql", redirect: "/nl2sql" },
    ...["/eval", "/traces"].map((path) => ({ path, redirect: "/engineering" })),
    { path: "/:pathMatch(.*)*", redirect: "/llm" }
  ]
})

export default router
