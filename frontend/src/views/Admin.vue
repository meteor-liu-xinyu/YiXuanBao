<template>
  <div class="admin-page">
    <h1>管理员面板 — 用户管理</h1>

    <!-- 页面级提示栏 -->
    <div v-if="message.visible" :class="['message', message.type]" role="status">
      {{ message.text }}
      <button class="close" @click="hideMessage">×</button>
    </div>

    <div class="admin-controls">
      <select v-model="searchField">
        <option value="username">用户名</option>
        <option value="email">邮箱</option>
        <option value="real_name">姓名</option>
        <option value="nickname">昵称</option>
      </select>

      <input v-model="q" placeholder="搜索用户（按上方字段）" @keyup.enter="searchAdmins" />
      <button @click="searchAdmins">搜索用户</button>
      <button @click="clearSearch" v-if="searching">清除搜索</button>
      <button @click="openCreate">新建用户</button>
      <button @click="exitAdmin" class="plain">退出管理员</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <!-- 搜索结果区域 -->
    <section v-if="!loading && (searchResults.length > 0 || searching)" class="section">
      <h2>搜索结果（共 {{ searchResults.length }}）</h2>
      <div v-if="searchResults.length === 0" class="loading">没有匹配的用户</div>
      <table v-if="searchResults.length > 0" class="admin-table">
        <thead>
          <tr>
            <th>ID</th><th>用户名</th><th>邮箱</th><th>姓名</th><th>注册时间</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in searchResults" :key="'search-'+u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.email || '-' }}</td>
            <td>{{ (u.first_name || '') + ' ' + (u.last_name || '') }}</td>
            <td>{{ formatDate(u.date_joined) }}</td>
            <td>
              <button @click="openEdit(u)">编辑</button>
              <button class="danger" @click="confirmDelete(u)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 管理员列表 -->
    <section v-if="!loading" class="section">
      <h2>管理员账户（共 {{ admins.length }}）</h2>
      <table class="admin-table">
        <thead>
          <tr>
            <th>ID</th><th>用户名</th><th>邮箱</th><th>姓名</th><th>注册时间</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in admins" :key="'admin-'+u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.email || '-' }}</td>
            <td>{{ (u.first_name || '') + ' ' + (u.last_name || '') }}</td>
            <td>{{ formatDate(u.date_joined) }}</td>
            <td>
              <button @click="openEdit(u)">编辑</button>
              <button class="danger" @click="confirmDelete(u)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 最近登录用户 -->
    <section v-if="!loading" class="section" style="margin-top:20px;">
      <h2>最近登录用户（最近 20 条）</h2>
      <table class="admin-table">
        <thead>
          <tr>
            <th>ID</th><th>用户名</th><th>邮箱</th><th>最后登录</th><th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="u in recent" :key="'recent-'+u.id">
            <td>{{ u.id }}</td>
            <td>{{ u.username }}</td>
            <td>{{ u.email || '-' }}</td>
            <td>{{ formatDate(u.last_login) }}</td>
            <td>
              <button @click="openEdit(u)">编辑</button>
              <button class="danger" @click="confirmDelete(u)">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <!-- 编辑/新建模态 -->
    <div v-if="modalVisible" class="modal">
      <div class="modal-body">
        <h3>{{ editingUser?.id ? '编辑用户' : '新建用户' }}</h3>

        <label>用户名（新建时必填，编辑只读）</label>
        <input v-model="form.username" :readonly="!!editingUser?.id" />

        <label>密码（新建时必填；编辑时留空不修改）</label>
        <input v-model="form.password" type="password" placeholder="新建请填写，编辑留空不修改" />

        <label>昵称</label>
        <input v-model="form.nickname" />

        <label>邮箱</label>
        <input v-model="form.email" />

        <label>名字</label>
        <input v-model="form.first_name" placeholder="First name" />
        <label>姓氏</label>
        <input v-model="form.last_name" placeholder="Last name" />

        <label>真实姓名（写入 first_name）</label>
        <input v-model="form.real_name" placeholder="整段姓名写入 first_name" />

        <label>性别</label>
        <select v-model="form.gender">
          <option value="">未填写</option>
          <option value="male">男</option>
          <option value="female">女</option>
          <option value="other">其他</option>
        </select>

        <label>电话</label>
        <input v-model="form.phone" />

        <label>生日</label>
        <div style="display:flex;gap:8px;align-items:center;">
          <input v-model="form.birthday_year" placeholder="年" maxlength="4" style="width:90px" @blur="normalizeYearInput" />
          <select v-model="form.birthday_month">
            <option value="">月</option>
            <option v-for="m in 12" :key="m" :value="String(m).padStart(2,'0')">{{ String(m).padStart(2,'0') }}</option>
          </select>
          <input v-model="form.birthday_day" placeholder="日" maxlength="2" style="width:60px" />
          <button @click="clearBirthday">清空</button>
        </div>

        <label>地址</label>
        <input v-model="form.address" />

        <label>偏好地区</label>
        <input v-model="form.preferred_region" placeholder="例如：北京" />

        <label>偏好专科</label>
        <input v-model="form.preferred_specialty" placeholder="例如：心内科" />

        <label>头像（上传新头像或留空不改）</label>
        <input type="file" ref="avatarInput" @change="onAvatarSelect" accept="image/*" />

        <label>是否管理员</label>
        <input type="checkbox" v-model="form.is_staff" />

        <label>是否激活</label>
        <input type="checkbox" v-model="form.is_active" />

        <div class="modal-actions">
          <button @click="saveUser" :disabled="saving">{{ saving ? '保存中...' : '保存' }}</button>
          <button @click="closeModal">取消</button>
        </div>
      </div>
    </div>

    <!-- 删除确认模态（替代 browser confirm） -->
    <div v-if="deleteModal.visible" class="modal">
      <div class="modal-body">
        <h3>确认删除</h3>
        <p>确认删除用户 <strong>{{ deleteModal.target?.username }}</strong> ? 该操作不可恢复。</p>
        <div class="modal-actions">
          <button class="danger" @click="removeUserConfirmed" :disabled="saving">{{ saving ? '删除中...' : '确认删除' }}</button>
          <button @click="closeDeleteModal">取消</button>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/api'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

