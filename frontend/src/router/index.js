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
  // 公开页面
  { 
    path: '/', 
    component: Welcome 
  },
  { 
    path: '/home', 
    redirect: '/' 
  },
  { 
    path: '/welcome', 
    redirect: '/' 
  },
  
  // 认证相关（不需要登录）
  { 
    path: '/login', 
    component: Login, 
    meta: { hideUserMenu: true } 
  },
  { 
    path: '/register', 
    component: Register, 
    meta: { hideUserMenu: true } 
  },
  
  // 需要登录的页面
  { 
    path: '/profile', 
    component: Profile, 
    meta: { 
      hideUserMenu: true,
      requiresAuth: true
    } 
  },
  
  // 推荐功能
  { 
    path: '/recommend', 
    component: Recommend 
  },
  { 
    path: '/result', 
    component: Result 
  },
  
  // 历史记录（需要登录）
  { 
    path: '/history', 
    name: 'History', 
    component: () => import('@/views/History.vue'),
    meta: { requiresAuth: true }
  },
  
  // 管理员页面（需要管理员权限）
  { 
    path: '/admin', 
    component: Admin, 
    meta: { 
      hideUserMenu: true,
      requiresAuth: true,
      requiresAdmin: true
    } 
  },

  // 404 捕获
  { 
    path: '/:pathMatch(.*)*', 
    redirect: '/' 
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 全局查询参数白名单
const globalAllowed = new Set(['next'])

// 每个路由允许的查询参数
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
  // ⭐ 排除后端路由，跳过 Vue Router，使用原生导航
  const backendPaths = ['/django-admin', '/api', '/static', '/media'];
  
  if (backendPaths.some(path => to.path.startsWith(path))) {
    window.location.href = to.fullPath;
    return;
  }

  const userStore = useUserStore()

  // 1. 查询参数验证
  try {
    const keys = Object.keys(to.query || {})
    if (keys && keys.length) {
      const allowed = allowedQueryKeysMap[to.path] ?? globalAllowed
      const unknown = keys.find(k => !allowed.has(k))
      if (unknown) {
        console.warn(`⚠️ 非法查询参数: ${unknown} 在路由 ${to.path}`)
        return next({ path: '/' })
      }
    }
  } catch (e) {
    console.error('路由参数验证错误:', e)
    return next({ path: '/' })
  }

  // 2. 尝试恢复用户会话
  const hasSessionCookie = document.cookie.includes('sessionid=')
  if (!userStore.isAuthenticated && hasSessionCookie) {
    try {
      await userStore.fetchUser()
    } catch (e) {
      // Session 可能已过期，忽略错误
      console.debug('Session 恢复失败:', e.message)
    }
  }

  // 3. 管理员权限检查（最高优先级）
  if (to.meta && to.meta.requiresAdmin) {
    if (!userStore.isAuthenticated) {
      console.log('未登录，重定向到登录页')
      return next({ path: '/login', query: { next: to.fullPath } })
    }
    if (!userStore.isAdmin) {
      console.warn('⚠️ 非管理员用户尝试访问管理页面')
      return next({ path: '/' })
    }
    return next()
  }

  // 4. 普通登录保护
  if (to.meta && to.meta.requiresAuth) {
    if (!userStore.isAuthenticated) {
      console.log('需要登录，重定向到登录页')
      return next({ path: '/login', query: { next: to.fullPath } })
    }
  }

  next()
})

export default router