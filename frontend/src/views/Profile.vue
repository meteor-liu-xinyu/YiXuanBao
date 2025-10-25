<template>
  <div class="profile-fullscreen">
    <div class="profile-form">
      <h1 class="profile-title">个人信息</h1>

      <!-- 头像行 -->
      <div class="profile-field avatar-row">
        <label>头像：</label>
        <div class="profile-value">
          <img
            :src="validAvatar"
            class="avatar-img"
            alt="头像"
            @error="onAvatarError"
          />
          <div style="display:flex;flex-direction:column;gap:8px;">
            <div style="display:flex;gap:8px;">
              <button class="avatar-edit-btn" @click="triggerAvatarUpload" :disabled="uploadingAvatar">
                {{ uploadingAvatar ? '上传中...' : '修改头像' }}
              </button>
              <button class="avatar-edit-btn plain" @click="onRemoveAvatar" :disabled="uploadingAvatar">
                删除头像
              </button>
            </div>
            <div class="small text-muted">建议头像为正方形，大小不超过 2MB</div>
          </div>

          <input
            ref="avatarInput"
            type="file"
            accept="image/*"
            class="avatar-upload"
            @change="onAvatarChange"
            style="display: none"
          />
        </div>
      </div>

      <!-- 裁剪弹窗 -->
      <div v-if="cropVisible" class="cropper-modal">
        <div class="cropper-body">
          <img ref="cropperImg" :src="cropImageUrl" class="cropper-img" />
        </div>
        <div style="text-align:center;margin-top:12px;">
          <button @click="confirmCrop" class="crop-btn" :disabled="uploadingAvatar">确定</button>
          <button @click="closeCrop" class="crop-btn cancel" :disabled="uploadingAvatar">取消</button>
        </div>
      </div>

      <!-- 帐户信息（只读） -->
      <div class="profile-field">
        <label>用户名：</label>
        <div class="profile-value">
          {{ username || '未填写' }}
          <span v-if="isAdmin" class="admin-tag">管理员 / Admin</span>
        </div>
      </div>

      <!-- 昵称（可编辑，blur 自动写入本地草稿并展示） -->
      <div class="profile-field">
        <label>昵称：</label>
        <div class="profile-value">
          <template v-if="editing === 'nickname'">
            <input v-model="editNickname" class="edit-input" @blur="onBlurAndSave('nickname')" />
          </template>
          <template v-else>
            <span>{{ displayNickname || '未填写' }}</span>
            <span class="icon-btn" @click="editField('nickname')">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
        </div>
      </div>

      <!-- 真实姓名 -->
      <div class="profile-field">
        <label>真实姓名：</label>
        <div class="profile-value">
          <template v-if="editing === 'real_name'">
            <input v-model="editRealName" class="edit-input" @blur="onBlurAndSave('real_name')" />
          </template>
          <template v-else>
            <span>{{ displayRealName || '未填写' }}</span>
            <span class="icon-btn" @click="editField('real_name')">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
        </div>
      </div>

      <!-- 邮箱（可编辑） -->
      <div class="profile-field">
        <label>邮箱：</label>
        <div class="profile-value" style="flex-direction:column;align-items:flex-start;">
          <template v-if="editing === 'email'">
            <div style="width:100%;">
              <!-- 加上 emailError 的 class 绑定，这样会显示红框 -->
              <input
                v-model="editEmail"
                :class="['edit-input', { invalid: emailError }]"
                @input="onEmailInput"
                @blur="onBlurEmail"
                style="width:100%"
                placeholder="例如：user@example.com"
              />
              <div class="field-error" v-if="emailError">
                <small>邮箱格式不正确</small>
              </div>
            </div>
          </template>
          <template v-else>
            <!-- 在非编辑状态也显示错误提示（当存在错误时） -->
            <div style="display:flex;flex-direction:column;width:100%;">
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <span>{{ displayEmail || '未填写' }}</span>
                <span class="icon-btn" @click="editField('email')">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </span>
              </div>
              <div class="field-error" v-if="emailError && editing !== 'email'">
                <small>邮箱格式不正确</small>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 电话：失焦时校验（中国手机号） -->
      <div class="profile-field">
        <label>手机号：</label>
        <div class="profile-value" style="flex-direction:column;align-items:flex-start;">
          <template v-if="editing === 'phone'">
            <div style="display:flex;align-items:center;gap:8px;width:100%;">
              <input
                v-model="editPhone"
                :class="['edit-input', { invalid: phoneError }]"
                @input="onPhoneInput"
                @blur="onBlurPhone"
                placeholder="例如：13912345678"
                style="flex:1;"
              />
            </div>
            <div class="field-error" v-if="phoneError">
              <small>请输入有效的中国手机号（11 位，如 13912345678）</small>
            </div>
          </template>
          <template v-else>
            <!-- 非编辑状态也显示错误提示 -->
            <div style="display:flex;flex-direction:column;width:100%;">
              <div style="display:flex;align-items:center;justify-content:space-between;">
                <span>{{ displayPhone || '未填写' }}</span>
                <span class="icon-btn" @click="editField('phone')">
                  <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                    <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
                  </svg>
                </span>
              </div>
              <div class="field-error" v-if="phoneError && editing !== 'phone'">
                <small>请输入有效的中国手机号（11 位，如 13912345678）</small>
              </div>
            </div>
          </template>
        </div>
      </div>

      <!-- 性别（选择后自动写入本地草稿并展示） -->
      <div class="profile-field">
        <label>性别：</label>
        <div class="profile-value">
          <template v-if="editing === 'gender'">
            <select v-model="editGender" class="edit-input" style="width:140px" @change="onChangeAndSave('gender')">
              <option value="">未填写</option>
              <option value="male">男 / Male</option>
              <option value="female">女 / Female</option>
              <option value="other">其他 / Other</option>
            </select>
          </template>
          <template v-else>
            <span>{{ genderText(displayGender) }}</span>
            <span class="icon-btn" @click="editField('gender')">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
        </div>
      </div>

      <!-- 出生日期 -->
      <div class="profile-field">
        <label>出生日期：</label>
        <div class="profile-value" style="align-items:center;">
          <template v-if="editing === 'birthday'">
            <div class="birthday-inputs" @keydown.enter.stop>
              <input
                ref="birthYearInput"
                v-model.trim="editBirthdayYear"
                class="birthday-year"
                placeholder="年"
                maxlength="4"
                @blur="onBlurAndSave('birthday', $event)"
                inputmode="numeric"
              />
              <select
                ref="birthMonthInput"
                v-model="editBirthdayMonth"
                class="birthday-month"
                @change="onBirthdayChange"
                @blur="onBlurAndSave('birthday', $event)"
              >
                <option value="">月</option>
                <option v-for="m in 12" :key="m" :value="String(m).padStart(2,'0')">{{ String(m).padStart(2,'0') }}</option>
              </select>
              <input
                ref="birthDayInput"
                v-model.trim="editBirthdayDay"
                class="birthday-day"
                placeholder="日"
                maxlength="2"
                @blur="onBlurAndSave('birthday', $event)"
                inputmode="numeric"
              />
            </div>
          </template>
          <template v-else>
            <span>{{ displayBirthday || '未填写' }}</span>
            <span class="icon-btn" @click="editField('birthday')">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
        </div>
      </div>

      <!-- 偏好地区 -->
      <div class="profile-field">
        <label>偏好地区：</label>
        <div class="profile-value">
          <el-cascader
            :options="regionOptions"
            :props="regionProps"
            v-model="editPreferredRegion"
            placeholder="选择省/市/区"
            clearable
            @change="onChangePreferredRegion"
            style="min-width:220px;"
          />
          <div style="margin-left:12px;color:#666;font-size:0.95rem;">{{ displayPreferredRegion || '未填写' }}</div>
        </div>
      </div>

      <!-- 注册时间（只读） -->
      <div class="profile-field">
        <label>注册时间：</label>
        <div class="profile-value">{{ dateJoined || '未填写' }}</div>
      </div>

      <!-- 修改密码 -->
      <div style="display:flex;justify-content:center;margin-top:16px;margin-bottom:8px;">
        <button class="back-btn plain" @click="changePassword">修改密码</button>
      </div>

      <!-- 取消与保存行 -->
      <div style="display:flex;gap:12px;justify-content:center;margin-bottom:12px;">
        <button class="back-btn plain" :disabled="!isDirty || saving" @click="cancelAll" :class="{disabled: !isDirty || saving}">取消修改</button>
        <button class="save-all-btn" :disabled="!isDirty || saving" @click="saveAll">{{ saving ? '保存中...' : '保存全部' }}</button>
      </div>

      <!-- 底部 -->
      <div style="display:flex;gap:12px;justify-content:center;margin-top:6px;flex-wrap:wrap">
        <button class="back-btn" @click="goBack" :disabled="isDirty" :class="{disabled: isDirty}">返回</button>
        <button class="logout-btn" @click="onConfirmLogout">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch, nextTick } from 'vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import { useRouter } from 'vue-router'
