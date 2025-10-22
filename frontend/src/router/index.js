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
]

const router = createRouter({
  history: createWebHistory(),
  routes
})


router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()

  // 如果 store 还没加载用户，但页面需要认证/管理员权限，尝试拉取一次 user
  const hasSessionCookie = document.cookie.includes('sessionid=')
  if (!userStore.isAuthenticated && hasSessionCookie) {
    // 等待 fetchUser 完成以便判断权限
    await userStore.fetchUser()
  }

  if (to.meta && to.meta.requiresAdmin) {
    if (!userStore.isAuthenticated) {
      // 未登录 -> 去登录页
      return next({ path: '/login', query: { next: to.fullPath } })
    }
    if (!userStore.isAdmin) {
      // 已登录但不是管理员 -> 直接跳转到 welcome 页面（不提示）
      return next({ path: '/welcome' })
    }
    return next()
  }

  if (to.meta && to.meta.requiresAuth) {
    if (!userStore.isAuthenticated) {
      return next({ path: '/login', query: { next: to.fullPath } })
    }
  }

  next()
})

export default router