import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'

import Welcome from '@/views/Welcome.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Profile from '@/views/Profile.vue'
import Recommend from '@/views/Recommend.vue'
import Result from '@/views/Result.vue'
import Admin from '@/views/Admin.vue'

const routes = [
  { path: '/', component: Welcome },
  { path: '/home', redirect: '/' },
  { path: '/welcome', redirect: '/' },
  { path: '/login', component: Login, meta: { hideUserMenu: true } },
  { path: '/register', component: Register, meta: { hideUserMenu: true } },
  { path: '/profile', component: Profile, meta: { hideUserMenu: true, requiresAuth: true } },
  { path: '/recommend', component: Recommend },
  { path: '/result', component: Result },
  { 
    path: '/admin', 
    component: Admin, 
    meta: { 
      hideUserMenu: true,
      requiresAuth: true,
      requiresAdmin: true
    } 
  },
  { 
    path: '/history', 
    name: 'History', 
    component: () => import('@/views/History.vue'),
    meta: { requiresAuth: true }
  },

  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

const globalAllowed = new Set(['next'])
const allowedQueryKeysMap = {
  '/recommend': new Set([
    'name', 'gender', 'age', 'disease_code', 'disease_label', 'disease_vector',
    'disease_description', 'past_history', 'economic_level', 'region', 'region_cascader',
    'health_risk', 'urgency', 'urgency_value', 'history_satisfaction',
    'user_lat', 'user_lng', 'prefill', 'next'
  ]),
  '/result': new Set([
    'name', 'gender', 'age', 'disease_code', 'disease_label',
    'economic_level', 'region', 'health_risk', 'urgency',
    'user_lat', 'user_lng', 'next'
  ]),
  '/history': new Set(['next']),
  '/login': new Set(['next']),
  '/register': new Set(['next']),
  '/profile': new Set(['next']),
  '/admin': new Set(['next'])
}

router.beforeEach(async (to, from, next) => {
  // 排除后端路由
  const backendPaths = ['/django-admin', '/api', '/static', '/media']
  if (backendPaths.some(path => to.path.startsWith(path))) {
    window.location.href = to.fullPath
    return
  }

  const userStore = useUserStore()

  // 1) 查询参数验证
  try {
    const keys = Object.keys(to.query || {})
    if (keys && keys.length) {
      const allowed = allowedQueryKeysMap[to.path] ?? globalAllowed
      const unknown = keys.find(k => !allowed.has(k))
      if (unknown) {
        return next({ path: '/' })
      }
    }
  } catch (e) {
    return next({ path: '/' })
  }

  // 2) ⭐⭐⭐ 修改：只在需要认证的路由才恢复会话 ⭐⭐⭐
  const needsAuth = to.meta?.requiresAuth || to.meta?.requiresAdmin
  
  if (needsAuth && !userStore.isAuthenticated) {
    try {
      await userStore.fetchUser()
    } catch (e) {
      // 会话恢复失败，继续后面的逻辑
    }
  }

  // 3) 管理员权限检查
  if (to.meta && to.meta.requiresAdmin) {
    if (!userStore.isAuthenticated) {
      return next({ path: '/login', query: { next: to.fullPath } })
    }
    if (!userStore.isAdmin) {
      return next({ path: '/' })
    }
    return next()
  }

  // 4) 普通登录保护
  if (to.meta && to.meta.requiresAuth) {
    if (!userStore.isAuthenticated) {
      return next({ path: '/login', query: { next: to.fullPath } })
    }
  }

  next()
})

export default router