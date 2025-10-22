import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/api'

function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return match ? decodeURIComponent(match.pop()) : ''
}

export const useUserStore = defineStore('user', () => {
  const username = ref('')
  const avatar = ref('')
  const avatarTimestamp = ref(Date.now())
  const isAuthenticated = ref(false)

  function clearAuth() {
    username.value = ''
    avatar.value = ''
    avatarTimestamp.value = Date.now()
    isAuthenticated.value = false
  }

  async function fetchUser() {
    try {
      const res = await api.get('/accounts/userinfo/', { withCredentials: true })
      if (res && res.status === 200 && res.data && res.data.username) {
        username.value = res.data.username || ''
        avatar.value = res.data.avatar || ''
        isAuthenticated.value = true
      } else {
        clearAuth()
      }
    } catch (e) {
      clearAuth()
    }
  }

  function refreshAvatar(newUrl) {
    avatar.value = newUrl
    avatarTimestamp.value = Date.now()
  }

  async function login(payload) {
    try {
      const csrftoken = getCookie('csrftoken')
      const headers = {}
      if (csrftoken) headers['X-CSRFToken'] = csrftoken
      const res = await api.post('/accounts/login/', payload, { withCredentials: true, headers })
      if (res && (res.status === 200 || res.status === 201)) {
        await fetchUser()
        return true
      }
      return false
    } catch (e) {
      clearAuth()
      return false
    }
  }

  async function register(payload) {
    const csrftoken = getCookie('csrftoken')
    const headers = {}
    if (csrftoken) headers['X-CSRFToken'] = csrftoken
    return api.post('/accounts/register/', payload, { withCredentials: true, headers })
  }

  async function logout() {
    try {
      const csrftoken = getCookie('csrftoken')
      const headers = {}
      if (csrftoken) headers['X-CSRFToken'] = csrftoken
      await api.post('/accounts/logout/', {}, { withCredentials: true, headers })
    } catch (e) {
      // ignore; still clear client state
    } finally {
      clearAuth()
      // 尝试本地删除 cookie（客户端补偿）
      document.cookie = 'sessionid=; Path=/; Max-Age=0'
      document.cookie = 'csrftoken=; Path=/; Max-Age=0'
      // 推荐在 logout UI 调用后做 router.replace('/login')
    }
  }

  return { username, avatar, avatarTimestamp, isAuthenticated, fetchUser, refreshAvatar, login, register, logout, clearAuth }
})