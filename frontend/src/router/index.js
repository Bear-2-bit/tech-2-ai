import {
  createRouter,
  createWebHistory,
} from "vue-router"

import ChatView from "../views/ChatView.vue"

import ExtractView from "../views/ExtractView.vue"

import SearchView from "../views/SearchView.vue"

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

  ],
})


export default router