import api from '@/api/api'
import Cookies from 'js-cookie'
import defaultAvatar from '/default.png'
import { useUserStore } from '@/stores/user'
import { ElMessage, ElMessageBox } from 'element-plus'
import areasData from '@/assets/areas.json'

/* Basic server fields */
const username = ref('')
const nickname = ref('')
const email = ref('')
const dateJoined = ref('')
const avatar = ref('')
const gender = ref('')
const phone = ref('')
const isStaff = ref(false)
const isSuperuser = ref(false)
const realName = ref('')
const birthday = ref('')
const preferredRegion = ref('') // keep preferred_region; preferred_specialty removed

/* display variables */
const displayNickname = ref('')
const displayEmail = ref('')
const displayPhone = ref('')
const displayRealName = ref('')
const displayGender = ref('')
const displayBirthday = ref('')
const displayPreferredRegion = ref('')

/* edit temp fields */
const editing = ref(null)
const editNickname = ref('')
const editEmail = ref('')
const editGender = ref('')
const editPhone = ref('')
const editRealName = ref('')
const editBirthdayYear = ref('')
const editBirthdayMonth = ref('')
const editBirthdayDay = ref('')
const editPreferredRegion = ref([])
// editPreferredSpecialty removed

/* refs for birthday inputs to coordinate focus handling */
const birthYearInput = ref(null)
const birthMonthInput = ref(null)
const birthDayInput = ref(null)

/* avatar */
const avatarInput = ref(null)
const avatarTimestamp = ref(Date.now())

