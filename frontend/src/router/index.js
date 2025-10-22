import { createRouter, createWebHistory } from 'vue-router'
import Login from '@/views/Login.vue'
import Register from '@/views/Register.vue'
import Profile from '@/views/Profile.vue'
import Recommend from '@/views/Recommend.vue'
import Result from '@/views/Result.vue'
import Home from '@/views/Home.vue'

const routes = [
  { path: '/', redirect: '/recommend' },
  { path: '/home', component: Home },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/profile', component: Profile },
  { path: '/recommend', component: Recommend },
  { path: '/result', component: Result }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router