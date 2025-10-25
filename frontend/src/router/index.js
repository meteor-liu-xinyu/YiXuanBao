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
  { path: '/', component: Welcome }, // 默认进入 Welcome
  { path: '/home', redirect: '/' },
  { path: '/welcome', redirect: '/' },
  { path: '/login', component: Login, meta: { hideUserMenu: true } },
  { path: '/register', component: Register, meta: { hideUserMenu: true } },
  { path: '/profile', component: Profile, meta: { hideUserMenu: true } },
  { path: '/recommend', component: Recommend },
  { path: '/result', component: Result },
  { path: '/admin', component: Admin, meta: { hideUserMenu: true } },
  { path: '/history', name: 'History', component: () => import('@/views/History.vue') },

  // catch-all: 如果路径本身不匹配任何已知路由，重定向到 welcome
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})


/**
 * Allowed query keys per route (only these query params are accepted).
 * 如果 URL 中包含了不在 allow 列表里的查询参数，则重定向到 welcome 页面。
 *
 * - 对于没有在表里的 routePath，将使用 globalAllowed 作为白名单。
 * - 如果你需要为更多路由支持额外参数，可在这里扩展。
 */
const globalAllowed = new Set(['next']) // 全局允许的通用参数
const allowedQueryKeysMap = {
  '/recommend': new Set([
    'name', 'gender', 'age', 'disease_code', 'disease_label', 'disease_vector',
    'disease_description', 'past_history', 'economic_level', 'region', 'region_cascader',
    'health_risk', 'urgency', 'urgency_value', 'history_satisfaction',
    'user_lat', 'user_lng', 'prefill', 'next'
  ]),
  '/result': new Set([
    // result 页面允许从外部传入的 payload 字段（通常通过 state 传递，但在 query 中也允许这些字段）
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
  const userStore = useUserStore()

  // 1) 校验查询参数是否合法（如果包含未在白名单内的参数，则重定向到 welcome）
  try {
    const keys = Object.keys(to.query || {})
    if (keys && keys.length) {
      const allowed = allowedQueryKeysMap[to.path] ?? globalAllowed
      const unknown = keys.find(k => !allowed.has(k))
      if (unknown) {
        // 发现非法查询参数，重定向到 welcome（不继续后面的权限检查）
        return next({ path: '/' })
      }
    }
  } catch (e) {
    // 出现异常则安全退回
    return next({ path: '/' })
  }

  // 2) 若 store 未加载但存在 sessionid cookie，则尝试 fetchUser 以便后续权限判断
  const hasSessionCookie = document.cookie.includes('sessionid=')
  if (!userStore.isAuthenticated && hasSessionCookie) {
    try {
      await userStore.fetchUser()
    } catch (e) {
      // ignore fetch errors, userStore stays unauthenticated
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