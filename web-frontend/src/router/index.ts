import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/chat' },
    {
      path: '/chat',
      name: 'chat',
      component: () => import('../views/ChatView.vue'),
      meta: { title: '对话台' },
    },
    {
      path: '/sites',
      name: 'sites',
      component: () => import('../views/SitesView.vue'),
      meta: { title: '站点清单' },
    },
    {
      path: '/documents',
      name: 'documents',
      component: () => import('../views/PlaceholderView.vue'),
      meta: { title: '文档与任务', hint: 'P0/P1 文档上传与入库任务页（占位）' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/PlaceholderView.vue'),
      meta: { title: '应用配置', hint: 'App bindings / model_profile 配置页（占位）' },
    },
    {
      path: '/menus',
      name: 'menus',
      component: () => import('../views/MenuManageView.vue'),
      meta: { title: '菜单管理' },
    },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || 'CACCH AI'
  document.title = `${title} · CACCH AI 智能平台`
})

export default router