const router = useRouter()
const store = useUserStore()
const isAdmin = computed(() => isStaff.value || isSuperuser.value)
const validAvatar = computed(() => {
  let src = avatar.value
  if (!src || src === 'null' || src === 'None' || src === '/media/None' || src === 'undefined') {
    return defaultAvatar
  }
  if (!/^https?:\/\//.test(src) && !src.startsWith('/')) {
    src = '/' + src
  }
  return src + '?t=' + avatarTimestamp.value
})

/* cropper */
const cropVisible = ref(false)
const cropper = ref(null)
const cropperImg = ref(null)
const cropImageUrl = ref('')
const uploadingAvatar = ref(false)

/* saving state */
const saving = ref(false)

/* cascader */
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
regionOptions.value = buildCascaderOptionsFromTree(areasData)

/* local draft key */
const DRAFT_KEY = `profile_draft_v1_${''}`

/* Validation flags */
const phoneError = ref(false)
const emailError = ref(false)

/* strict Chinese phone rule and email rule */
const chinaPhoneRegex = /^1[3-9]\d{9}$/
const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

/* helper validators used during load/save/final-check */
function normalizeToDigits(s) { return String(s || '').replace(/[^\d]/g, '').trim() }
function testPhone(s) {
  const raw = String(s || '').trim()
  if (!raw || raw === '未填写') return null // empty
  const digits = normalizeToDigits(raw)
  return { ok: chinaPhoneRegex.test(digits), digits }
}
function testEmail(s) {
  const raw = String(s || '').trim()
  if (!raw || raw === '未填写') return null
  return { ok: emailRegex.test(raw), value: raw }
}

function loadLocalDraft() {
  try {
    console.log('[profile] loadLocalDraft start, key=', DRAFT_KEY)
    const raw = localStorage.getItem(DRAFT_KEY)
    if (!raw) { console.log('[profile] loadLocalDraft: no draft found'); return }
    const obj = JSON.parse(raw)
    if (!obj) { console.log('[profile] loadLocalDraft: parsed null'); return }
    if (obj.editNickname !== undefined) editNickname.value = obj.editNickname
    if (obj.editEmail !== undefined) editEmail.value = obj.editEmail
    if (obj.editGender !== undefined) editGender.value = obj.editGender
    if (obj.editPhone !== undefined) editPhone.value = obj.editPhone
    if (obj.editRealName !== undefined) editRealName.value = obj.editRealName
    if (obj.editBirthdayYear !== undefined) editBirthdayYear.value = obj.editBirthdayYear
    if (obj.editBirthdayMonth !== undefined) editBirthdayMonth.value = obj.editBirthdayMonth
    if (obj.editBirthdayDay !== undefined) editBirthdayDay.value = obj.editBirthdayDay
    if (obj.editPreferredRegion !== undefined) editPreferredRegion.value = obj.editPreferredRegion
    console.log('[profile] loadLocalDraft loaded', obj)

    // validate loaded draft immediately so format errors can't be bypassed by refresh
    const emailCheck = testEmail(editEmail.value)
    if (emailCheck === null) {
      emailError.value = false
    } else {
      emailError.value = !emailCheck.ok
    }
    const phoneCheck = testPhone(editPhone.value)
    if (phoneCheck === null) {
      phoneError.value = false
    } else {
      phoneError.value = !phoneCheck.ok
    }

    applyDraftToDisplay()
  } catch (e) { console.log('loadLocalDraft failed', e) }
}

function saveLocalDraft() {
  try {
    const payload = {
      editNickname: editNickname.value,
      editEmail: editEmail.value,
      editGender: editGender.value,
      editPhone: editPhone.value,
      editRealName: editRealName.value,
      editBirthdayYear: editBirthdayYear.value,
      editBirthdayMonth: editBirthdayMonth.value,
      editBirthdayDay: editBirthdayDay.value,
      editPreferredRegion: editPreferredRegion.value
    }
    localStorage.setItem(DRAFT_KEY, JSON.stringify(payload))
    console.log('[profile] saveLocalDraft saved', payload)
  } catch (e) { console.log('saveLocalDraft failed', e) }
}
function clearLocalDraft() { try { localStorage.removeItem(DRAFT_KEY); console.log('[profile] clearLocalDraft removed key') } catch (e) { console.log('clearLocalDraft failed', e) } }

function applyDraftToDisplay() {
  displayNickname.value = (editNickname.value === '未填写' ? '' : (editNickname.value || nickname.value || ''))
  displayEmail.value = (editEmail.value === '未填写' ? '' : (editEmail.value || email.value || ''))
  displayPhone.value = (editPhone.value === '未填写' ? '' : (editPhone.value || phone.value || ''))
  displayRealName.value = (editRealName.value === '未填写' ? '' : (editRealName.value || realName.value || ''))
  displayGender.value = (editGender.value || gender.value || '')
  const built = buildBirthdayFromParts()
  displayBirthday.value = built || birthday.value || ''
  const regionLabels = getLabelsByValues(editPreferredRegion.value || [], regionOptions.value)
  displayPreferredRegion.value = regionLabels.length ? regionLabels.join('/') : (preferredRegion.value || '')
}

/* helpers */
function getCookie(name) { const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)'); return m ? decodeURIComponent(m.pop()) : '' }
async function ensureCsrf() { if (!getCookie('csrftoken')) { try { await api.get('/accounts/csrf/', { withCredentials: true }) } catch (e) {} } }

