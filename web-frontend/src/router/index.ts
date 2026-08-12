import { createRouter, createWebHistory } from 'vue-router'
import {
  NO_MENU_CHECK_PATHS,
  PATH_MENU_MAP,
  PUBLIC_PATHS,
} from '../constants/menus'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { title: '登录', public: true },
    },
    {
      path: '/change-password',
      name: 'change-password',
      component: () => import('../views/ChangePasswordView.vue'),
      meta: { title: '修改密码' },
    },
    {
      path: '/403',
      name: 'forbidden',
      component: () => import('../views/ForbiddenView.vue'),
      meta: { title: '无权限' },
    },
    {
      path: '/',
      component: () => import('../layouts/WorkbenchLayout.vue'),
      children: [
        { path: '', redirect: '/chat' },
        {
          path: 'chat',
          name: 'chat',
          component: () => import('../views/ChatView.vue'),
          meta: { title: '对话台' },
        },
        {
          path: 'sites',
          name: 'sites',
          component: () => import('../views/SitesView.vue'),
          meta: { title: '站点清单' },
        },
        {
          path: 'documents',
          name: 'documents',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { title: '文档与任务', hint: 'P0/P1 文档上传与入库任务页（占位）' },
        },
        {
          path: 'settings',
          name: 'settings',
          component: () => import('../views/PlaceholderView.vue'),
          meta: { title: '应用配置', hint: 'App bindings / model_profile 配置页（占位）' },
        },
        {
          path: 'menus',
          name: 'menus',
          component: () => import('../views/MenuManageView.vue'),
          meta: { title: '菜单管理' },
        },
        {
          path: 'orgs',
          name: 'orgs',
          component: () => import('../views/OrgsView.vue'),
          meta: { title: '组织管理' },
        },
        {
          path: 'roles',
          name: 'roles',
          component: () => import('../views/RolesView.vue'),
          meta: { title: '角色管理' },
        },
        {
          path: 'users',
          name: 'users',
          component: () => import('../views/UsersView.vue'),
          meta: { title: '用户管理' },
        },
      ],
    },
  ],
})

let bootstrapped = false

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()
  const isPublic = PUBLIC_PATHS.includes(to.path as (typeof PUBLIC_PATHS)[number])

  if (isPublic) {
    if (auth.isAuthenticated.value && to.path === '/login') {
      const redirect = (to.query.redirect as string) || '/chat'
      if (auth.mustChangePassword.value) {
        return next('/change-password')
      }
      return next(redirect)
    }
    return next()
  }

  if (!bootstrapped && auth.isAuthenticated.value) {
    await auth.bootstrap()
    bootstrapped = true
  }

  if (!auth.isAuthenticated.value) {
    bootstrapped = false
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  if (auth.mustChangePassword.value && to.path !== '/change-password') {
    return next('/change-password')
  }

  const skipMenuCheck = NO_MENU_CHECK_PATHS.includes(
    to.path as (typeof NO_MENU_CHECK_PATHS)[number],
  )
  const menuId = PATH_MENU_MAP[to.path]
  if (!skipMenuCheck && menuId && !auth.hasMenu(menuId)) {
    return next('/403')
  }

  next()
})

router.afterEach((to) => {
  const title = (to.meta.title as string) || 'CACCH AI'
  document.title = `${title} · CACCH AI 智能平台`
})

export default router
