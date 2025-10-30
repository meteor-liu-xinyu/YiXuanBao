<template>
  <div class="main-header">
    <div class="title">医选宝智能助手</div>
    <div class="user-section">
      <div v-if="user.isAuthenticated" @click="gotoProfile" class="user-info">
        <img :src="avatarSrc" alt="avatar" class="avatar"/>
        <span class="username">{{ user.username }}</span>
      </div>
      <div v-else>
        <el-button type="text" @click="$router.push('/login')" class="login-btn">登录</el-button>
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

<style scoped>
.main-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 20px;
  background: linear-gradient(90deg, #6a85e6, #43cea2);
  color: #fff;
  min-height: 60px;
  box-sizing: border-box;
}

.title {
  font-weight: 700;
  font-size: 18px;
  white-space: nowrap;
  flex-shrink: 0;
}

.user-section {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
  margin-left: auto;
}

.user-info {
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 8px;
  border-radius: 20px;
  transition: background-color 0.3s;
}

.user-info:hover {
  background-color: rgba(255, 255, 255, 0.15);
}

.avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  border: 2px solid #fff;
  flex-shrink: 0;
}

.username {
  color: #fff;
  font-weight: 500;
  white-space: nowrap;
}

.login-btn {
  color: #fff !important;
  font-weight: 500;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .main-header {
    padding: 10px 15px;
    min-height: 56px;
  }

  .title {
    font-size: 16px;
  }

  .avatar {
    width: 32px;
    height: 32px;
  }

  .username {
    font-size: 14px;
    max-width: 80px;
    overflow: hidden;
    text-overflow: ellipsis;
  }
}

/* 超小屏幕优化 */
@media (max-width: 480px) {
  .main-header {
    padding: 8px 12px;
    min-height: 50px;
    gap: 8px;
  }

  .title {
    font-size: 15px;
  }

  .user-info {
    gap: 6px;
    padding: 2px 6px;
  }

  .avatar {
    width: 28px;
    height: 28px;
    border-width: 1.5px;
  }

  .username {
    font-size: 13px;
    max-width: 60px;
  }
}

/* 极小屏幕：只显示头像，隐藏用户名 */
@media (max-width: 360px) {
  .title {
    font-size: 14px;
  }

  .username {
    display: none;
  }

  .user-info {
    padding: 2px;
  }

  .avatar {
    width: 30px;
    height: 30px;
    margin: 0;
  }
}
</style>