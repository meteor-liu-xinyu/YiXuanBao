import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/api'

export const useUserStore = defineStore('user', () => {
  const username = ref('未登录')
  const avatar = ref('')
  const avatarTimestamp = ref(Date.now())
  const isAuthenticated = ref(false)

  async function fetchUser() {
    try {
      // GET accounts/userinfo/ 需后端返回 user + profile info
      const res = await api.get('accounts/userinfo/')
      if (res.status === 200 && res.data.username) {
        username.value = res.data.username
        avatar.value = res.data.avatar || ''
        isAuthenticated.value = true
      } else {
        isAuthenticated.value = false
      }
    } catch (e) {
      isAuthenticated.value = false
    }
  }

  function refreshAvatar(newUrl) {
    avatar.value = newUrl
    avatarTimestamp.value = Date.now()
  }

  async function login(payload) {
    // payload: { username, password }
    const res = await api.post('accounts/login/', payload)
    if (res.status === 200) {
      await fetchUser()
      return true
    }
    return false
  }

  async function register(payload) {
    const res = await api.post('accounts/register/', payload)
    return res
  }

  async function logout() {
    await api.post('accounts/logout/')
    isAuthenticated.value = false
    username.value = '未登录'
    avatar.value = ''
  }

  return {
    username, avatar, avatarTimestamp, isAuthenticated,
    fetchUser, refreshAvatar, login, register, logout
  }
})