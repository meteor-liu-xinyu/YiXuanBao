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
              <button class="avatar-edit-btn plain" @click="removeAvatar" :disabled="uploadingAvatar">
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

      <!-- 昵称（可编辑） -->
      <div class="profile-field">
        <label>昵称：</label>
        <div class="profile-value">
          <template v-if="editing === 'nickname'">
            <input v-model="editNickname" class="edit-input" />
            <span class="icon-btn" @click="saveField('nickname')" :title="'保存'">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M6 12.5L9.5 16L16 8.5" stroke="#43cea2" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
          <template v-else>
            <span>{{ nickname || '未填写' }}</span>
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
            <input v-model="editRealName" class="edit-input" />
            <span class="icon-btn" @click="saveField('real_name')" :title="'保存'">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M6 12.5L9.5 16L16 8.5" stroke="#43cea2" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
          <template v-else>
            <span>{{ realName || '未填写' }}</span>
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
        <div class="profile-value">
          <template v-if="editing === 'email'">
            <input v-model="editEmail" class="edit-input" />
            <span class="icon-btn" @click="saveField('email')" :title="'保存'">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M6 12.5L9.5 16L16 8.5" stroke="#43cea2" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
          <template v-else>
            <span>{{ email || '未填写' }}</span>
            <span class="icon-btn" @click="editField('email')">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
        </div>
      </div>

      <!-- 电话 -->
      <div class="profile-field">
        <label>手机号：</label>
        <div class="profile-value">
          <template v-if="editing === 'phone'">
            <input v-model="editPhone" class="edit-input" />
            <span class="icon-btn" @click="saveField('phone')" :title="'保存'">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M6 12.5L9.5 16L16 8.5" stroke="#43cea2" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
          <template v-else>
            <span>{{ phone || '未填写' }}</span>
            <span class="icon-btn" @click="editField('phone')">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
        </div>
      </div>

      <!-- 性别 -->
      <div class="profile-field">
        <label>性别：</label>
        <div class="profile-value">
          <template v-if="editing === 'gender'">
            <select v-model="editGender" class="edit-input" style="width:140px">
              <option value="">未填写</option>
              <option value="male">男 / Male</option>
              <option value="female">女 / Female</option>
              <option value="other">其他 / Other</option>
            </select>
            <span class="icon-btn" @click="saveField('gender')" :title="'保存'">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M6 12.5L9.5 16L16 8.5" stroke="#43cea2" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
          <template v-else>
            <span>{{ genderText(gender) }}</span>
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
        <div class="profile-value">
          <template v-if="editing === 'birthday'">
            <input v-model="editBirthday" type="date" class="edit-input" style="width:160px"/>
            <span class="icon-btn" @click="saveField('birthday')" :title="'保存'">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M6 12.5L9.5 16L16 8.5" stroke="#43cea2" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
          <template v-else>
            <span>{{ birthday || '未填写' }}</span>
            <span class="icon-btn" @click="editField('birthday')">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
        </div>
      </div>

      <!-- 地址 -->
      <div class="profile-field">
        <label>地址：</label>
        <div class="profile-value">
          <template v-if="editing === 'address'">
            <input v-model="editAddress" class="edit-input" />
            <span class="icon-btn" @click="saveField('address')" :title="'保存'">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M6 12.5L9.5 16L16 8.5" stroke="#43cea2" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
          <template v-else>
            <span>{{ address || '未填写' }}</span>
            <span class="icon-btn" @click="editField('address')">
              <svg width="22" height="22" viewBox="0 0 22 22" fill="none">
                <path d="M3 19L8.5 17.5L19 7.5L14.5 3L4.5 13.5L3 19Z" stroke="#6a85e6" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
            </span>
          </template>
        </div>
      </div>

      <!-- 偏好医院/专科 -->
      <div class="profile-field">
        <label>偏好地区：</label>
        <div class="profile-value">
          <input v-model="editPreferredRegion" class="edit-input" placeholder="例如：北京/上海" />
        </div>
      </div>

      <div class="profile-field">
        <label>偏好专科：</label>
        <div class="profile-value">
          <input v-model="editPreferredSpecialty" class="edit-input" placeholder="例如：肿瘤科/心内科" />
        </div>
      </div>

      <!-- 注册时间（只读） -->
      <div class="profile-field">
        <label>注册时间：</label>
        <div class="profile-value">{{ dateJoined || '未填写' }}</div>
      </div>

      <!-- 操作按钮 -->
      <div style="display:flex;gap:12px;justify-content:center;margin-top:20px;flex-wrap:wrap">
        <button class="back-btn" @click="goBack">返回</button>

        <button class="back-btn plain" @click="changePassword">修改密码</button>

        <button class="save-all-btn" :disabled="saving" @click="saveAll">
          {{ saving ? '保存中...' : '保存全部' }}
        </button>

        <button class="logout-btn" @click="confirmLogout">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, nextTick } from 'vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import { useRouter } from 'vue-router'
