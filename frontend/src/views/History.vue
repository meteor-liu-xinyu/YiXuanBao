<template>
  <div class="history-page" style="max-width:980px;margin:20px auto">
    <el-card>
      <div class="header-row">
        <div style="display:flex;align-items:center;gap:12px;">
          <el-button type="primary" plain @click="goBack">返回</el-button>
          <h2 style="margin:0;">历史记录</h2>
        </div>

        <div>
          <el-button type="danger" plain @click="clearAll" :disabled="!entries.length">清空全部</el-button>
        </div>
      </div>

      <div v-if="!entries.length" class="empty" style="padding:40px;text-align:center;color:#777;">
        暂无历史记录。
      </div>

      <div v-else class="entries-list" style="display:flex;flex-direction:column;gap:12px;">
        <el-card
          v-for="it in entries"
          :key="it.id"
          class="history-entry-card"
          shadow="hover"
        >
          <div class="entry-top" style="display:flex;justify-content:space-between;align-items:center;">
            <div>
              <div style="display:flex;gap:12px;align-items:center;">
                <strong style="font-size:1.05rem">{{ it.summary || '推荐记录' }}</strong>
                <span class="created-at" style="color:#999;font-size:0.92rem;">{{ formatDate(it.created_at) }}</span>
              </div>
              <div style="margin-top:6px;color:#666;font-size:0.95rem;">
                <span v-if="it.payload?.name">姓名：{{ it.payload.name }}</span>
                <span v-if="it.payload?.gender" style="margin-left:12px">性别：{{ genderText(it.payload.gender) }}</span>
                <span v-if="it.payload?.age !== null && it.payload?.age !== undefined" style="margin-left:12px">年龄：{{ it.payload.age }}</span>
              </div>
            </div>

            <div style="display:flex;gap:8px;align-items:center;">
              <el-button size="small" type="primary" @click="openEntry(it)">打开</el-button>
              <el-button size="small" type="danger" plain @click="removeOne(it)">删除</el-button>
            </div>
          </div>

          <div class="entry-body" style="display:flex;gap:20px;margin-top:12px;flex-wrap:wrap;">
            <div v-if="it.payload?.disease_label || it.payload?.disease_code" class="field-pill">
              <strong>疾病（ICD）</strong>
              <div class="val">
                <span v-if="it.payload?.disease_label">{{ it.payload.disease_label }}</span>
                <span v-else>{{ it.payload.disease_code }}</span>
              </div>
            </div>

            <div v-if="it.payload?.urgency" class="field-pill"><strong>紧迫性</strong><div class="val">{{ urgencyText(it.payload.urgency) }}</div></div>
            <div v-if="it.payload?.health_risk !== null && it.payload?.health_risk !== undefined" class="field-pill"><strong>风险评分</strong><div class="val">{{ it.payload.health_risk }}</div></div>
            <div v-if="it.payload && it.payload.economic_level !== null && it.payload.economic_level !== undefined && it.payload.economic_level !== '' && it.payload.economic_level !== '无要求'" class="field-pill"><strong>经济承受</strong><div class="val">{{ economicText(it.payload.economic_level) }}</div></div>
            <div v-if="regionLabelFor(it.payload)" class="field-pill" style="min-width:220px"><strong>地区</strong><div class="val">{{ regionLabelFor(it.payload) }}</div></div>
            <div v-if="it.payload?.past_history" class="field-pill large"><strong>既往病史</strong><div class="val">{{ it.payload.past_history }}</div></div>
            <div v-if="it.payload?.disease_description" class="field-pill large"><strong>病情补充</strong><div class="val">{{ it.payload.disease_description }}</div></div>
          </div>
        </el-card>
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import areasData from '@/assets/areas.json'
import api from '@/api/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const HISTORY_KEY = 'recommend_history_v1'
const entries = ref([])

const userStore = useUserStore()

/* --- region helpers (same approach as Result.vue / Recommend.vue) --- */
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

function regionLabelFor(payload = {}) {
  const vals = payload.region || payload.region_cascader || []
  if (!Array.isArray(vals) || !vals.length) return ''
  const labels = valuesToLabelsFallback(vals, regionOptions)
  return labels.join('/')
}

