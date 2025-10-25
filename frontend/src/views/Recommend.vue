<template>
  <div class="page">
    <el-card style="max-width:900px;margin:20px auto">
      <!-- header: title + history button (visible only when logged in) -->
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px;">
        <h2 style="margin:0">填写信息，推荐医院</h2>
        <el-button v-if="isLoggedIn" type="primary" plain @click="goHistory">历史记录</el-button>
      </div>

      <el-form :model="form" label-width="160px" label-position="right">
        <el-form-item label="姓名（可选）">
          <el-input v-model="form.name" placeholder="请输入姓名" />
        </el-form-item>

        <!-- 必填：性别 -->
        <el-form-item>
          <template #label>
            <span>性别 <span style="color: #f56c6c">*</span></span>
          </template>
          <el-select v-model="form.gender" placeholder="请选择性别">
            <el-option label="男" value="male" />
            <el-option label="女" value="female" />
            <el-option label="其他" value="other" />
            <el-option label="未知/不愿透露" value="" />
          </el-select>
        </el-form-item>

        <!-- 必填：年龄 -->
        <el-form-item>
          <template #label>
            <span>年龄 <span style="color: #f56c6c">*</span></span>
          </template>
          <el-input-number v-model="form.age" :min="0" :max="150" @change="onAgeChange" />
        </el-form-item>

        <!-- 必填：疾病类别（ICD） -->
        <el-form-item>
          <template #label>
            <span>疾病类别（ICD） <span style="color: #f56c6c">*</span></span>
          </template>
          <div style="display:flex;align-items:center;gap:8px;width:100%;">
            <el-autocomplete
              v-model="diseaseQuery"
              :fetch-suggestions="queryICD"
              placeholder="输入疾病名称或 ICD 码检索"
              @select="onDiseaseSelect"
              @input="onDiseaseInput"
              @blur="onDiseaseBlur"
              :debounce="300"
              clearable
              :popper-class="'icd-autocomplete-popper'"
              style="flex:1;"
            >
              <template #default="{ item }">
                <div v-if="item.type === 'group'" class="icd-group-header">{{ item.label }}</div>
                <div v-else-if="item.type === 'subgroup'" class="icd-subgroup-header" :style="{ paddingLeft: '12px' }">
                  {{ item.label }}
                </div>
                <div v-else-if="item.type === 'item'" class="icd-item" :style="{ paddingLeft: '24px' }">
                  <div style="font-weight:500;">{{ item.value }}</div>
                </div>
                <div v-else-if="item.type === 'nomatch'" style="padding:8px 12px;color:#999;">
                  {{ item.value }}
                </div>
              </template>
            </el-autocomplete>

            <el-button type="primary" @click="openIcdTree = true">选择</el-button>
          </div>

          <div style="margin-top:8px;color:#666;font-size:0.9rem">
            本地匹配：输入框直接在前端匹配 ICD 数据（以顶层/次级分组展示）；也可点击右侧“选择”按钮按层级选择。
          </div>
        </el-form-item>

        <el-form-item label="既往病史">
          <el-input
            type="textarea"
            v-model="form.past_history"
            placeholder="填写既往病史（例如：高血压、糖尿病、手术史等）"
            :rows="3"
          />
        </el-form-item>

        <el-form-item label="经济承受能力（可选）">
          <el-select v-model="form.economic_level" placeholder="请选择经济承受能力">
            <el-option label="无要求" :value="'无要求'" />
            <el-option label="低（有限）" :value="0" />
            <el-option label="中（一般）" :value="1" />
            <el-option label="高（宽裕）" :value="2" />
          </el-select>
        </el-form-item>

        <el-form-item label="就医地/所在地区（可选）">
          <el-cascader
            v-model="form.region_cascader"
            :options="regionOptions"
            :props="regionProps"
            placeholder="请选择省 / 市 / 区"
            clearable
          />
        </el-form-item>

        <!-- 必填：就医紧迫性 -->
        <el-form-item>
          <template #label>
            <span>就医紧迫性 <span style="color: #f56c6c">*</span></span>
          </template>
          <el-select v-model="form.urgency" placeholder="请选择紧迫性" @change="onUrgencyChange">
            <el-option label="急诊" value="emergency" />
            <el-option label="较紧急" value="urgent" />
            <el-option label="常规/随访" value="routine" />
          </el-select>
        </el-form-item>

        <el-form-item label="病情补充/备注">
          <el-input
            type="textarea"
            v-model="form.disease_description"
            placeholder="可填写症状、既往处理、用药或其它说明（选填）"
            :rows="3"
          />
        </el-form-item>

        <el-form-item label="历史满意度（可选）">
          <el-rate v-model="historyRating" :max="5" />
        </el-form-item>

        <el-form-item label="健康风险评分">
          <div style="display:flex;align-items:center;gap:12px;">
            <el-input-number
              v-model="form.health_risk"
              :min="0"
              :max="100"
              :step="1"
              @focus="manualEditHealth = true"
              @change="onHealthRiskChange"
            />
            <el-button type="text" @click="recalcHealthRisk">重新计算</el-button>
            <el-button type="text" v-if="manualEditHealth" @click="undoManualHealth">撤销手动修改</el-button>
          </div>
        </el-form-item>

        <el-form-item>
          <el-button type="primary" :loading="loading" @click="submit">推荐医院</el-button>
          <el-button @click="reset" style="margin-left:12px">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <IcdTreeSelector v-model:modelValue="openIcdTree" :target-key="targetTreeKey" @select="onIcdTreeSelect" />
  </div>