function formatDateForBackend(val) {
  if (!val && val !== '') return null
  if (val === '') return null
  if (typeof val === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(val)) return val
  if (typeof val === 'string' && val.indexOf('T') !== -1) return val.split('T')[0]
  const d = new Date(val)
  if (!isNaN(d.getTime())) return d.toISOString().slice(0, 10)
  return null
}
function parseBirthdayToParts(val) {
  const normalized = formatDateForBackend(val)
  if (!normalized) return { y: '', m: '', d: '' }
  const parts = normalized.split('-')
  return { y: parts[0], m: parts[1], d: parts[2] }
}
function normalizeYearInput() {
  let y = String(editBirthdayYear.value || '').trim()
  if (!y) { editBirthdayYear.value = ''; return }
  y = y.replace(/[^\d]/g, '')
  if (y.length === 2) {
    const n = parseInt(y, 10)
    const full = n >= 70 ? 1900 + n : 2000 + n
    editBirthdayYear.value = String(full); return
  }
  if (y.length === 3) { editBirthdayYear.value = '0' + y; return }
  if (y.length >= 4) { editBirthdayYear.value = y.slice(0, 4); return }
  if (y.length === 1) { const n = parseInt(y, 10); editBirthdayYear.value = String(2000 + n) }
}
function buildBirthdayFromParts() {
  const y = (editBirthdayYear.value || '').trim()
  const m = (editBirthdayMonth.value || '').trim()
  const d = (editBirthdayDay.value || '').trim()
  if (!y || !m || !d) return null
  const mm = m.padStart(2, '0'); const dd = d.padStart(2, '0')
  const yi = parseInt(y, 10); const mi = parseInt(mm, 10); const di = parseInt(dd, 10)
  if (isNaN(yi) || isNaN(mi) || isNaN(di)) return null
  if (mi < 1 || mi > 12) return null
  if (di < 1 || di > 31) return null
  return `${String(yi).padStart(4,'0')}-${String(mi).padStart(2,'0')}-${String(di).padStart(2,'0')}`
}

/* load user info */
async function fetchUserInfo() {
  try {
    console.log('[profile] fetchUserInfo start')
    const res = await api.get('/accounts/userinfo/', { withCredentials: true })
    const data = res.data || {}
    username.value = data.username || '未填写'
    nickname.value = data.nickname || ''
    email.value = data.email || ''
    avatar.value = data.avatar || ''
    gender.value = data.gender || ''
    phone.value = data.phone || ''
    dateJoined.value = data.date_joined ? data.date_joined.split('T')[0] : ''
    isStaff.value = !!data.is_staff
    isSuperuser.value = !!data.is_superuser
    realName.value = data.real_name || ''
    preferredRegion.value = data.preferred_region || ''
    // preferred_specialty removed from frontend

    if (data.birthday) {
      const parts = parseBirthdayToParts(data.birthday)
      birthday.value = parts.y && parts.m && parts.d ? `${parts.y}-${parts.m}-${parts.d}` : ''
      editBirthdayYear.value = parts.y; editBirthdayMonth.value = parts.m; editBirthdayDay.value = parts.d
    } else {
      birthday.value = ''; editBirthdayYear.value = ''; editBirthdayMonth.value = ''; editBirthdayDay.value = ''
    }

    // init edit fields from server
    editNickname.value = nickname.value
    editEmail.value = email.value
    editGender.value = gender.value
    editPhone.value = phone.value
    editRealName.value = realName.value

    // parse preferredRegion into cascader values but validate format first
    editPreferredRegion.value = []
    if (preferredRegion.value) {
      const ok = validatePreferredRegionFormat(preferredRegion.value)
      if (ok) {
        const labels = preferredRegion.value.split('/').map(s => s.trim()).filter(Boolean)
        const values = mapLabelsToValues(labels, regionOptions.value)
        if (values && values.length) editPreferredRegion.value = values
        else console.warn('Preferred region labels could not be mapped to cascader values:', labels)
      } else {
        console.warn('preferred_region from backend has unexpected format, skipping parse:', preferredRegion.value)
      }
    }

    // overlay draft and apply display; draft validation occurs inside loadLocalDraft
    loadLocalDraft()
    applyDraftToDisplay()

    // ensure error flags reflect effective values after fetch+draft overlay
    const emailCheck = testEmail(editEmail.value)
    emailError.value = emailCheck ? !emailCheck.ok : false
    const phoneCheck = testPhone(editPhone.value)
    phoneError.value = phoneCheck ? !phoneCheck.ok : false

    if (store && typeof store.fetchUser === 'function') await store.fetchUser()
    console.log('[profile] fetchUserInfo done')
  } catch (e) {
    const statusCode = e?.response?.status
    if (statusCode === 401 || statusCode === 403) router.replace('/login')
    else { console.log('fetchUserInfo error', e); ElMessage.error('获取用户信息失败') }
  }
}

