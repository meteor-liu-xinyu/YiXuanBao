import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
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
  // 将 isAdmin 改为计算属性，避免状态不一致
  const isAdmin = computed(() => isStaff.value || isSuperuser.value)

  // 统一 userData（方便外部直接读取完整对象）
  const userData = ref({})

  function clearAuth() {
    username.value = ''
    avatar.value = ''
    avatarTimestamp.value = Date.now()
    isAuthenticated.value = false
    isStaff.value = false
    isSuperuser.value = false
    userData.value = {}
  }

  async function fetchUser() {
    try {
      const res = await api.get('/accounts/userinfo/', { withCredentials: true })
      if (res && res.status === 200 && res.data) {
        const data = res.data
        username.value = data.username || ''
        avatar.value = data.avatar || ''
        isAuthenticated.value = true
        isStaff.value = !!data.is_staff
        isSuperuser.value = !!data.is_superuser
        // store user object for easy consumption by UI
        userData.value = { ...data }
        return data
      } else {
        clearAuth()
        return null
      }
    } catch (e) {
      // 若需要区分错误类型，可在此检查 e.response.status，并返回更细的信息
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
      // 客户端尝试删除 cookie（注意：若有 domain/path/secure 等设置，前端删除可能无效）
      document.cookie = 'sessionid=; Path=/; Max-Age=0'
      document.cookie = 'csrftoken=; Path=/; Max-Age=0'
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
    isAdmin, // computed
    userData, // 新增：完整用户对象
    fetchUser,
    refreshAvatar,
    login,
    register,
    logout,
    clearAuth
  }
})