</template>

<script setup>
import { reactive, ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'

import areasData from '@/assets/areas.json'
import { loadAndFlattenICD, searchICD } from '@/utils/icd-utils'
import IcdTreeSelector from '@/components/IcdTreeSelector.vue'
import api from '@/api/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const loading = ref(false)

// user / login state
const user = useUserStore()
const isLoggedIn = computed(() => !!(user.isAuthenticated || user.username))

function goHistory() {
  router.push('/history')
}

// history storage key
const HISTORY_KEY = 'recommend_history_v1'

// main form
const form = reactive({
  name: '',
  gender: '',
  age: null,
  disease_code: '',
  disease_vector: [],
  disease_description: '',
  past_history: '',
  economic_level: '无要求',
  region_cascader: [],
  urgency: '',
  health_risk: null,
  history_satisfaction: null
})

const historyRating = ref(0)
const diseaseQuery = ref('')
const manualEditHealth = ref(false)

// mark whether last action was selecting from suggestions
const selectedFromSuggest = ref(false)

// region cascader options and props
const regionOptions = ref([])
const regionProps = { value: 'value', label: 'label', children: 'children' }

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
const buildCascaderOptions = buildCascaderOptionsFromTree

// ICD local cache and state
let localICDList = null
let icdTimer = null
const openIcdTree = ref(false)
const targetTreeKey = ref(null)

/* ---------- helpers (kept same as existing implementation) ---------- */
function mapLabelsToValues(labels = [], options = []) {
  if (!labels || !labels.length) return []
  const values = []
  let curOpts = options
  for (const lbl of labels) {
    if (!curOpts || !curOpts.length) break
    const found = curOpts.find(o => String(o.label) === String(lbl) || String(o.value) === String(lbl))
    if (!found) break
    values.push(found.value)
    curOpts = found.children || []
  }
  return values
}

async function tryPrefillFromProfileOrRoute() {
  try {
    // sessionStorage fallback first
    try {
      const raw = sessionStorage.getItem('recommend_prefill')
      if (raw) {
        const obj = JSON.parse(raw)
        if (obj) {
          applyPrefill(obj)
          sessionStorage.removeItem('recommend_prefill')
          return
        }
      }
    } catch (e) {}

    // route.state prefill
    const prefillFromRoute = route?.state?.prefill
    if (prefillFromRoute) {
      applyPrefill(prefillFromRoute)
      try { sessionStorage.removeItem('recommend_prefill') } catch (e) {}
      return
    }

    // user profile
    const store = useUserStore()
    let data = null
    if (store.userData && Object.keys(store.userData).length) {
      data = store.userData
    } else {
      data = await store.fetchUser()
    }
    if (!data) return

    if (data.real_name) form.name = data.real_name
    else if (data.first_name || data.last_name) form.name = ((data.first_name || '') + ' ' + (data.last_name || '')).trim()
    if (data.gender) form.gender = data.gender

    if (data.birthday) {
      const b = new Date(data.birthday)
      if (!isNaN(b.getTime())) {
        const today = new Date()
        let age = today.getFullYear() - b.getFullYear()
        const m = today.getMonth() - b.getMonth()
        if (m < 0 || (m === 0 && today.getDate() < b.getDate())) age--
        if (age >= 0 && age <= 150) form.age = age
      }
    }

    if (Array.isArray(data.preferred_region_values) && data.preferred_region_values.length) {
      form.region_cascader = data.preferred_region_values.slice()
    } else if (data.preferred_region && typeof data.preferred_region === 'string') {
      const labels = data.preferred_region.split('/').map(s => s.trim()).filter(Boolean)
      if (labels.length) {
        const mapped = mapLabelsToValues(labels, regionOptions.value)
        if (mapped && mapped.length) form.region_cascader = mapped
      }
    }
  } catch (e) {
    console.debug('tryPrefillFromProfileOrRoute failed', e)
  }
}

function applyPrefill(obj = {}) {
  try {
    if (obj.name) form.name = obj.name
    if (obj.gender !== undefined) form.gender = obj.gender
    if (obj.age !== undefined) form.age = obj.age
    if (obj.disease_label) {
      diseaseQuery.value = obj.disease_label
      form.disease_code = obj.disease_code || ''
    } else if (obj.disease_code) {
      form.disease_code = obj.disease_code
      diseaseQuery.value = obj.disease_code
    }
    if (Array.isArray(obj.region)) form.region_cascader = obj.region.slice()
    if (obj.economic_level !== undefined) {
      if (obj.economic_level === '') form.economic_level = '无要求'
      else form.economic_level = obj.economic_level
    }
    if (obj.urgency) form.urgency = obj.urgency
    if (obj.health_risk !== undefined) form.health_risk = obj.health_risk
    if (obj.past_history) form.past_history = obj.past_history
    if (obj.disease_description) form.disease_description = obj.disease_description
    if (obj.history_satisfaction !== undefined) historyRating.value = obj.history_satisfaction
  } catch (e) { console.debug('applyPrefill failed', e) }
}

function queryICD(queryString, cb) {
  if (icdTimer) clearTimeout(icdTimer)
  if (!queryString) { cb([]); return }
  icdTimer = setTimeout(async () => {
    try {
      if (!localICDList) localICDList = await loadAndFlattenICD()
      const matched = searchICD(localICDList, queryString, { limit: 800 })
      if (!matched || !matched.length) {
        cb([{ type: 'nomatch', value: '未匹配到' }])
        return
      }
      const results = []
      const topSeen = new Set()
      const subSeenMap = new Map()
      for (const it of matched) {
        const path = Array.isArray(it.path) ? it.path : []
        const top = path[0] || { code: '__OTHER__', name: '其它' }
        const sub = path[1] || null
        const topLabel = top.code ? (top.code + (top.name ? ' ' + top.name : '')) : (top.name || '__OTHER__')
        if (!topSeen.has(topLabel)) {
          results.push({ type: 'group', label: topLabel })
          topSeen.add(topLabel)
          subSeenMap.set(topLabel, new Set())
        }
        const subLabel = sub ? (sub.code ? (sub.code + (sub.name ? ' ' + sub.name : '')) : sub.name) : '__no_sub__'
        const subSeen = subSeenMap.get(topLabel)
        if (sub && !subSeen.has(subLabel)) {
          results.push({ type: 'subgroup', label: subLabel, level: 1 })
          subSeen.add(subLabel)
        }
        results.push({
          type: 'item',
          value: `${it.code}${it.name ? ' ' + it.name : ''}`,
          code: it.code,
          label: it.name,
          level: 2
        })
      }
      cb(results)
    } catch (e) {
      console.warn('ICD 本地加载/搜索出错', e)
      cb([{ type: 'nomatch', value: '未匹配到' }])
    }
  }, 120)
}

function onDiseaseInput(val) { selectedFromSuggest.value = false }

async function onDiseaseSelect(item) {
  if (!item || item.type !== 'item' || !item.code) return
  selectedFromSuggest.value = true
  form.disease_code = item.code
  diseaseQuery.value = item.value || `${item.code} ${item.label || ''}`.trim()
  form.disease_vector = []
  if (!manualEditHealth.value) recalcHealthRisk()
}

function onDiseaseBlur() {
  setTimeout(() => {
    if (!selectedFromSuggest.value) {
      diseaseQuery.value = ''
      form.disease_code = ''
    }
    selectedFromSuggest.value = false
  }, 120)
}

async function onIcdTreeSelect(payload) {
  if (!payload || !payload.code) {
    ElMessage.warning('请选择一个 ICD 节点')
    return
  }
  form.disease_code = payload.code
  diseaseQuery.value = (payload.label || (payload.code + ' ' + payload.name)).trim()
  form.disease_vector = []
  if (!manualEditHealth.value) recalcHealthRisk()
}

function estimateRisk() {
  let score = 10
  if (form.age >= 0 && form.age <= 30) score += 0
  else if (form.age <= 50) score += 8
  else if (form.age <= 70) score += 18
  else score += 30

  if (form.urgency === 'emergency') score += 30
  else if (form.urgency === 'urgent') score += 15

  if (form.disease_code && /^C/.test(form.disease_code)) score += 20
  if (form.disease_code && /^I/.test(form.disease_code)) score += 10
  if (form.past_history && form.past_history.match(/心|冠|梗/)) score += 10

  score = Math.round(Math.max(0, Math.min(100, score)))
  return score
}
function recalcHealthRisk() { form.health_risk = estimateRisk() }
function onAgeChange() { if (!manualEditHealth.value) recalcHealthRisk() }
function onUrgencyChange() { if (!manualEditHealth.value) recalcHealthRisk() }
function onHealthRiskChange() { manualEditHealth.value = true }
function undoManualHealth() { manualEditHealth.value = false; recalcHealthRisk() }

function validate() {
  if (!form.gender && form.gender !== '') {
    ElMessage.error('请选择性别')
    return false
  }
  if (form.age === null || form.age === undefined || form.age === '') {
    ElMessage.error('请填写年龄')
    return false
  }
  const ageNum = Number(form.age)
  if (Number.isNaN(ageNum) || ageNum < 0 || ageNum > 150) {
    ElMessage.error('请输入有效的年龄（0-150）')
    return false
  }
  if (!form.disease_code) {
    ElMessage.error('请填写或选择疾病类别（ICD）')
    return false
  }
  if (!form.urgency) {
    ElMessage.error('请选择就医紧迫性')
    return false
  }
  return true
}

function reset() {
  form.name = ''
  form.disease_code = ''
  form.disease_vector = []
  diseaseQuery.value = ''
  form.disease_description = ''
  form.past_history = ''
  form.economic_level = '无要求'
  form.region_cascader = []
  form.urgency = ''
  form.health_risk = null
  form.history_satisfaction = null
  historyRating.value = 0
  manualEditHealth.value = false
}

/* -- 历史保存相关 -- */
function loadHistory() {
  try {
    const raw = localStorage.getItem(HISTORY_KEY)
    if (!raw) return []
    const arr = JSON.parse(raw)
    if (!Array.isArray(arr)) return []
    return arr
  } catch (e) {
    console.debug('loadHistory failed', e)
    return []
  }
}

async function saveHistoryEntry(entry) {
  try {
    // 如果登录则保存到后端，否则回落到 localStorage
    if (isLoggedIn.value) {
      await api.post('/accounts/history/', entry, { withCredentials: true })
    } else {
      const cur = loadHistory()
      cur.unshift(entry)
      const limited = cur.slice(0, 200)
      localStorage.setItem(HISTORY_KEY, JSON.stringify(limited))
    }
  } catch (e) {
    // 回退到本地存储（网络/后端失败）
    try {
      const cur = loadHistory()
      cur.unshift(entry)
      const limited = cur.slice(0, 200)
      localStorage.setItem(HISTORY_KEY, JSON.stringify(limited))
    } catch (err) {
      console.debug('saveHistoryEntry failed', err)
    }
  }
}

/* ---------- submit -> call backend recommend API and handle response ---------- */
async function submit() {
  if (!validate()) return
  loading.value = true
  form.history_satisfaction = historyRating.value

  const urgencyMap = { emergency: 2, urgent: 1, routine: 0 }

  // economic: backend expects integer or null (null means "not provided" / no requirement)
  const economicForPayload = (form.economic_level === '无要求' || form.economic_level === '') ? null : form.economic_level

  // region: many backends expect a string like "省/市/区". Convert cascader values -> labels -> join by '/'
  const regionLabels = Array.isArray(form.region_cascader) && form.region_cascader.length
    ? valuesToLabelsFallback(form.region_cascader, regionOptions.value)
    : []
  const regionForPayload = regionLabels.length ? regionLabels.join('/') : ''

  const payload = {
    name: form.name || '',
    gender: form.gender || '',
    age: form.age === null ? null : Number(form.age),
    disease_code: form.disease_code,
    disease_label: diseaseQuery.value || (form.disease_code || ''),
    disease_vector: form.disease_vector || [],
    disease_description: form.disease_description || '',
    past_history: form.past_history || '',
    // changed: send economic_level as null when no requirement (not empty string)
    economic_level: economicForPayload,
    // changed: send region as string (labels joined) to match backend validation requiring string
    region: regionForPayload,
    region_values: Array.isArray(form.region_cascader) ? form.region_cascader.slice() : [],
    health_risk: form.health_risk === null ? null : Number(form.health_risk),
    urgency: form.urgency,
    urgency_value: urgencyMap[form.urgency] ?? 0,
    history_satisfaction: form.history_satisfaction === null ? null : Number(form.history_satisfaction)
  }

  // 保存历史（local 或 后端）
  const entry = {
    id: Date.now(),
    created_at: new Date().toISOString(),
    summary: `${payload.disease_label || payload.disease_code || '未知疾病'} · ${payload.urgency || '未知紧迫性'}`,
    payload
  }
  await saveHistoryEntry(entry)

  try {
    const res = await api.post('/recommend/', payload, { withCredentials: true })
    const results = (res && res.data && res.data.results) ? res.data.results : []
    try {
      sessionStorage.setItem('recommend_payload', JSON.stringify(payload))
      sessionStorage.setItem('recommend_result', JSON.stringify(results))
    } catch (e) {}
    router.push({ path: '/result', state: { result: results, payload } })
    ElMessage.success('推荐已完成')
  } catch (e) {
    console.error('recommend API failed', e)
    ElMessage.error('推荐服务调用失败，使用本地模拟结果')
    const mock = [
      { id: 1, name: '市人民医院', address: '市中心路 1 号', specialty: '综合', contact: '010-1111111', recommendation_score: 60 },
      { id: 2, name: '省肿瘤医院', address: '省道 10 号', specialty: '肿瘤科', contact: '010-2222222', recommendation_score: 65 }
    ]
    try {
      sessionStorage.setItem('recommend_payload', JSON.stringify(payload))
      sessionStorage.setItem('recommend_result', JSON.stringify(mock))
    } catch (e) {}
    router.push({ path: '/result', state: { result: mock, payload } })
  } finally {
    loading.value = false
  }
}

onMounted(async () => {
  regionOptions.value = buildCascaderOptionsFromTree(areasData)
  try { await tryPrefillFromProfileOrRoute() } catch (e) {}
  if (!manualEditHealth.value) recalcHealthRisk()
})
</script>

<style scoped>
.page { padding: 12px 0 60px; }

.icd-autocomplete-popper .el-autocomplete-suggestion__wrap > li {
  display:block;
  padding:0;
}
.icd-group-header {
  padding:8px 12px;
  background:#fafafa;
  font-weight:600;
  color:#333;
  border-top:1px solid #eee;
}
.icd-subgroup-header {
  padding:6px 12px;
  color:#666;
  font-weight:500;
}
.icd-item {
  padding:6px 12px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  border-left:3px solid #e6edf7;
}
</style>