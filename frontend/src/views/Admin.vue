<template>
  <div class="admin-page">
    <h1>管理员面板 — 用户管理</h1>

    <div class="admin-controls">
      <input v-model="q" placeholder="搜索用户名 / 邮箱 / 姓名" @keyup.enter="search" />
      <button @click="search">搜索</button>
      <button @click="openCreate">新建用户</button>
      <button @click="exitAdmin" class="plain">退出管理员</button>
    </div>

    <div v-if="loading" class="loading">加载中...</div>

    <table v-if="!loading" class="admin-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>用户名</th>
          <th>邮箱</th>
          <th>昵称</th>
          <th>姓名</th>
          <th>性别</th>
          <th>电话</th>
          <th>生日</th>
          <th>地区/专科</th>
          <th>角色</th>
          <th>状态</th>
          <th>注册时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="u in users" :key="u.id">
          <td>{{ u.id }}</td>
          <td>{{ u.username }}</td>
          <td>{{ u.email }}</td>
          <td>{{ u.nickname || '-' }}</td>
          <td>{{ (u.first_name || '') + ' ' + (u.last_name || '') }}</td>
          <td>{{ u.gender || '-' }}</td>
          <td>{{ u.phone || '-' }}</td>
          <td>{{ u.birthday ? (u.birthday.indexOf('T') !== -1 ? u.birthday.split('T')[0] : u.birthday) : '-' }}</td>
          <td>{{ (u.preferred_region||'-') + ' / ' + (u.preferred_specialty||'-') }}</td>
          <td><span v-if="u.is_staff">管理员</span><span v-else>用户</span></td>
          <td><span v-if="u.is_active">启用</span><span v-else>已禁用</span></td>
          <td>{{ formatDate(u.date_joined) }}</td>
          <td class="actions">
            <button @click="openEdit(u)">编辑</button>
            <button @click="toggleActive(u)">{{ u.is_active ? '停用' : '启用' }}</button>
            <button @click="removeUser(u)" class="danger">删除</button>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="pagination" v-if="pageCount > 1">
      <button :disabled="page<=1" @click="changePage(page-1)">上一页</button>
      <span>第 {{ page }} 页 / 共 {{ pageCount }} 页</span>
      <button :disabled="page>=pageCount" @click="changePage(page+1)">下一页</button>
    </div>

    <!-- 编辑/新建模态 -->
    <div v-if="modalVisible" class="modal">
      <div class="modal-body">
        <h3>{{ editingUser?.id ? '编辑用户' : '新建用户' }}</h3>

        <label>用户名（只读）</label>
        <input v-model="form.username" :readonly="!!editingUser?.id" />

        <label>密码（新建或修改密码）</label>
        <input v-model="form.password" type="password" placeholder="留空则不修改密码" />

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

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '@/api/api'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const store = useUserStore()

const users = ref([])
const loading = ref(false)
const page = ref(1)
const pageCount = ref(1)
const q = ref('')
const pageSize = ref(20)

const modalVisible = ref(false)
const editingUser = ref(null)
const avatarFile = ref(null)
const avatarInput = ref(null)
const saving = ref(false)

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

async function fetchUsers() {
  loading.value = true
  try {
    const res = await api.get('/accounts/admin/users/', {
      params: { page: page.value, page_size: pageSize.value, search: q.value },
      withCredentials: true
    })
    const data = res.data
    if (data.results) {
      users.value = data.results
      pageCount.value = Math.ceil((data.count || users.value.length) / pageSize.value)
    } else {
      users.value = data.results || data
      pageCount.value = Math.ceil((data.count || (users.value && users.value.length) || 0) / pageSize.value)
    }
  } catch (e) {
    console.error('fetchUsers error', e)
    if (e?.response?.status === 403) {
      router.replace('/welcome')
    }
  } finally {
    loading.value = false
  }
}

function changePage(p) { page.value = p; fetchUsers() }
function search() { page.value = 1; fetchUsers() }

