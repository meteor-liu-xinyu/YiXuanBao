<template>
  <div id="app">
    <AppHeader />
    <router-view />
  </div>
</template>

<script setup>
import AppHeader from '@/components/AppHeader.vue'
</script>

<style>
/* 全局小样式 */
#app {
  min-height: 100vh;
  background: linear-gradient(90deg,#f2f6fc 0%,#e0eafc 100%);
}
</style>