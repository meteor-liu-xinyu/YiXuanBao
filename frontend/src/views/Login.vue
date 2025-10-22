<template>
  <div class="page">
    <el-card style="max-width:420px;margin:40px auto">
      <h3>登录</h3>
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doLogin">登录</el-button>
          <el-button @click="$router.push('/register')">去注册</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const user = useUserStore()
const form = reactive({ username:'', password:'' })

async function doLogin() {
  try {
    const ok = await user.login({ username: form.username, password: form.password })
    if (ok) {
      ElMessage.success('登录成功')
      // redirect to recommend
      window.location.href = '/recommend'
    } else {
      ElMessage.error('登录失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('登录请求失败')
  }
}
</script>