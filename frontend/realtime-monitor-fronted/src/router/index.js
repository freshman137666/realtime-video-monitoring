import { createRouter, createWebHistory } from 'vue-router'


const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue')  // 将监控视图设置为默认页面
    },
    {
      path: '/about',
      name: 'about',
      // route level code-splitting
      // this generates a separate chunk (About.[hash].js) for this route
      // which is lazy-loaded when the route is visited.
      component: () => import('../views/AboutView.vue')
    },
    {
      path: '/monitor',
      name: 'monitor',
      component: () => import('../views/MonitorView.vue')
    },
    {
    path: '/alert',
    name: 'alert',
    component: () => import('../views/AlertView.vue')
    },
    {
    path: '/face',
    name: 'face',
    component: () => import('../views/FaceView.vue')
    },
    {
    path: '/device',
    name: 'device',
    component: () => import('../views/DeviceView.vue')
    },
  ]
})

export default router 