import api from '@/api/api'
import Cookies from 'js-cookie'
import defaultAvatar from '/default.png'
import { useUserStore } from '@/stores/user'

/* 基本字段 */
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
const address = ref('')
const birthday = ref('')
const preferredRegion = ref('')
const preferredSpecialty = ref('')

/* edit 临时字段 */
const editing = ref(null)
const editNickname = ref('')
const editEmail = ref('')
const editGender = ref('')
const editPhone = ref('')
const editRealName = ref('')
const editAddress = ref('')
const editBirthday = ref('')
const editPreferredRegion = ref('')
const editPreferredSpecialty = ref('')

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

/* 裁剪相关 */
const cropVisible = ref(false)
const cropper = ref(null)
const cropperImg = ref(null)
const cropImageUrl = ref('')
const uploadingAvatar = ref(false)

/* loading/saving */
const saving = ref(false)

/* 帮助函数：读取 cookie 与确保 csrftoken */
function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return m ? decodeURIComponent(m.pop()) : ''
}
async function ensureCsrf() {
  if (!getCookie('csrftoken')) {
    try {
      await api.get('/accounts/csrf/', { withCredentials: true })
    } catch (e) {
      // ignore
    }
  }
}

/* 加载用户信息 */
async function fetchUserInfo() {
  try {
    const res = await api.get('/accounts/userinfo/', { withCredentials: true })
    const data = res.data
    username.value = data.username || '未填写'
    nickname.value = data.nickname || ''
    email.value = data.email || ''
    avatar.value = data.avatar || ''
    gender.value = data.gender || ''
    phone.value = data.phone || ''
    dateJoined.value = data.date_joined ? data.date_joined.split('T')[0] : ''
    isStaff.value = !!data.is_staff
    isSuperuser.value = !!data.is_superuser
    realName.value = data.real_name || data.full_name || ''
    address.value = data.address || ''
    birthday.value = data.birthday || ''
    preferredRegion.value = data.preferred_region || ''
    preferredSpecialty.value = data.preferred_specialty || ''

    // 初始化可编辑字段（用于保存全部）
    editNickname.value = nickname.value
    editEmail.value = email.value
    editGender.value = gender.value
    editPhone.value = phone.value
    editRealName.value = realName.value
    editAddress.value = address.value
    editBirthday.value = birthday.value
    editPreferredRegion.value = preferredRegion.value
    editPreferredSpecialty.value = preferredSpecialty.value

    // 让全局 store 同步（如果需要）
    if (store && typeof store.fetchUser === 'function') {
      await store.fetchUser()
    }
  } catch (e) {
    // 如果 403/401 => 跳转到登录（会话失效或 CSRF 问题）
    const status = e?.response?.status
    if (status === 401 || status === 403) {
      console.warn('fetchUserInfo unauthorized, redirect to login', e)
      router.replace('/login')
    } else {
      console.error('fetchUserInfo error', e)
    }
  }
}

/* 头像上传流程 */
async function onAvatarChange(e) {
  const file = e.target.files[0]
  if (!file) return
  // 简单大小校验
  if (file.size > 5 * 1024 * 1024) {
    alert('文件过大，请选择小于 5MB 的图片')
    return
  }
  cropImageUrl.value = URL.createObjectURL(file)
  cropVisible.value = true
  await nextTick()
  if (cropper.value) {
    cropper.value.destroy()
    cropper.value = null
  }
  cropper.value = new Cropper(cropperImg.value, {
    aspectRatio: 1,
    viewMode: 1,
    dragMode: 'move',
    autoCropArea: 1,
    background: false,
    movable: true,
    zoomable: true,
    scalable: false,
    rotatable: false,
  })
}

async function confirmCrop() {
  if (!cropper.value) return
  uploadingAvatar.value = true
  try {
    const canvas = cropper.value.getCroppedCanvas({
      width: 300,
      height: 300,
      imageSmoothingQuality: 'high'
    })

    const preferWebp = true
    const mimeType = preferWebp ? 'image/webp' : 'image/jpeg'
    let quality = 0.8

    // 生成 blob 并在需要时降质重试
    const blobFromCanvas = (q) => new Promise(resolve => canvas.toBlob(resolve, mimeType, q))
    let blob = await blobFromCanvas(quality)
    if (!blob) throw new Error('生成图片失败')
    if (blob.size > 2 * 1024 * 1024 && mimeType === 'image/jpeg') {
      quality = 0.6
      blob = await blobFromCanvas(quality)
    }

    // 上传前确保 csrftoken
    await ensureCsrf()
    const csrftoken = getCookie('csrftoken') || ''

    const ext = mimeType.includes('webp') ? 'webp' : 'jpg'
    const formData = new FormData()
    formData.append('avatar', blob, `avatar.${ext}`)

    // 不要设置 Content-Type，浏览器 会自动添加 boundary
    await api.patch('/accounts/userinfo/', formData, {
      withCredentials: true,
      headers: { 'X-CSRFToken': csrftoken }
    })

    await fetchUserInfo()
    avatarTimestamp.value = Date.now()
    closeCrop()
  } catch (err) {
    console.error(err)
    alert('头像上传失败')
  } finally {
    uploadingAvatar.value = false
  }
}