/* avatar functions (unchanged) */
async function onAvatarChange(e) {
  const file = e.target.files && e.target.files[0]; if (!file) return
  if (file.size > 5 * 1024 * 1024) { ElMessage.error('文件过大，请选择小于 5MB 的图片'); if (avatarInput.value) avatarInput.value.value = ''; return }
  cropImageUrl.value = URL.createObjectURL(file); cropVisible.value = true; await nextTick()
  if (cropper.value) { cropper.value.destroy(); cropper.value = null }
  cropper.value = new Cropper(cropperImg.value, {
    aspectRatio: 1, viewMode: 1, dragMode: 'move', autoCropArea: 0.9,
    modal: true, background: true, guides: true, highlight: true, movable: true, zoomable: true, scalable: false, rotatable: false, responsive: true,
  })
}

async function confirmCrop() {
  if (!cropper.value) return
  uploadingAvatar.value = true
  try {
    const canvas = cropper.value.getCroppedCanvas({ width: 420, height: 420, imageSmoothingQuality: 'high' })
    const preferWebp = true
    const mimeType = preferWebp ? 'image/webp' : 'image/jpeg'
    let quality = 0.8
    const blobFromCanvas = (q) => new Promise(resolve => canvas.toBlob(resolve, mimeType, q))
    let blob = await blobFromCanvas(quality)
    if (!blob) throw new Error('生成图片失败')
    if (blob.size > 2 * 1024 * 1024 && mimeType === 'image/webp') {
      const jpegBlob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.8))
      if (jpegBlob && jpegBlob.size <= 2 * 1024 * 1024) blob = jpegBlob
    }
    await ensureCsrf()
    const csrftoken = getCookie('csrftoken') || ''
    const ext = blob.type.includes('webp') ? 'webp' : (blob.type.includes('jpeg') ? 'jpg' : 'png')
    const formData = new FormData(); formData.append('avatar', blob, `avatar.${ext}`)
    await api.patch('/accounts/userinfo/', formData, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
    await fetchUserInfo(); avatarTimestamp.value = Date.now(); closeCrop(); ElMessage.success('头像已更新'); clearLocalDraft()
  } catch (err) { console.log(err); ElMessage.error('头像上传失败') } finally { uploadingAvatar.value = false }
}
function closeCrop() { cropVisible.value = false; if (cropper.value) { cropper.value.destroy(); cropper.value = null } cropImageUrl.value = ''; if (avatarInput.value) avatarInput.value.value = '' }
function triggerAvatarUpload() { if (avatarInput.value) avatarInput.value.click() }
function onAvatarError(e) { e.target.src = defaultAvatar }
async function onRemoveAvatar() {
  try { await ElMessageBox.confirm('确认删除头像？', '删除头像', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }) } catch (e) { return }
  uploadingAvatar.value = true
  try {
    await ensureCsrf(); const csrftoken = getCookie('csrftoken') || ''
    await api.patch('/accounts/userinfo/', { avatar: null }, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
    await fetchUserInfo(); avatarTimestamp.value = Date.now(); ElMessage.success('头像已删除'); clearLocalDraft()
  } catch (e) { console.log(e); ElMessage.error('删除失败') } finally { uploadingAvatar.value = false }
}

/* edit entry */
function editField(field) {
  editing.value = field
  if (field === 'nickname') editNickname.value = editNickname.value || nickname.value
  if (field === 'email') editEmail.value = editEmail.value || email.value
  if (field === 'gender') editGender.value = editGender.value || gender.value
  if (field === 'phone') {
    // Clear placeholder '未填写' to make input empty for typing
    if ((String(editPhone.value || '').trim() === '未填写') || (!editPhone.value && !phone.value)) editPhone.value = ''
    else editPhone.value = editPhone.value || phone.value
    // clear error when user starts editing (they may fix it)
    phoneError.value = false
  }
  if (field === 'real_name') editRealName.value = editRealName.value || realName.value
  if (field === 'birthday') { /* parts already initialized */ }
}

/*
  通用校验函数（与前面约定相同）。
  注意：我们同时在 loadLocalDraft/fetchUserInfo/saveAll 做最终验证，避免刷新绕过验证。
*/
function onGenericInput(editRef, errorRef, regex, displayRef, normalizeForTest) {
  const raw = String(editRef.value || '').trim()
  console.log('[profile] onGenericInput raw=', raw)

  const testVal = normalizeForTest ? normalizeForTest(raw) : raw
  try {
    if (testVal && regex.test(testVal)) {
      errorRef.value = false
    }
  } catch (e) {
    console.log('[profile] onGenericInput regex test failed', e)
  }

  saveLocalDraft()
  if (displayRef) displayRef.value = editRef.value || ''
}

function onGenericBlur(editRef, errorRef, regex, displayRef, normalizeForTest, normalizeForSave) {
  const raw = String(editRef.value || '').trim()
  console.log('[profile] onGenericBlur raw=', raw)

  if (!raw) {
    editRef.value = '未填写'
    errorRef.value = false
    saveLocalDraft(); applyDraftToDisplay(); editing.value = null
    return
  }

  const testVal = normalizeForTest ? normalizeForTest(raw) : raw
  try {
    if (!regex.test(testVal)) {
      errorRef.value = true
      saveLocalDraft()
      return
    }
  } catch (e) {
    console.log('[profile] onGenericBlur regex test failed', e)
    errorRef.value = true
    saveLocalDraft()
    return
  }

  const finalVal = normalizeForSave ? normalizeForSave(testVal) : testVal
  errorRef.value = false
  editRef.value = finalVal
  saveLocalDraft(); applyDraftToDisplay(); editing.value = null
}

