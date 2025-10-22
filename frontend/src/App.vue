<template>
  <div id="app">
    <header class="app-header">
      <div class="header-inner container">
        <div class="brand" @click="$router.push('/')">
          <svg class="logo" viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
            <rect width="120" height="120" rx="18" fill="#C4E7F5"/>
            <text x="60" y="74" font-size="42" fill="#000" text-anchor="middle" font-family="Inter, Arial, sans-serif">医</text>
          </svg>
          <span class="site-title">医选宝智能助手</span>
        </div>

        <div class="header-actions">
          <!-- 只有登录并且当前路由没有设置 hideUserMenu 时才显示 UserMenu 下拉 -->
          <UserMenu v-if="isLoggedIn && !route.meta.hideUserMenu" />
        </div>
      </div>
    </header>

    <main class="app-main">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import UserMenu from '@/components/UserMenu.vue'
import { useUserStore } from '@/stores/user' // 若路径不同请修改

const route = useRoute()
const user = useUserStore()

// 判断是否登录（依赖 store 中的 username 字段）
// 若你的 store 有 isAuthenticated，请使用对应字段
const isLoggedIn = computed(() => !!(user.username))
</script>

<style>
#app { min-height: 100vh; display:flex; flex-direction:column; }
.app-header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 64px;
  z-index: 1000;
  background: linear-gradient(90deg, #6a85e6 0%, #43cea2 100%);
  color: #fff;
  box-shadow: 0 2px 8px rgba(70,110,210,0.13);
}
.header-inner {
  height: 100%;
  display:flex;
  align-items:center;
  justify-content:space-between;
  padding: 0 16px;
}
.brand { display:flex; align-items:center; gap:12px; cursor:pointer; user-select:none; }
.logo { width:40px; height:40px; border-radius:8px; display:block; }
.site-title { font-size:1.1rem; font-weight:600; color:#fff; }
.header-actions { display:flex; align-items:center; gap:12px; }

.app-main {
  margin-top: 64px; /* 留出 header 高度 */
  flex: 1 1 auto;
  min-height: calc(100vh - 64px);
  padding: 24px;
  box-sizing: border-box;
}
.container { max-width: 1200px; margin: 0 auto; width:100%; }
</style>