function closeCrop() {
  cropVisible.value = false
  if (cropper.value) {
    cropper.value.destroy()
    cropper.value = null
  }
  cropImageUrl.value = ''
  if (avatarInput.value) avatarInput.value.value = ''
}

function triggerAvatarUpload() {
  avatarInput.value && avatarInput.value.click()
}

function onAvatarError(e) {
  e.target.src = defaultAvatar
}

async function removeAvatar() {
  if (!confirm('确认删除头像？')) return
  uploadingAvatar.value = true
  try {
    await ensureCsrf()
    const csrftoken = getCookie('csrftoken') || ''
    await api.patch('/accounts/userinfo/', { avatar: null }, {
      withCredentials: true,
      headers: { 'X-CSRFToken': csrftoken }
    })
    await fetchUserInfo()
    avatarTimestamp.value = Date.now()
  } catch (e) {
    console.error(e)
    alert('删除失败')
  } finally {
    uploadingAvatar.value = false
  }
}

/* 编辑字段逻辑 */
function editField(field) {
  editing.value = field
  if (field === 'nickname') editNickname.value = nickname.value
  if (field === 'email') editEmail.value = email.value
  if (field === 'gender') editGender.value = gender.value
  if (field === 'phone') editPhone.value = phone.value
  if (field === 'real_name') editRealName.value = realName.value
  if (field === 'address') editAddress.value = address.value
  if (field === 'birthday') editBirthday.value = birthday.value
}

/* 保存单字段 */
async function saveField(field) {
  const prevEditing = editing.value
  let payload = {}
  if (field === 'nickname') payload.nickname = editNickname.value
  if (field === 'email') payload.email = editEmail.value
  if (field === 'gender') payload.gender = editGender.value
  if (field === 'phone') payload.phone = editPhone.value
  if (field === 'real_name') payload.real_name = editRealName.value
  if (field === 'address') payload.address = editAddress.value
  if (field === 'birthday') payload.birthday = editBirthday.value

  try {
    await ensureCsrf()
    const csrftoken = getCookie('csrftoken') || ''
    await api.patch('/accounts/userinfo/', payload, {
      withCredentials: true,
      headers: { 'X-CSRFToken': csrftoken }
    })
    await fetchUserInfo()
    editing.value = null
  } catch (e) {
    console.error('saveField error', e)
    if (e?.response?.status === 403) {
      alert('请求被拒绝，请重新登录')
      router.replace('/login')
    } else {
      alert('保存失败，请检查格式或重试')
    }
    editing.value = prevEditing
  }
}

/* 保存全部（包含偏好） */
async function saveAll() {
  saving.value = true
  const payload = {
    nickname: editNickname.value || nickname.value,
    email: editEmail.value || email.value,
    gender: editGender.value || gender.value,
    phone: editPhone.value || phone.value,
    real_name: editRealName.value || realName.value,
    address: editAddress.value || address.value,
    birthday: editBirthday.value || birthday.value,
    preferred_region: editPreferredRegion.value || preferredRegion.value,
    preferred_specialty: editPreferredSpecialty.value || preferredSpecialty.value
  }
  try {
    await ensureCsrf()
    const csrftoken = getCookie('csrftoken') || ''
    await api.patch('/accounts/userinfo/', payload, {
      withCredentials: true,
      headers: { 'X-CSRFToken': csrftoken }
    })
    await fetchUserInfo()
    alert('保存成功')
  } catch (e) {
    console.error('saveAll error', e)
    if (e?.response?.status === 403) {
      alert('请求被拒绝，请重新登录')
      router.replace('/login')
    } else {
      alert('保存全部失败，请重试')
    }
  } finally {
    saving.value = false
  }
}

/* 其他工具方法 */
function genderText(g) {
  if (g === 'male') return '男 / Male'
  if (g === 'female') return '女 / Female'
  if (g === 'other') return '其他 / Other'
  return '未填写'
}

/* 返回 */
function goBack() {
  router.back()
}

/* 修改密码跳转（假设有对应页面） */
function changePassword() {
  router.push('/change-password')
}

