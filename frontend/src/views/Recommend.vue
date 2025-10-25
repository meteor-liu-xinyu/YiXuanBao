<template>
  <div class="page">
    <el-card style="max-width:900px;margin:20px auto">
      <h2>填写信息，推荐医院</h2>

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
import { reactive, ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'

import areasData from '@/assets/areas.json'
import { loadAndFlattenICD, searchICD } from '@/utils/icd-utils'
import IcdTreeSelector from '@/components/IcdTreeSelector.vue'
import api from '@/api/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const loading = ref(false)

// main form
const form = reactive({
  name: '',
  gender: '',
  age: null,
  disease_code: '',
  disease_vector: [],
  disease_description: '',
  past_history: '',
  economic_level: null,
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

// helpers for mapping preferred_region -> cascader values
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

/**
 * 从用户信息中尝试预填表单字段：姓名、性别、年龄、地区
 */
async function tryPrefillFromProfile() {
  try {
    const store = useUserStore()
    let data = null
    // 优先使用 store.userData（如果已加载）
    if (store.userData && Object.keys(store.userData).length) {
      data = store.userData
    } else {
      // 如果未加载，尝试 fetchUser（会返回 data 或 null）
      data = await store.fetchUser()
    }
    if (!data) return

    // 名字：优先 real_name 或 first+last
    if (data.real_name) {
      form.name = data.real_name
    } else if (data.first_name || data.last_name) {
      form.name = ((data.first_name || '') + ' ' + (data.last_name || '')).trim()
    }

    if (data.gender) form.gender = data.gender

    // birthday -> age
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

    // region: 优先 preferred_region_values (已为 value 列表)
    if (Array.isArray(data.preferred_region_values) && data.preferred_region_values.length) {
      form.region_cascader = data.preferred_region_values.slice()
    } else if (data.preferred_region && typeof data.preferred_region === 'string') {
      const labels = data.preferred_region.split('/').map(s => s.trim()).filter(Boolean)
      if (labels.length) {
        const mapped = mapLabelsToValues(labels, regionOptions.value)
        if (mapped && mapped.length) {
          form.region_cascader = mapped
        }
      }
    }
  } catch (e) {
    console.debug('tryPrefillFromProfile failed', e)
  }
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

function onDiseaseInput(val) {
  selectedFromSuggest.value = false
}

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
  // 必填项：gender, age, disease_code, urgency
  if (!form.gender && form.gender !== '') {
    ElMessage.error('请选择性别')
    return false
  }
  if (form.age === null || form.age === undefined || form.age === '') {
    ElMessage.error('请填写年龄')
    return false
  }
  // age 必须为数字且在合理范围
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

  // 其余字段均为可选（经济承受能力、地区等）
  return true
}

function reset() {
  form.name = ''
  form.disease_code = ''
  form.disease_vector = []
  diseaseQuery.value = ''
  form.disease_description = ''
  form.past_history = ''
  form.economic_level = null
  form.region_cascader = []
  form.urgency = ''
  form.health_risk = null
  form.history_satisfaction = null
  historyRating.value = 0
  manualEditHealth.value = false
}

async function submit() {
  if (!validate()) return
  loading.value = true
  form.history_satisfaction = historyRating.value

  const urgencyMap = { emergency: 2, urgent: 1, routine: 0 }
  const payload = {
    name: form.name || '',
    gender: form.gender || '',
    age: form.age === null ? null : Number(form.age),
    disease_code: form.disease_code,
    disease_vector: form.disease_vector || [],
    disease_description: form.disease_description || '',
    past_history: form.past_history || '',
    economic_level: form.economic_level,
    region: form.region_cascader,
    health_risk: form.health_risk === null ? null : Number(form.health_risk),
    urgency: form.urgency,
    urgency_value: urgencyMap[form.urgency] ?? 0,
    history_satisfaction: form.history_satisfaction === null ? null : Number(form.history_satisfaction)
  }

  console.log('本地提交 payload:', payload)
  ElMessage.success('已在前端模拟提交（未调用后端）。查看控制台 payload。')
  try { router.push({ path: '/result', state: { result: [] } }) } catch (e) {}
  finally { loading.value = false }
}

onMounted(async () => {
  regionOptions.value = buildCascaderOptionsFromTree(areasData)
  try { await tryPrefillFromProfile() } catch (e) {}
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