/* --- 保持邮箱的原始逻辑（未改变） --- */
function onEmailInput() {
  const raw = String(editEmail.value || '').trim()
  console.log('[profile] onEmailInput raw=', raw)
  if (raw && emailRegex.test(raw)) {
    emailError.value = false
  }
  saveLocalDraft()
  displayEmail.value = editEmail.value || ''
}

function onBlurEmail() {
  const raw = String(editEmail.value || '').trim()
  console.log('[profile] onBlurEmail raw=', raw)
  if (!raw) {
    editEmail.value = '未填写'
    emailError.value = false
    saveLocalDraft(); applyDraftToDisplay(); editing.value = null
    return
  }
  if (!emailRegex.test(raw)) {
    emailError.value = true
    saveLocalDraft()
    return
  }
  emailError.value = false
  editEmail.value = raw
  saveLocalDraft(); applyDraftToDisplay(); editing.value = null
}

/* --- 手机使用通用函数 --- */
function onPhoneInput() {
  onGenericInput(editPhone, phoneError, chinaPhoneRegex, displayPhone, normalizeToDigits)
}

function onBlurPhone() {
  onGenericBlur(editPhone, phoneError, chinaPhoneRegex, displayPhone, normalizeToDigits, (v) => String(v || '').replace(/[^\d]/g, '').trim())
}

/* other blur save */
/**
 * Improved onBlurAndSave:
 * - Accepts optional event to detect where focus moved.
 * - For 'birthday' field, defer finalizing (editing = null) if focus moved to another birthday input (year/month/day),
 *   preventing the inputs from disappearing when user switches between them.
 */
function onBlurAndSave(field, ev) {
  if (field === 'birthday') normalizeYearInput()

  // For birthday, we need to allow focus transitions between the three inputs.
  if (field === 'birthday') {
    // small deferral to allow document.activeElement to update
    setTimeout(() => {
      const active = document.activeElement
      const yearEl = birthYearInput.value
      const monthEl = birthMonthInput.value
      const dayEl = birthDayInput.value
      // If focus moved to another birthday input, do not finalize editing (keep inputs visible)
      if (active === yearEl || active === monthEl || active === dayEl) {
        // still save draft but keep editing open
        saveLocalDraft(); applyDraftToDisplay()
        return
      }
      // otherwise finalize
      // same logic as original: normalize empty -> '未填写'
      const built = buildBirthdayFromParts()
      if (!built) { editBirthdayYear.value = ''; editBirthdayMonth.value = ''; editBirthdayDay.value = '' }
      saveLocalDraft(); applyDraftToDisplay(); editing.value = null
    }, 10)
    return
  }

  // Non-birthday fields: original behavior
  switch (field) {
    case 'nickname':
      if (!String(editNickname.value || '').trim()) editNickname.value = '未填写'
      break
    case 'real_name':
      if (!String(editRealName.value || '').trim()) editRealName.value = '未填写'
      break
    default: break
  }
  saveLocalDraft(); applyDraftToDisplay(); editing.value = null
}

/* Birthday month change should not close editing - just persist and update display */
function onBirthdayChange() {
  normalizeYearInput()
  saveLocalDraft()
  applyDraftToDisplay()
}

/* cascader change */
function onChangePreferredRegion(value) {
  console.log('[profile] onChangePreferredRegion values=', value)
  saveLocalDraft()
  const labels = getLabelsByValues(value || [], regionOptions.value)
  displayPreferredRegion.value = labels.length ? labels.join('/') : ''
  saveLocalDraft()
}

/* preferred region format validator:
   accept 1-3 components separated by '/', non-empty labels (no extra slashes) */
function validatePreferredRegionFormat(s) {
  if (!s || typeof s !== 'string') return false
  const parts = s.split('/').map(p => p.trim()).filter(Boolean)
  if (parts.length === 0 || parts.length > 3) return false
  return parts.every(p => p.length > 0 && !p.includes('/'))
}

/* helper to get labels by cascader values */
function getLabelsByValues(values = [], options = []) {
  const labels = []
  let cur = options
  for (const v of (values || [])) {
    if (!cur || !cur.length) break
    const found = cur.find(o => String(o.value) === String(v))
    if (!found) break
    labels.push(found.label)
    cur = found.children || []
  }
  return labels
}

/* fallback: map values -> label by searching options recursively (safeguard) */
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
    else labels.push(String(v)) // fallback to value text to avoid losing info
  }
  return labels
}

/* isDirty detection */
function norm(v) { return (v === '未填写' ? '' : (v || '')) }
const isDirty = computed(() => {
  if (norm(editNickname.value) !== norm(nickname.value)) return true
  if (norm(editEmail.value) !== norm(email.value)) return true
  if (norm(editGender.value) !== norm(gender.value)) return true
  if (norm(editPhone.value) !== norm(phone.value)) return true
  if (norm(editRealName.value) !== norm(realName.value)) return true
  // preferred_specialty removed from isDirty
  const built = buildBirthdayFromParts()
  const curBirthday = birthday.value || null
  if ((built || null) !== (curBirthday || null)) return true
  const curRegionLabels = preferredRegion.value ? (preferredRegion.value.includes('/') ? preferredRegion.value.split('/').map(s=>s.trim()) : [preferredRegion.value]) : []
  const editRegionLabels = getLabelsByValues(editPreferredRegion.value || [], regionOptions.value)
  if (JSON.stringify(curRegionLabels) !== JSON.stringify(editRegionLabels)) return true
  return false
})

