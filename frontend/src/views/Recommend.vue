<template>
  <div class="page">
    <el-card style="max-width:900px;margin:20px auto">
      <h2>填写信息，推荐医院</h2>
      <el-form :model="form" label-width="110px">
        <el-form-item label="姓名"><el-input v-model="form.name"/></el-form-item>
        <el-form-item label="性别">
          <el-select v-model="form.gender" placeholder="选择">
            <el-option label="男" value="male" />
            <el-option label="女" value="female" />
            <el-option label="其他" value="other" />
          </el-select>
        </el-form-item>
        <el-form-item label="年龄"><el-input-number v-model="form.age" :min="0"/></el-form-item>
        <el-form-item label="病种/症状"><el-input v-model="form.disease"/></el-form-item>
        <el-form-item label="地区"><el-input v-model="form.region"/></el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submit">推荐医院</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { reactive } from 'vue'
import api from '@/api/api'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

const router = useRouter()
const form = reactive({ name:'', gender:'', age:null, disease:'', region:'' })

async function submit(){
  try {
    const res = await api.post('hospital/recommend/', form)
    router.push({ path: '/result', state: { result: res.data.hospitals } })
  } catch (e) {
    console.error(e)
    ElMessage.error('请求失败')
  }
}
</script>