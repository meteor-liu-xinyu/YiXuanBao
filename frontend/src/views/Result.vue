<template>
  <div class="page">
    <h2 style="text-align:center;margin-top:14px">推荐医院</h2>

    <!-- Summary -->
    <el-card class="summary-card" shadow="hover">
      <div class="summary-grid">
        <div><strong>姓名：</strong>{{ payload.name || '未填写' }}</div>
        <div><strong>性别：</strong>{{ genderText(payload.gender) }}</div>
        <div><strong>年龄：</strong>{{ payload.age ?? '未填写' }}</div>
        <div><strong>疾病（ICD）：</strong>{{ payload.disease_label || payload.disease_code || '未填写' }}</div>
        <div><strong>就医紧迫性：</strong>{{ urgencyText(payload.urgency) }}</div>
        <div><strong>健康风险评分：</strong>{{ payload.health_risk ?? '未填写' }}</div>
        <div class="region-cell"><strong>地区：</strong>{{ regionLabel || '未填写' }}</div>
        <div><strong>经济承受：</strong>{{ economicText(payload.economic_level) }}</div>
      </div>
      <div style="margin-top:10px;display:flex;gap:8px;align-items:center;">
        <el-button type="primary" @click="goBack">修改条件</el-button>
        <el-button @click="recompute">重新推荐（本地）</el-button>
        <el-button type="text" @click="copyPayload">复制请求参数</el-button>
      </div>
    </el-card>

    <div v-if="loadingResults" style="text-align:center;padding:24px">
      <el-icon><Loading /></el-icon> 正在获取推荐结果...
    </div>

    <div v-else-if="!hospitals || hospitals.length === 0" class="no-result">
      <!-- 如果没有医院，显示空状态。不要显示示例数据 -->
      <el-empty description="未匹配到医院推荐">
        <template #footer>
          <el-button type="primary" @click="goBack">返回修改条件</el-button>
        </template>
      </el-empty>
    </div>

    <div v-else class="results-wrapper">
      <!-- 结果列表（保持原样） -->
      <div class="controls">
        <div>
          <el-select v-model="sortKey" placeholder="排序" size="small" @change="applySort">
            <el-option label="推荐度（降序）" value="score_desc" />
            <el-option label="健康风险（降序）" value="risk_desc" />
            <el-option label="距离（升序）" value="distance_asc" />
            <el-option label="按名称（A→Z）" value="name_asc" />
          </el-select>
        </div>
        <div>
          <el-input v-model="filterKeyword" size="small" placeholder="按医院名称/科室过滤" clearable @input="applyFilter" />
        </div>
      </div>

      <el-row :gutter="20" style="padding:20px">
        <el-col :span="8" v-for="(h, idx) in filteredAndSorted" :key="h.id || idx">
          <el-card shadow="always" :body-style="{ padding: '14px' }" class="hospital-card">
            <div class="card-header">
              <h3>{{ h.name }}</h3>
              <div class="tags">
                <el-tag type="danger" v-if="payload.urgency === 'emergency'">急</el-tag>
                <el-tag type="warning" v-else-if="payload.urgency === 'urgent'">紧</el-tag>
                <el-tag type="success" v-else>常</el-tag>
                <el-tag v-if="h.recommendation_score != null">得分 {{ Math.round(h.recommendation_score * 100) / 100 }}</el-tag>
              </div>
            </div>

            <p class="muted">{{ h.address }}</p>
            <p><strong>科室/专长：</strong> {{ h.specialty || '未填' }}</p>
            <p v-if="h.contact"><strong>联系方式：</strong> {{ h.contact }}</p>

            <div style="display:flex;gap:8px;margin-top:12px;align-items:center;">
              <el-button type="primary" size="small" @click="viewDetail(h)">查看详情</el-button>
              <el-button type="text" size="small" @click="openMap(h)">在地图中查看</el-button>
              <el-button type="text" size="small" @click="contactHospital(h)">联系医院</el-button>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import areasData from '@/assets/areas.json'
import api from '@/api/api'
import { Loading } from '@element-plus/icons-vue'  // 新增：Loading 图标

const route = useRoute()
const router = useRouter()

const loadingResults = ref(false)
// read hospitals and payload from route.state (Recommend.vue pushes { result, payload } optionally)
// if absent, fall back to sessionStorage or call backend
const hospitals = ref(Array.isArray(route.state?.result) ? route.state.result.slice() : [])
const payload = ref(route.state?.payload ? { ...route.state.payload } : (route.state?.resultPayload ? route.state.resultPayload : {}))

