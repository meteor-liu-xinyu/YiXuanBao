import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/api'
import router from '@/router'

function getCookie(name) {
  const match = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return match ? decodeURIComponent(match.pop()) : ''
}

export const useUserStore = defineStore('user', () => {
  const username = ref('')
  const avatar = ref('')
  const avatarTimestamp = ref(Date.now())
  const isAuthenticated = ref(false)
  const isStaff = ref(false)
  const isSuperuser = ref(false)
  const isAdmin = ref(false) // 快捷标志：isStaff || isSuperuser

  function clearAuth() {
    username.value = ''
    avatar.value = ''
    avatarTimestamp.value = Date.now()
    isAuthenticated.value = false
    isStaff.value = false
    isSuperuser.value = false
    isAdmin.value = false
  }

  async function fetchUser() {
    try {
      const res = await api.get('/accounts/userinfo/', { withCredentials: true })
      if (res && res.status === 200 && res.data) {
        const data = res.data
        username.value = data.username || ''
        avatar.value = data.avatar || ''
        isAuthenticated.value = true
        // 后端需返回 is_staff / is_superuser 字段（UserSerializer中包含）
        isStaff.value = !!data.is_staff
        isSuperuser.value = !!data.is_superuser
        isAdmin.value = isStaff.value || isSuperuser.value
        return data
      } else {
        clearAuth()
        return null
      }
    } catch (e) {
      clearAuth()
      return null
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
      // 客户端补偿删除 cookie
      document.cookie = 'sessionid=; Path=/; Max-Age=0'
      document.cookie = 'csrftoken=; Path=/; Max-Age=0'
      // 导航到登录页
      try { router.replace('/login') } catch (err) { /* ignore */ }
    }
  }

  return {
    username,
    avatar,
    avatarTimestamp,
    isAuthenticated,
    isStaff,
    isSuperuser,
    isAdmin,
    fetchUser,
    refreshAvatar,
    login,
    register,
    logout,
    clearAuth
  }
})