const admins = ref([])
const recent = ref([])
const searchResults = ref([])
const loading = ref(false)
const q = ref('')
const searchField = ref('username')
const searching = ref(false)

const modalVisible = ref(false)
const editingUser = ref(null)
const avatarFile = ref(null)
const avatarInput = ref(null)
const saving = ref(false)

// message state for in-page notifications
const message = ref({ visible: false, text: '', type: 'info', timeoutId: null })

// delete modal state
const deleteModal = ref({ visible: false, target: null })

const form = ref({
  username: '',
  password: '',
  nickname: '',
  email: '',
  first_name: '',
  last_name: '',
  real_name: '',
  gender: '',
  phone: '',
  birthday_year: '',
  birthday_month: '',
  birthday_day: '',
  address: '',
  preferred_region: '',
  preferred_specialty: '',
  is_staff: false,
  is_active: true
})

function showMessage(text, type = 'info', duration = 4000) {
  if (message.value.timeoutId) clearTimeout(message.value.timeoutId)
  message.value.text = text
  message.value.type = type
  message.value.visible = true
  message.value.timeoutId = setTimeout(() => {
    message.value.visible = false
    message.value.timeoutId = null
  }, duration)
}

function hideMessage() {
  if (message.value.timeoutId) clearTimeout(message.value.timeoutId)
  message.value.visible = false
  message.value.timeoutId = null
}

function confirmDelete(u) {
  deleteModal.value.target = u
  deleteModal.value.visible = true
}

function closeDeleteModal() {
  deleteModal.value.visible = false
  deleteModal.value.target = null
}

function formatDate(dt) {
  if (!dt) return ''
  if (typeof dt === 'string' && dt.indexOf('T') !== -1) {
    return dt.split('T')[0] + ' ' + dt.split('T')[1]?.slice(0,8)
  }
  return String(dt)
}

function normalizeYearInput() {
  let y = String(form.value.birthday_year || '').trim()
  if (!y) { form.value.birthday_year = ''; return }
  y = y.replace(/[^\d]/g, '')
  if (y.length === 2) {
    const n = parseInt(y,10)
    form.value.birthday_year = (n >= 70 ? 1900 + n : 2000 + n).toString()
  } else {
    form.value.birthday_year = y.slice(0,4)
  }
}

function buildBirthdayFromForm() {
  const y = (form.value.birthday_year||'').trim()
  const m = (form.value.birthday_month||'').trim()
  const d = (form.value.birthday_day||'').trim()
  if (!y || !m || !d) return null
  const mm = m.padStart(2,'0'), dd = d.padStart(2,'0')
  return `${String(y).padStart(4,'0')}-${mm}-${dd}`
}

