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
      meta: { title: '站点清单', layout: 'workbench' },
    },
    {
      path: '/documents',
      name: 'documents',
      component: () => import('../views/PlaceholderView.vue'),
      meta: { title: '文档与任务', layout: 'workbench', hint: 'P0/P1 文档上传与入库任务页（占位）' },
    },
    {
      path: '/settings',
      name: 'settings',
      component: () => import('../views/PlaceholderView.vue'),
      meta: { title: '应用配置', layout: 'workbench', hint: 'App bindings / model_profile 配置页（占位）' },
    },
  ],
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || 'CACCH AI'
  document.title = `${title} · CACCH AI`
})

export default router
