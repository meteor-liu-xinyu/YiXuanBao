<template>
  <div class="page">
    <h2 style="text-align:center;margin-top:14px">推荐医院</h2>
    <el-row :gutter="20" style="padding:20px">
      <el-col :span="8" v-for="(h, idx) in hospitals" :key="idx">
        <el-card>
          <h3>{{ h.name }}</h3>
          <p>{{ h.address }}</p>
          <p>科室/专长: {{ h.specialty }}</p>
          <p>联系方式: {{ h.contact }}</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
const route = useRoute()
const hospitals = ref([])

onMounted(() => {
  if (route.state && route.state.result) {
    hospitals.value = route.state.result
  } else {
    hospitals.value = []
  }
})
</script>