function clearBirthday() {
  form.value.birthday_year = ''
  form.value.birthday_month = ''
  form.value.birthday_day = ''
}

async function fetchOverview() {
  loading.value = true
  try {
    const res = await api.get('/accounts/admin/overview/', { withCredentials: true })
    admins.value = res.data.admins || []
    recent.value = res.data.recent_logins || []
  } catch (e) {
    console.error('fetchOverview error', e)
    if (e?.response?.status === 403) {
      router.replace('/welcome')
    } else {
      showMessage('加载管理员概览失败', 'error')
    }
  } finally {
    loading.value = false
  }
}

async function searchAdmins() {
  const term = (q.value || '').toString().trim()
  if (!term) {
    searchResults.value = []
    searching.value = false
    return fetchOverview()
  }

  loading.value = true
  searching.value = true
  try {
    const res = await api.get('/accounts/admin/users/', {
      params: { q: term, field: searchField.value },
      withCredentials: true
    })
    searchResults.value = Array.isArray(res.data) ? res.data : (res.data.results || [])
  } catch (e) {
    console.error('searchAdmins error', e)
    searchResults.value = []
    showMessage('搜索失败，请检查后端或网络', 'error')
  } finally {
    loading.value = false
  }
}

function clearSearch() {
  q.value = ''
  searchResults.value = []
  searching.value = false
  fetchOverview()
}

function openEdit(u) {
  editingUser.value = u
  let by='', bm='', bd=''
  if (u.birthday) {
    const d = u.birthday.indexOf('T') !== -1 ? u.birthday.split('T')[0] : u.birthday
    const parts = d.split('-')
    if (parts.length === 3) { by = parts[0]; bm = parts[1]; bd = parts[2] }
  }
  form.value = {
    username: u.username || '',
    password: '',
    nickname: u.nickname || '',
    email: u.email || '',
    first_name: u.first_name || '',
    last_name: u.last_name || '',
    real_name: ((u.first_name || '') + ' ' + (u.last_name || '')).trim(),
    gender: u.gender || '',
    phone: u.phone || '',
    birthday_year: by,
    birthday_month: bm,
    birthday_day: bd,
    address: u.address || '',
    preferred_region: u.preferred_region || '',
    preferred_specialty: u.preferred_specialty || '',
    is_staff: !!u.is_staff,
    is_active: !!u.is_active
  }
  avatarFile.value = null
  if (avatarInput.value) avatarInput.value.value = ''
  modalVisible.value = true
}

function openCreate() {
  editingUser.value = null
  avatarFile.value = null
  form.value = {
    username: '',
    password: '',
    nickname: '',
    email: '',
    first_name: '',
    last_name: '',
    real_name: '',
    gender: '',
    phone: '',
    birthday_year: '',
    birthday_month: '',
    birthday_day: '',
    address: '',
    preferred_region: '',
    preferred_specialty: '',
    is_staff: false,
    is_active: true
  }
  if (avatarInput.value) avatarInput.value.value = ''
  modalVisible.value = true
}

function closeModal() {
  modalVisible.value = false
  editingUser.value = null
}

function onAvatarSelect(e) {
  const f = e.target.files[0]
  if (!f) return
  avatarFile.value = f
}

