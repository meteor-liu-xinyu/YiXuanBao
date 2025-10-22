<template>
  <div class="page">
    <el-card style="max-width:420px;margin:40px auto">
      <h3>注册</h3>
      <el-form :model="form" label-width="80px">
        <el-form-item label="用户名">
          <el-input v-model="form.username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="doRegister">注册</el-button>
          <el-button @click="$router.push('/login')">去登录</el-button>
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

async function doRegister() {
  try {
    const res = await user.register({ username: form.username, password: form.password })
    if (res.status === 201 || res.status === 200) {
      ElMessage.success('注册成功，请登录')
      $router.push('/login')
    } else {
      ElMessage.error('注册失败')
    }
  } catch (e) {
    console.error(e)
    ElMessage.error('注册请求失败')
  }
}
</script>