function openEdit(u) {
  editingUser.value = u
  // 填充表单（拆分 birthday）
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
  saving.value = true
  try {
    const csrftoken = (document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)') || [])[2] || ''
    // 构造 payload
    const payloadObj = {
      nickname: form.value.nickname || null,
      email: form.value.email || null,
      first_name: form.value.first_name || null,
      last_name: form.value.last_name || null,
      real_name: form.value.real_name || null,
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
      // 使用 FormData 发送（multipart/form-data）
      const formData = new FormData()
      // append JSON fields
      Object.keys(payloadObj).forEach(k => {
        // FormData 不接受 undefined，明确传 null -> '' 或 'null'，这里使用 '' 表示清空
        const v = payloadObj[k] === null ? '' : payloadObj[k]
        if (v !== undefined) formData.append(k, v)
      })
      formData.append('avatar', avatarFile.value)
      if (!editingUser.value) {
        // create
        await api.post('/accounts/admin/users/', formData, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
      } else {
        await api.patch(`/accounts/admin/users/${editingUser.value.id}/`, formData, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
      }
    } else {
      // 以 JSON 发送。注意：若想表示删除 avatar，请在 payloadObj.avatar = null 并后端处理
      if (!editingUser.value) {
        payloadObj.username = form.value.username
        await api.post('/accounts/admin/users/', payloadObj, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
      } else {
        await api.patch(`/accounts/admin/users/${editingUser.value.id}/`, payloadObj, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
      }
    }

    await fetchUsers()
    closeModal()
  } catch (e) {
    console.error('saveUser error', e)
    const body = e?.response?.data
    alert('保存失败：' + (body ? JSON.stringify(body) : '请检查输入或重试'))
  } finally {
    saving.value = false
  }
}

async function toggleActive(u) {
  const csrftoken = (document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)') || [])[2] || ''
  try {
    await api.patch(`/accounts/admin/users/${u.id}/`, { is_active: !u.is_active }, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
    await fetchUsers()
  } catch (e) {
    console.error(e)
    alert('操作失败')
  }
}

async function removeUser(u) {
  if (!confirm(`确认删除用户 ${u.username} ? 该操作不可恢复`)) return
  const csrftoken = (document.cookie.match('(^|;)\\s*csrftoken\\s*=\\s*([^;]+)') || [])[2] || ''
  try {
    await api.delete(`/accounts/admin/users/${u.id}/`, { withCredentials: true, headers: { 'X-CSRFToken': csrftoken } })
    await fetchUsers()
  } catch (e) {
    console.error(e)
    alert('删除失败')
  }
}

function exitAdmin() {
  // 退出管理员页面，直接跳转到 welcome
  router.replace('/welcome')
}

onMounted(async () => {
  // 权限判断由路由守卫处理，这里再做一次保护
  if (!store.isAuthenticated) {
    const hasSessionCookie = document.cookie.includes('sessionid=')
    if (hasSessionCookie) await store.fetchUser()
  }
  if (!store.isAuthenticated || !store.isAdmin) {
    router.replace('/welcome')
    return
  }
  fetchUsers()
})
</script>

<style scoped>
.admin-page { padding: 24px; }
.admin-controls { display:flex; gap:8px; margin-bottom:12px; align-items:center; }
.admin-controls .plain { background: transparent; color: #6a85e6; border: 1px solid rgba(106,133,230,0.14); padding:6px 10px; border-radius:6px; cursor:pointer; }
.admin-table { width:100%; border-collapse: collapse; margin-top:8px; }
.admin-table th, .admin-table td { border: 1px solid #eee; padding:8px; text-align:left; font-size:0.95rem }
.actions button { margin-right:6px; }
.modal { position:fixed; left:0; top:0; right:0; bottom:0; display:flex; align-items:center; justify-content:center; background: rgba(0,0,0,0.45); z-index:9999; }
.modal-body { background:#fff; padding:20px; border-radius:8px; width:720px; max-width:94vw; display:flex; flex-direction:column; gap:8px; max-height:90vh; overflow:auto }
.modal-actions { display:flex; gap:8px; justify-content:flex-end; margin-top:12px; }
.danger { color:#fff; background:#d32f2f; border:none; padding:6px 10px; border-radius:6px; }
.loading { padding:20px; color:#666; }
input[type="file"] { padding:6px 0; }
</style>