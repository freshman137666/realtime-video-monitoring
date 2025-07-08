import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/home',
      name: 'home',
      component: () => import('../views/HomeView.vue')
    },
    {
      path: '/about',
      name: 'about',
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/monitor',
      name: 'monitor',
      component: () => import('../views/MonitorView.vue')
    },
    {
      path: '/alart',
      name: 'alart',
      component: () => import('../views/AlertView.vue')
    },
    // 新增登录路由
    {
      path: '/',
      name: 'login',
      component: () => import('../views/LoginView.vue')
    }
    ,
    // 新增注册路由
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/RegisterView.vue')
    }
  ]
})

export default router