// try sessionStorage fallback
try {
  if ((!payload.value || Object.keys(payload.value).length === 0) && sessionStorage.getItem('recommend_payload')) {
    payload.value = JSON.parse(sessionStorage.getItem('recommend_payload'))
  }
  if ((!hospitals.value || hospitals.value.length === 0) && sessionStorage.getItem('recommend_result')) {
    const r = JSON.parse(sessionStorage.getItem('recommend_result'))
    if (Array.isArray(r) && r.length) hospitals.value = r
  }
} catch (e) { /* ignore */ }

// region helpers (same as before)
function buildCascaderOptionsFromTree(tree) {
  return (tree || []).map(prov => ({
    value: prov.code || prov.value || prov.name,
    label: prov.name || prov.label,
    children: (prov.children || []).map(city => ({
      value: city.code || city.value || city.name,
      label: city.name || city.label,
      children: (city.children || []).map(area => ({
        value: area.code || area.value || area.name,
        label: area.name || area.label,
        leaf: true
      }))
    }))
  }))
}
const regionOptions = buildCascaderOptionsFromTree(areasData)

function valuesToLabelsFallback(values = [], options = []) {
  const labels = []
  const findByValue = (opts, value) => {
    if (!opts) return null
    for (const o of opts) {
      if (String(o.value) === String(value)) return o
      if (o.children) {
        const r = findByValue(o.children, value)
        if (r) return r
      }
    }
    return null
  }
  for (const v of (values || [])) {
    const node = findByValue(options, v)
    if (node) labels.push(node.label)
    else labels.push(String(v))
  }
  return labels
}

const regionLabel = computed(() => {
  const vals = payload.value.region || payload.value.region_cascader || []
  if (!Array.isArray(vals) || !vals.length) return ''
  const labels = valuesToLabelsFallback(vals, regionOptions)
  return labels.join('/')
})

function genderText(g) {
  if (!g && g !== '') return '未填写'
  if (g === 'male') return '男'
  if (g === 'female') return '女'
  if (g === 'other') return '其他'
  return g
}

function urgencyText(u) {
  if (!u) return '未填写'
  if (u === 'emergency') return '急诊'
  if (u === 'urgent') return '较紧急'
  if (u === 'routine') return '常规/随访'
  return u
}

function economicText(v) {
  if (v === '') return '无要求'
  if (v === null || v === undefined) return '未填写'
  if (v === 0) return '低（有限）'
  if (v === 1) return '中（一般）'
  if (v === 2) return '高（宽裕）'
  return String(v)
}

// filtering / sorting
const filterKeyword = ref('')
const sortKey = ref('score_desc')

const filteredAndSorted = computed(() => {
  // same sorting/filtering logic as before
  let list = (hospitals.value || []).slice()
  if (filterKeyword.value) {
    const kw = filterKeyword.value.toLowerCase()
    list = list.filter(h => {
      return (h.name || '').toLowerCase().includes(kw) ||
             (h.specialty || '').toLowerCase().includes(kw)
    })
  }
  list.sort((a, b) => {
    if (sortKey.value === 'score_desc') {
      const sa = Number(a.recommendation_score ?? a.match_score ?? -Infinity)
      const sb = Number(b.recommendation_score ?? b.match_score ?? -Infinity)
      return sb - sa
    }
    if (sortKey.value === 'risk_desc') {
      const ra = Number(payload.value.health_risk ?? 0)
      const rb = Number(payload.value.health_risk ?? 0)
      return rb - ra
    }
    if (sortKey.value === 'distance_asc') {
      const da = Number(a.distance ?? Infinity)
      const db = Number(b.distance ?? Infinity)
      return da - db
    }
    if (sortKey.value === 'name_asc') {
      return String(a.name || '').localeCompare(String(b.name || ''))
    }
    return 0
  })
  return list
})


function applySort() {}
function applyFilter() {}

function goBack() {
  try {
    sessionStorage.setItem('recommend_prefill', JSON.stringify(payload.value || {}))
  } catch (e) {}
  const prefill = payload.value ? JSON.parse(JSON.stringify(payload.value)) : {}
  router.push({ path: '/recommend', state: { prefill } })
}

function viewDetail(h) {
  if (h && h.id) router.push({ path: `/hospital/${h.id}` })
  else ElMessage.info('打开医院详情（示例）')
}

