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
      '/api': {
        target: 'http://127.0.0.1:8000', // 与 Django runserver 实际地址保持一致
        changeOrigin: true,
        secure: false,
        // 将后端返回的 Set-Cookie 中的 Domain 字段去掉，确保浏览器把它设为 host-only（localhost:5173 -> cookie 也能被接受）
        // http-proxy 支持 cookieDomainRewrite，Vite 会把该选项传下去
        cookieDomainRewrite: ''  // 空字符串表示移除 domain 属性，使 cookie host-only
        // 如需把 domain 改为特定值，使用 { '*': 'localhost' } 的形式
      }
    }
  }
})