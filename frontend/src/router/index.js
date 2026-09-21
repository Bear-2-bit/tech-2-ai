import { createRouter, createWebHistory } from "vue-router"
import ChatView from "../views/ChatView.vue"

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      redirect: "/chat",
    },
    {
      path: "/chat",
      component: ChatView,
    },
  ],
})

export default router