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

import WorkflowView from "../views/WorkflowView.vue"

import EvalView from "../views/EvalView.vue"

import TracesView from "../views/TracesView.vue"

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
    {
      path: "/workflow",
      component: WorkflowView,
    },  
    
    {
      path: "/eval",
      component: EvalView,
    },
    {
      path: "/traces",
      component: TracesView,
    },
  ],
})


export default router