function openMap(h) {
  if (h && h.latitude && h.longitude) {
    window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(h.latitude + ',' + h.longitude)}`, '_blank')
  } else ElMessage.info('无定位信息')
}

function contactHospital(h) {
  if (h && h.contact) {
    if (h.contact.startsWith('tel:') || /^[+\d]/.test(h.contact)) window.location.href = `tel:${h.contact.replace(/^tel:/, '')}`
    else navigator.clipboard?.writeText(h.contact).then(() => ElMessage.success('联系方式已复制')).catch(() => ElMessage.info(h.contact))
  } else ElMessage.info('无联系方式')
}

function copyPayload() {
  try {
    const text = JSON.stringify(payload.value || {}, null, 2)
    navigator.clipboard?.writeText(text)
    ElMessage.success('已复制请求参数到剪贴板')
  } catch (e) { ElMessage.warning('复制失败') }
}

async function fetchRecommendationsFromBackend(p) {
  if (!p || Object.keys(p || {}).length === 0) return
  loadingResults.value = true

  function normalizePayloadForBackend(raw) {
    const payload = { ...raw }

    try {
      const vals = Array.isArray(payload.region) && payload.region.length ? payload.region
        : (Array.isArray(payload.region_cascader) && payload.region_cascader.length ? payload.region_cascader : [])
      if (Array.isArray(vals) && vals.length) {
        const opts = (regionOptions && (regionOptions.value || regionOptions)) || []
        const labels = typeof valuesToLabelsFallback === 'function'
          ? valuesToLabelsFallback(vals, opts)
          : vals.map(v => String(v))
        payload.region = labels.join('/')
      } else {
        payload.region = ''
      }
    } catch (e) {
      payload.region = ''
    }

    if (payload.economic_level === '' || payload.economic_level === '无要求' || payload.economic_level === undefined || payload.economic_level === null) {
      delete payload.economic_level
    } else {
      const n = Number(payload.economic_level)
      if (Number.isNaN(n)) delete payload.economic_level
      else payload.economic_level = n
    }

    if (payload.age !== null && payload.age !== undefined && payload.age !== '') payload.age = Number(payload.age)
    if (payload.health_risk !== null && payload.health_risk !== undefined && payload.health_risk !== '') payload.health_risk = Number(payload.health_risk)
    return payload
  }

  try {
    const normalized = normalizePayloadForBackend(p)
    const res = await api.post('/recommend/', normalized, { withCredentials: true })
    const results = (res && res.data && res.data.results) ? res.data.results : []

    hospitals.value = results || []

    try {
      sessionStorage.setItem('recommend_payload', JSON.stringify(p))
      sessionStorage.setItem('recommend_result', JSON.stringify(results))
    } catch (e) {}

    return results
  } catch (e) {
    console.error('fetchRecommendationsFromBackend failed', e)
    const detail = e?.response?.data?.detail
    const errors = e?.response?.data?.errors
    if (detail) {
      ElMessage.error(String(detail))
    } else if (errors && typeof errors === 'object') {
      try {
        const parts = []
        for (const k of Object.keys(errors)) {
          parts.push(`${k}: ${Array.isArray(errors[k]) ? errors[k].join('; ') : String(errors[k])}`)
        }
        ElMessage.error(parts.join('；'))
      } catch (_) {
        ElMessage.error('推荐服务返回参数错误')
      }
    } else {
      ElMessage.error('从推荐服务读取结果失败，请稍后重试')
    }

    hospitals.value = []
    return []
  } finally {
    loadingResults.value = false
  }
}

// recompute 调用
function recompute() {
  if (!payload.value || Object.keys(payload.value).length === 0) {
    ElMessage.info('当前没有请求参数，无法重新推荐')
    return
  }
  fetchRecommendationsFromBackend(payload.value)
}

onMounted(() => {
  if ((!hospitals.value || hospitals.value.length === 0) && payload.value && Object.keys(payload.value).length) {
    fetchRecommendationsFromBackend(payload.value)
  }
})
</script>

<style scoped>
.page { padding: 12px 0 60px; }
.summary-card { max-width:900px; margin: 14px auto; }
.summary-grid { display:grid; grid-template-columns: repeat(3, 1fr); gap:10px; align-items:center; }
.region-cell { grid-column: span 3; }
.controls { max-width:900px; margin: 12px auto; display:flex; justify-content:space-between; align-items:center; gap:12px; padding: 0 6px; }
.muted { color:#666; margin-top:6px; }
.hospital-card { min-height:160px; }
.card-header { display:flex; justify-content:space-between; align-items:flex-start; gap:8px; }
.tags { display:flex; gap:6px; align-items:center; }
.no-result { max-width:600px; margin:30px auto; text-align:center; }
</style>