async function saveUser() {
  // front-end required check for creation
  if (!editingUser.value) {
    if (!form.value.username || !String(form.value.username).trim()) {
      showMessage('新建用户需要填写用户名', 'error')
      return
    }
    if (!form.value.password || !String(form.value.password).trim()) {
      showMessage('新建用户需要填写密码', 'error')
      return
    }
  }

  saving.value = true
  try {
    const csrftoken = (document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)') || [])[2] || ''

    // Keep empty string '' if user cleared the field; null means "not provided"
    const rawRealName = (form.value.real_name == null) ? null : String(form.value.real_name)
    const firstNameToSend = (form.value.real_name != null)
      ? (String(form.value.real_name).trim())  // can be '' intentionally to clear
      : (form.value.first_name || null)

    const payloadObj = {
      nickname: form.value.nickname || null,
      email: form.value.email || null,
      first_name: firstNameToSend,
      last_name: form.value.last_name || null,
      real_name: rawRealName,
      gender: form.value.gender || null,
      phone: form.value.phone || null,
      birthday: buildBirthdayFromForm(),
      address: form.value.address || null,
      preferred_region: form.value.preferred_region || null,
      preferred_specialty: form.value.preferred_specialty || null,
      is_staff: form.value.is_staff,
      is_active: form.value.is_active
    }
    if (form.value.password) payloadObj.password = form.value.password

    if (avatarFile.value) {
      const formData = new FormData()
      Object.keys(payloadObj).forEach(k => {
        const v = payloadObj[k] === undefined ? '' : (payloadObj[k] === null ? '' : payloadObj[k])
        formData.append(k, v)
      })
      formData.append('avatar', avatarFile.value)
      if (!editingUser.value) {
        await api.post('/accounts/admin/users/', formData, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
      } else {
        await api.patch(`/accounts/admin/users/${editingUser.value.id}/`, formData, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
      }
    } else {
      if (!editingUser.value) {
        payloadObj.username = form.value.username
        await api.post('/accounts/admin/users/', payloadObj, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
      } else {
        await api.patch(`/accounts/admin/users/${editingUser.value.id}/`, payloadObj, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
      }
    }

    showMessage('保存成功', 'success')
    // 更新界面并关闭模态
    await fetchOverview()
    if (searching.value && q.value) {
      await searchAdmins()
    }
    closeModal()
  } catch (e) {
    console.error('saveUser error', e)
    const body = e?.response?.data
    showMessage('保存失败：' + (body ? JSON.stringify(body) : '请检查输入或重试'), 'error')
  } finally {
    saving.value = false
  }
}

async function removeUserConfirmed() {
  const u = deleteModal.value.target
  if (!u) return
  const csrftoken = (document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)') || [])[2] || ''
  saving.value = true
  try {
    await api.delete(`/accounts/admin/users/${u.id}/`, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })

    // 本地立即移除
    admins.value = admins.value.filter(x => x.id !== u.id)
    recent.value = recent.value.filter(x => x.id !== u.id)
    searchResults.value = searchResults.value.filter(x => x.id !== u.id)

    showMessage('删除成功', 'success')
    closeDeleteModal()

    // 同步刷新一次后端数据
    await fetchOverview()
    if (searching.value && q.value) {
      await searchAdmins()
    }
  } catch (e) {
    console.error(e)
    showMessage('删除失败', 'error')
  } finally {
    saving.value = false
  }
}

function exitAdmin() {
  router.replace('/welcome')
}

onMounted(async () => {
  if (!store.isAuthenticated) {
    const hasSessionCookie = document.cookie.includes('sessionid=')
    if (hasSessionCookie) await store.fetchUser()
  }
  if (!store.isAuthenticated || !store.isAdmin) {
    router.replace('/welcome')
    return
  }
  fetchOverview()
})
</script>

<style scoped>
.admin-page { padding: 24px; }
.admin-controls { display:flex; gap:8px; margin-bottom:12px; align-items:center; }
.admin-controls .plain { background: transparent; color: #6a85e6; border: 1px solid rgba(106,133,230,0.14); padding:6px 10px; border-radius:6px; cursor:pointer; }
.section { margin-bottom: 18px; }
.admin-table { width:100%; border-collapse: collapse; margin-top:8px; }
.admin-table th, .admin-table td { border: 1px solid #eee; padding:8px; text-align:left; font-size:0.95rem }
.modal { position:fixed; left:0; top:0; right:0; bottom:0; display:flex; align-items:center; justify-content:center; background: rgba(0,0,0,0.45); z-index:9999; }
.modal-body { background:#fff; padding:20px; border-radius:8px; width:720px; max-width:94vw; display:flex; flex-direction:column; gap:8px; max-height:90vh; overflow:auto }
.modal-actions { display:flex; gap:8px; justify-content:flex-end; margin-top:12px; }
.danger { color:#fff; background:#d32f2f; border:none; padding:6px 10px; border-radius:6px; cursor:pointer; }
.loading { padding:20px; color:#666; }
input[type="file"] { padding:6px 0; }

/* message styles */
.message { padding:10px 14px; border-radius:6px; margin-bottom:12px; display:flex; justify-content:space-between; align-items:center; }
.message.info { background:#e8f0ff; color:#0f3c9a; border:1px solid #cfe0ff }
.message.success { background:#e9f6ee; color:#0a6b2d; border:1px solid #cfeed8 }
.message.error { background:#fdecea; color:#8a1f1f; border:1px solid #f6c6c6 }
.message .close { background:transparent; border:none; font-size:18px; cursor:pointer; }
</style>