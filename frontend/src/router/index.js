import { createRouter, createWebHistory } from 'vue-router'
import Welcome from '@/views/Welcome.vue'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Profile from '@/views/Profile.vue'
import Recommend from '@/views/Recommend.vue'
import Result from '@/views/Result.vue'

const routes = [
  { path: '/', component: Welcome }, // 默认进入 Welcome
  { path: '/home', redirect: '/' },
  { path: '/welcome', redirect: '/' },
  { path: '/login', component: Login, meta: { hideUserMenu: true } },
  { path: '/register', component: Register, meta: { hideUserMenu: true } },
  { path: '/profile', component: Profile, meta: { hideUserMenu: true } },
  { path: '/recommend', component: Recommend },
  { path: '/result', component: Result }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router