/* saveAll: perform final validation (don't rely only on flags) to avoid refresh-bypass */
async function saveAll() {
  // perform final checks now
  // email
  const emailRaw = String(editEmail.value || '').trim()
  if (emailRaw && emailRaw !== '未填写' && !emailRegex.test(emailRaw)) {
    emailError.value = true
    ElMessage.error('请修正邮箱格式后再保存')
    return
  }
  // phone
  const phoneRaw = String(editPhone.value || '').trim()
  if (phoneRaw && phoneRaw !== '未填写') {
    const digits = normalizeToDigits(phoneRaw)
    if (!chinaPhoneRegex.test(digits)) {
      phoneError.value = true
      ElMessage.error('请修正手机号格式后再保存')
      return
    }
    // normalize to digits for payload
    editPhone.value = digits
  }

  if (phoneError.value || emailError.value) {
    ElMessage.error('请先修正表单中的错误后再保存')
    return
  }

  saving.value = true
  normalizeYearInput()
  const birthdayForBackend = buildBirthdayFromParts()

  let regionLabels = getLabelsByValues(editPreferredRegion.value || [], regionOptions.value)
  if ((!regionLabels || regionLabels.length === 0) && (editPreferredRegion.value && editPreferredRegion.value.length)) {
    regionLabels = valuesToLabelsFallback(editPreferredRegion.value || [], regionOptions.value)
  }
  const regionStr = regionLabels && regionLabels.length ? regionLabels.join('/') : ''
  const regionValues = Array.isArray(editPreferredRegion.value) ? editPreferredRegion.value.slice() : []

  const payload = {
    nickname: editNickname.value === '未填写' ? '' : (editNickname.value || nickname.value || ''),
    email: editEmail.value === '未填写' ? '' : (editEmail.value || email.value || ''),
    gender: editGender.value === '未填写' ? '' : (editGender.value || gender.value || ''),
    phone: (editPhone.value === '未填写') ? '' : (editPhone.value || phone.value || ''),
    real_name: editRealName.value === '未填写' ? '' : (editRealName.value || realName.value || ''),
    preferred_region: regionStr,
    preferred_region_values: regionValues,
    // preferred_specialty removed from payload
    birthday: birthdayForBackend
  }

  console.log('[profile] saveAll payload=', payload)
  try {
    await ensureCsrf()
    const csrftoken = getCookie('csrftoken') || ''
    const res = await api.patch('/accounts/userinfo/', payload, {
      withCredentials: true,
      headers: { 'X-CSRFToken': csrftoken }
    })
    console.log('[profile] saveAll response=', res?.data)
    await fetchUserInfo()
    ElMessage.success('保存成功')
    clearLocalDraft()
  } catch (e) {
    console.log('saveAll error', e)
    const errBody = e?.response?.data
    ElMessage.error('保存失败：' + (errBody ? JSON.stringify(errBody) : '请重试'))
  } finally {
    saving.value = false
  }
}

/* cancel draft */
async function cancelAll() {
  clearLocalDraft(); await fetchUserInfo(); editing.value = null
}

/* mapLabelsToValues */
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

/* misc */
function genderText(g) { if (g === 'male') return '男 / Male'; if (g === 'female') return '女 / Female'; if (g === 'other') return '其他 / Other'; return '未填写' }
function goBack() { if (isDirty.value) return; router.back() }
function changePassword() { router.push('/change-password') }

async function onConfirmLogout() {
  try { await ElMessageBox.confirm('确认退出登录？', '退出登录', { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }) } catch (e) { return }
  await doLogout()
}
async function doLogout() {
  try { await ensureCsrf(); const csrftoken = getCookie('csrftoken') || ''; await api.post('/accounts/logout/', {}, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } }) } catch (e) {} finally { Cookies.remove('access'); Cookies.remove('refresh'); if (store && typeof store.clearAuth === 'function') store.clearAuth(); router.replace('/login') }
}

/* watchers to auto-clear error flags when user fixes input (extra safety) */
watch(editPhone, (v) => {
  const raw = String(v || '').replace(/[\s\-]/g, '').trim()
  if (raw && chinaPhoneRegex.test(raw)) phoneError.value = false
})
watch(editEmail, (v) => {
  const raw = String(v || '').trim()
  if (raw && emailRegex.test(raw)) emailError.value = false
})

/* init */
onMounted(async () => { console.log('[profile] onMounted'); await ensureCsrf(); await fetchUserInfo() })
</script>