/* 退出登录 */
async function doLogout() {
  try {
    await ensureCsrf()
    const csrftoken = getCookie('csrftoken') || ''
    await api.post('/accounts/logout/', {}, {
      withCredentials: true,
      headers: { 'X-CSRFToken': csrftoken }
    })
  } catch (e) {
    // ignore backend error but continue cleanup
  } finally {
    // Clear client-side auth state if you store tokens locally
    Cookies.remove('access')
    Cookies.remove('refresh')
    // update global store
    if (store && typeof store.clearAuth === 'function') store.clearAuth()
    router.replace('/login')
  }
}

function confirmLogout() {
  if (confirm('确认退出登录？')) {
    doLogout()
  }
}

/* 初始化：先确保 csrftoken 再拉取用户信息 */
onMounted(async () => {
  await ensureCsrf()
  await fetchUserInfo()
})
</script>

<style scoped>
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
.avatar-row {
  align-items: flex-start;
}
.avatar-img {
  width: 72px; height: 72px; border-radius: 50%;
  object-fit: cover; border: 2px solid #6a85e6;
  box-shadow: 0 1px 7px #c3cfe2;
  margin-right: 16px;
  background: #eee;
}
.avatar-edit-btn {
  padding: 8px 16px;
  font-size: 0.98rem;
  background: linear-gradient(90deg, #6a85e6 0%, #43cea2 100%);
  color: #fff;
  border: none;
  border-radius: 7px;
  cursor: pointer;
  font-weight: 500;
  transition: background 0.18s;
}
.avatar-edit-btn.plain {
  background: transparent;
  color: #6a85e6;
  border: 1px solid rgba(106,133,230,0.16);
}
.avatar-edit-btn:hover {
  background: linear-gradient(90deg, #43cea2 0%, #6a85e6 100%);
}
.avatar-upload {
  display: none;
}
label {
  font-size: 1.02rem; color: #888; width: 120px; text-align: right;
  margin-right: 14px; flex-shrink: 0;
}
.profile-value {
  flex: 1;
  display: flex; align-items: center;
  font-size: 1.04rem; color: #234;
}
.edit-input {
  font-size: 1.02rem; padding: 7px 10px;
  border: 1.4px solid #e1e8f8; border-radius: 6px;
  outline: none; margin-right: 8px;
  width: 220px; max-width: 70vw;
}
.icon-btn {
  margin-left: 9px; cursor: pointer; display: flex; align-items: center;
  transition: opacity 0.16s;
}
.icon-btn:hover { opacity: 0.7; }
.admin-tag {
  background: #ff9800;
  color: #fff;
  font-size: 0.9rem;
  border-radius: 6px;
  padding: 2px 10px;
  margin-left: 10px;
  font-weight: 500;
}
.back-btn {
  background: linear-gradient(90deg, #6a85e6 0%, #43cea2 100%);
  color: #fff; border: none; border-radius: 8px; padding: 10px 22px;
  font-size: 1rem; cursor: pointer; font-weight: 600;
  transition: background 0.2s;
}
.back-btn.plain {
  background: transparent;
  color: #6a85e6;
  border: 1px solid rgba(106,133,230,0.14);
}
.save-all-btn {
  background: #43cea2; color:#fff; border:none; border-radius:8px; padding:10px 18px; font-weight:600;
}
.logout-btn {
  background: #fff; color:#d32f2f; border:1px solid rgba(211,47,47,0.12); border-radius:8px; padding:10px 18px; font-weight:600;
}
.small { font-size:0.92rem; color:#6c7a89; }
.text-muted { color:#8a98a8; }

:deep(.cropper-container .cropper-modal) {
  background: #fff !important;
  opacity: 1 !important;
}
:deep(.cropper-modal) {
  background: #fff !important;
  opacity: 1 !important;
}
.cropper-modal {
  position: fixed;
  left: 0; top: 0; width: 100vw; height: 100vh;
  background: rgba(255,255,255,0.98);
  z-index: 9999;
  display: flex; align-items: center; justify-content: center;
}
.cropper-body {
  background: #fff;
  padding: 18px 18px 8px 18px;
  border-radius: 12px;
  box-shadow: 0 2px 16px rgba(24,39,75,0.15);
  display: flex; flex-direction: column; align-items: center;
}
.cropper-img {
  max-width: 420px; max-height: 420px; min-width: 180px;
  border-radius: 8px;
  border: 1px solid #ddd;
}
.crop-btn {
  margin: 0 12px;
  background: linear-gradient(90deg, #6a85e6 0%, #43cea2 100%);
  border: none;
  border-radius: 7px;
  color: #fff;
  padding: 8px 32px;
  font-size: 1.02rem;
  font-weight: 500;
  cursor: pointer;
  transition: background 0.18s;
}
.crop-btn.cancel {
  background: #bdbdbd;
  color: #fff;
}
.crop-btn:not(.cancel):hover {
  background: linear-gradient(90deg, #43cea2 0%, #6a85e6 100%);
}
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
}
</style>