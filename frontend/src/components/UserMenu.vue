<template>
  <div
    class="user-menu-wrapper"
    ref="wrapper"
    tabindex="0"
    @click="toggleMenu"
    @keydown.esc="closeMenu"
  >
    <img :src="computedAvatarSrc" class="avatar-img" alt="头像" />
    <span class="username">{{ displayName }}</span>
    <svg class="dropdown-arrow" width="20" height="20" viewBox="0 0 20 20">
      <path d="M5 8l5 5 5-5" stroke="#fff" stroke-width="2" fill="none" stroke-linecap="round"/>
    </svg>

    <transition name="fade">
      <div v-if="menuOpen" class="dropdown-menu" @click.stop>
        <div class="dropdown-item" @click.stop="goProfile">个人信息</div>
        <div class="dropdown-item logout" @click.stop="doLogout">退出登录</div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

// Pinia user store (确保路径与项目一致)
const user = useUserStore()
const router = useRouter()

const menuOpen = ref(false)
const wrapper = ref(null)

// 使用 public 下的默认头像（确保 frontend/public/default.png 存在）
const defaultAvatar = '/default.png'

const computedAvatarSrc = computed(() => {
  const a = user?.avatar || ''
  // 如果没有 avatar 或值为伪值，直接返回默认头像（不要给默认头像拼接时间戳）
  if (!a || a === 'null' || a === 'None' || a === 'undefined' || a === '/media/None') {
    return defaultAvatar
  }
  // 若后端返回的是相对路径（不以 http 开头或不以 / 开头），补全为以 / 开头
  let src = a
  if (!/^https?:\/\//.test(src) && !src.startsWith('/')) {
    src = '/' + src
  }
  // 防止缓存：只有真实 avatar 才拼接时间戳（avatarTimestamp 可由 store 在上传成功后更新）
  return src + '?t=' + (user?.avatarTimestamp || Date.now())
})

const displayName = computed(() => {
  // 如果 store 中有 username，显示之；否则显示未登录
  return (user?.username) ? user.username : '未登录'
})

function toggleMenu() {
  // 如果未登录，跳转到登录页（你也可以改为打开一个提示框）
  if (!user?.username) {
    router.push('/login')
    return
  }
  menuOpen.value = !menuOpen.value
}

function closeMenu() {
  menuOpen.value = false
}

function goProfile() {
  menuOpen.value = false
  router.push('/profile')
}

async function doLogout() {
  try {
    if (typeof user.logout === 'function') {
      await user.logout()
    } else {
      // 如果没有 store.logout，尽量清理并跳转
      // 例如你可能还需要清除 cookies：Cookies.remove('access')
    }
  } catch (e) {
    // ignore
  } finally {
    menuOpen.value = false
    router.replace('/login')
  }
}

// 点击外部区域关闭下拉
function onDocumentClick(e) {
  if (!wrapper.value) return
  if (!wrapper.value.contains(e.target)) {
    menuOpen.value = false
  }
}

onMounted(async () => {
  document.addEventListener('click', onDocumentClick)
  // 尝试加载用户信息（若你实现了 fetchUser）
  try {
    if (typeof user.fetchUser === 'function') {
      await user.fetchUser()
    }
  } catch (e) {
    // 忽略加载失败，仍然显示默认头像
  }
})

onBeforeUnmount(() => {
  document.removeEventListener('click', onDocumentClick)
})
</script>

<style scoped>
.user-menu-wrapper {
  display: flex;
  align-items: center;
  position: relative;
  cursor: pointer;
  outline: none;
  min-width: 0;
  user-select: none;
}
.avatar-img {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  object-fit: cover;
  background: #eee;
  border: 2px solid #fff;
}
.username {
  margin: 0 8px 0 10px;
  color: #fff;
  font-size: 1.08rem;
  font-weight: 500;
  max-width: 100px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.dropdown-arrow {
  transition: transform 0.2s;
  margin-left: 2px;
  pointer-events: none;
  fill: #fff;
}

/* 下拉菜单样式 */
.dropdown-menu {
  position: absolute;
  top: 110%;
  right: 0;
  min-width: 150px;
  background: #fff;
  color: #234;
  box-shadow: 0 8px 32px rgba(0,0,0,0.13);
  border-radius: 10px;
  padding: 8px 0;
  z-index: 999;
  font-size: 1rem;
  display: block;
}
.dropdown-item {
  padding: 12px 18px;
  color: #234;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.18s;
}
.dropdown-item:hover {
  background: #f2f6fc;
}
.logout {
  color: #d32f2f;
  font-weight: 600;
  border-top: 1px solid #eee;
}

/* 动画 */
.fade-enter-active, .fade-leave-active {
  transition: opacity .18s;
}
.fade-enter-from, .fade-leave-to {
  opacity: 0;
}
</style>