<style scoped>
/*（保留 original styles, plus disabled styling） */
.profile-fullscreen {
  min-height: 100vh; background: #f4f8fc;
  display: flex; align-items: center; justify-content: center;
}
.profile-form {
  background: #fff; border-radius: 20px; box-shadow: 0 8px 32px rgba(60,60,80,0.15);
  min-width: 340px; max-width: 98vw; width: 560px;
  padding: 40px 32px 28px 32px; display: flex; flex-direction: column;
  align-items: stretch;
}
.profile-title {
  text-align: center; font-weight: 700; font-size: 1.9rem;
  color: #234; margin-bottom: 28px;
  letter-spacing: 2px;
}
.profile-field {
  display: flex; flex-direction: row; align-items: center;
  border-bottom: 1px solid #f1f3f6; padding: 14px 0;
}
.avatar-row { align-items: flex-start; }
.avatar-img {
  width: 72px; height: 72px; border-radius: 50%;
  object-fit: cover; border: 2px solid #6a85e6;
  box-shadow: 0 1px 7px #c3cfe2; margin-right: 16px; background: #eee;
}
.avatar-edit-btn {
  padding: 8px 16px; font-size: 0.98rem;
  background: linear-gradient(90deg, #6a85e6 0%, #43cea2 100%);
  color: #fff; border: none; border-radius: 7px; cursor: pointer; font-weight: 500; transition: background 0.18s;
}
.avatar-edit-btn.plain { background: transparent; color: #6a85e6; border: 1px solid rgba(106,133,230,0.16); }
.avatar-edit-btn:hover { background: linear-gradient(90deg, #43cea2 0%, #6a85e6 100%); }
.avatar-upload { display: none; }
label { font-size: 1.02rem; color: #888; width: 120px; text-align: right; margin-right: 14px; flex-shrink: 0; }
.profile-value { flex: 1; display: flex; align-items: center; font-size: 1.04rem; color: #234; }
.edit-input { font-size: 1.02rem; padding: 7px 10px; border: 1.4px solid #e1e8f8; border-radius: 6px; outline: none; margin-right: 8px; width: 220px; max-width: 70vw; }
.edit-input.invalid { border-color: #f56c6c; box-shadow: 0 0 0 3px rgba(245,108,108,0.06); }
.field-error small { color: #f56c6c; margin-top: 6px; display: block; }

/* birthday styles */
.birthday-inputs { display: flex; gap: 8px; align-items: center; }
.birthday-year, .birthday-month, .birthday-day { padding: 6px 8px; border-radius: 6px; border: 1.2px solid #e1e8f8; font-size: 1rem; width: 86px; text-align: center; }
.birthday-month { width: 78px; } .birthday-day { width: 64px; }

/* Buttons */
.icon-btn { margin-left: 9px; cursor: pointer; display: flex; align-items: center; transition: opacity 0.16s; }
.icon-btn:hover { opacity: 0.7; }
.admin-tag { background: #ff9800; color: #fff; font-size: 0.9rem; border-radius: 6px; padding: 2px 10px; margin-left: 10px; font-weight: 500; }
.back-btn { background: linear-gradient(90deg, #6a85e6 0%, #43cea2 100%); color: #fff; border: none; border-radius: 8px; padding: 10px 22px; font-size: 1rem; cursor: pointer; font-weight: 600; transition: background 0.2s; }
.back-btn.plain { background: transparent; color: #6a85e6; border: 1px solid rgba(106,133,230,0.14); }
.save-all-btn { background: #43cea2; color:#fff; border:none; border-radius:8px; padding:10px 18px; font-weight:600; }
.logout-btn { background: #fff; color:#d32f2f; border:1px solid rgba(211,47,47,0.12); border-radius:8px; padding:10px 18px; font-weight:600; }

/* disabled state */
button[disabled], .disabled { opacity: 0.45; cursor: not-allowed; pointer-events: none; }

/* cropper styles kept as before */
.small { font-size:0.92rem; color:#6c7a89; } .text-muted { color:#8a98a8; }
:deep(.cropper-container .cropper-modal) { opacity: 0.55 !important; background: rgba(0,0,0,0.55) !important; }
:deep(.cropper-modal) { background: #fff !important; opacity: 1 !important; }
.cropper-modal { position: fixed; left: 0; top: 0; width: 100vw; height: 100vh; background: rgba(0,0,0,0.55); z-index: 9999; display: flex; align-items: center; justify-content: center; }
.cropper-body { background: rgba(255,255,255,0.06); padding: 12px; border-radius: 10px; box-shadow: 0 8px 32px rgba(8,12,20,0.45); display: flex; flex-direction: column; align-items: center; max-width: 90vw; max-height: 90vh; }
.cropper-img { max-width: 640px; max-height: 80vh; border-radius: 6px; border: 1px solid rgba(0,0,0,0.08); object-fit: contain; }
.crop-btn { margin: 0 12px; background: linear-gradient(90deg, #6a85e6 0%, #43cea2 100%); border: none; border-radius: 7px; color: #fff; padding: 8px 32px; font-size: 1.02rem; font-weight: 500; cursor: pointer; transition: background 0.18s; }
.crop-btn.cancel { background: #bdbdbd; color: #fff; }
.crop-btn:not(.cancel):hover { background: linear-gradient(90deg, #43cea2 0%, #6a85e6 100%); }

@media (max-width: 600px) {
  .profile-form { padding: 18px 3vw 16px 3vw; width: 94vw; }
  .profile-title { font-size: 1.25rem; margin-bottom: 18px; }
  .edit-input { width: 120px; }
  label { width: 86px; font-size: 0.97rem; }
  .profile-value { font-size: 0.98rem; }
  .avatar-img { width: 56px; height: 56px; }
  .back-btn { padding: 8px 14px; font-size: 0.98rem; }
  .avatar-edit-btn { padding: 6px 10px; font-size: 0.95rem; }
  .cropper-img { max-width: 90vw; }
  .birthday-year { width: 90px; }
  .birthday-month { width: 80px; }
  .birthday-day { width: 70px; }
}
</style>