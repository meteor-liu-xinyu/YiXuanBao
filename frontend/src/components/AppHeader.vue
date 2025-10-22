<template>
  <div class="main-header" style="display:flex;justify-content:space-between;align-items:center;padding:12px 20px;background:linear-gradient(90deg,#6a85e6,#43cea2);color:#fff;">
    <div class="title" style="font-weight:700">医选宝智能助手</div>
    <div style="display:flex;align-items:center;gap:10px">
      <div v-if="user.isAuthenticated" @click="gotoProfile" style="cursor:pointer;display:flex;align-items:center">
        <img :src="avatarSrc" alt="avatar" style="width:36px;height:36px;border-radius:50%;object-fit:cover;border:2px solid #fff;margin-right:8px"/>
        <span style="color:#fff">{{ user.username }}</span>
      </div>
      <div v-else>
        <el-button type="text" @click="$router.push('/login')" style="color:#fff">登录</el-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useUserStore } from '@/stores/user'
const user = useUserStore()
onMounted(()=>user.fetchUser())

const avatarSrc = computed(()=> {
  if (!user.avatar) return '/default-avatar.png'
  return user.avatar + '?t=' + user.avatarTimestamp
})

function gotoProfile() {
  window.location.href = '/profile'
}
</script>