/* --- util display helpers --- */
function genderText(g) {
  if (!g && g !== '') return ''
  if (g === 'male') return '男'
  if (g === 'female') return '女'
  if (g === 'other') return '其他'
  return g
}
function urgencyText(u) {
  if (!u) return ''
  if (u === 'emergency') return '急诊'
  if (u === 'urgent') return '较紧急'
  if (u === 'routine') return '常规/随访'
  return u
}
function economicText(v) {
  // 约定：空字符串 '' 表示“无要求”；null/undefined 表示未填写
  if (v === '') return '无要求'
  if (v === null || v === undefined) return ''
  if (v === 0) return '低（有限）'
  if (v === 1) return '中（一般）'
  if (v === 2) return '高（宽裕）'
  return String(v)
}

function formatDate(s) {
  if (!s) return ''
  try {
    const d = new Date(s)
    if (isNaN(d.getTime())) return s
    return d.toLocaleString()
  } catch (e) { return s }
}

/* --- storage operations --- */
function loadHistoryLocal() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    if (!Array.isArray(arr)) return []
    return arr
  } catch (e) {
    console.debug('loadHistoryLocal failed', e)
    return []
  }
}

async function fetchHistoryFromServer() {
  try {
    const res = await api.get('/accounts/history/', { withCredentials: true })
    // expected res.data 为数组或 paginated results
    entries.value = Array.isArray(res.data) ? res.data : (res.data.results || [])
  } catch (e) {
    console.error('fetchHistoryFromServer failed', e)
    ElMessage.error('加载历史失败，显示本地历史（如有）')
    entries.value = loadHistoryLocal()
  }
}

/* --- actions --- */
function removeOne(item) {
  ElMessageBox.confirm('确认删除该历史项？', '删除', { confirmButtonText: '删除', cancelButtonText: '取消', type: 'warning' })
    .then(async () => {
      if (userStore && (userStore.isAuthenticated || userStore.username)) {
        try {
          await api.delete(`/accounts/history/${item.id}/`, { withCredentials: true })
          await fetchHistoryFromServer()
          ElMessage.success('已删除')
        } catch (e) {
          console.error('delete history failed', e)
          ElMessage.error('删除失败')
        }
      } else {
        const remaining = entries.value.filter(x => x.id !== item.id)
        entries.value = remaining
        try { localStorage.setItem(HISTORY_KEY, JSON.stringify(remaining)) } catch (e) {}
        ElMessage.success('已删除（本地）')
      }
    }).catch(() => {})
}

function clearAll() {
  ElMessageBox.confirm('确认清空全部历史？此操作不可恢复。', '清空历史', { confirmButtonText: '清空', cancelButtonText: '取消', type: 'warning' })
    .then(async () => {
      if (userStore && (userStore.isAuthenticated || userStore.username)) {
        try {
          await api.delete('/accounts/history/clear/', { withCredentials: true })
          entries.value = []
          ElMessage.success('已清空')
        } catch (e) {
          console.error('clear history failed', e)
          ElMessage.error('清空失败')
        }
      } else {
        entries.value = []
        try { localStorage.removeItem(HISTORY_KEY) } catch (e) {}
        ElMessage.success('已清空（本地）')
      }
    }).catch(() => {})
}

/**
 * 打开一条历史记录并进入结果页
 * 将 payload 写入 sessionStorage（保证传递可靠），并导航到 /result
 */
function openEntry(item) {
  try {
    const p = item && item.payload ? item.payload : {}
    try { sessionStorage.setItem('recommend_payload', JSON.stringify(p)) } catch (e) {}
    try {
      const r = item && item.result ? item.result : []
      sessionStorage.setItem('recommend_result', JSON.stringify(r))
    } catch (e) {}
    router.push('/result')
  } catch (e) {}
}

function goBack() {
  try {
    if (window.history && window.history.length > 1) {
      router.back()
    } else {
      router.push('/welcome')
    }
  } catch (e) {
    router.push('/welcome')
  }
}

onMounted(() => {
  if (userStore && (userStore.isAuthenticated || userStore.username)) {
    fetchHistoryFromServer()
  } else {
    entries.value = loadHistoryLocal()
  }
})
</script>

<style scoped>
.history-page { padding: 12px 0 60px; }
.empty { padding: 40px 20px; }

.header-row { display:flex;justify-content:space-between;align-items:center;margin-bottom:12px; }

.history-entry-card { cursor: default; }
.entry-top { cursor: pointer; }
.field-pill {
  background:#fbfdff;
  border:1px solid #eef3fb;
  padding:8px 10px;
  border-radius:8px;
  min-width:120px;
  display:flex;
  flex-direction:column;
  gap:6px;
}
.field-pill.large { min-width:260px; flex:1 1 100%; }
.field-pill .val { color:#234; margin-top:4px; font-weight:500; }
.created-at { margin-left:6px; }
</style>