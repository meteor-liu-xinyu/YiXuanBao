import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src')
    }
  },
  server: {
    proxy: {
      // 将 /api/* 转发到后端（http://localhost:8000）
      // 前端仍然请求 /api/...，Vite 会把请求转发到后端，避免浏览器跨域问题
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
        // 如果后端路由没有 /api 前缀，取消注释下面的 rewrite，将路径 /api/... 重写为 /...
        // rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})