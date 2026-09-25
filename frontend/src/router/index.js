import {
  createRouter,
  createWebHistory,
} from "vue-router"

import ChatView from "../views/ChatView.vue"

import ExtractView from "../views/ExtractView.vue"

import SearchView from "../views/SearchView.vue"

import RAGView from "../views/RAGView.vue"

import SQLView from "../views/SQLView.vue"

import AgentView from "../views/AgentView.vue"

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

    {
      path: "/extract",
      component: ExtractView,
    },
    { 
      path: "/search",
      component: SearchView,
    },
    {
      path: "/rag",
      component: RAGView,
    },
    {
      path: "/sql",
      component: SQLView,
    },
    {
      path: "/agent",
      component: AgentView,
    },
  ],
})


export default router