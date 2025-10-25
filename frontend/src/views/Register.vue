<template>
  <div class="login-container">
    <div class="login-card">
      <h2>用户注册 / Register</h2>

      <!-- 添加 @keydown.enter 来在用户按回车时先设置抑制，避免与 blur 竞争 -->
      <form @submit.prevent="onRegister" @keydown.enter="onEnterPress">
        <div style="position:relative;">
          <input
            v-model="username"
            placeholder="用户名 / Username"
            autocomplete="username"
            required
            @blur="onUsernameBlur($event)"
            @input="onUsernameInput"
          />
          <span v-if="checkingUsername" class="username-status checking">检测中...</span>
          <span v-else-if="usernameAvailable === true" class="username-status available">可用 ✓</span>
          <span v-else-if="usernameAvailable === false" class="username-status taken">已被占用 ✕</span>
        </div>

        <input v-model="password" type="password" placeholder="密码 / Password" autocomplete="new-password" required />
        <input v-model="confirm" type="password" placeholder="确认密码 / Confirm password" autocomplete="new-password" required />

        <button
          type="submit"
          :disabled="loading || usernameAvailable === false"
          @pointerdown="suppressOnPointer()"
          @mousedown="suppressOnPointer()"
          @touchstart="suppressOnPointer()"
          data-skip-blur="1"
        >
          {{ loading ? '注册中... / Registering...' : '注册 / Register' }}
        </button>

        <div v-if="error" class="error-tip">{{ error }}</div>
        <div v-if="success" class="success-tip">{{ success }}</div>
      </form>

      <div class="register-link">
        已有账号？<router-link to="/login">去登录 / Login</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import api from '@/api/api'
import { useUserStore } from '@/stores/user'

const username = ref('')
const password = ref('')
const confirm = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const router = useRouter()
const user = useUserStore()

const isSubmitting = ref(false)
const suppressUntil = ref(0) // short window to skip blur-checks

// UI state
const usernameAvailable = ref(null) // null/true/false
const checkingUsername = ref(false)

// debounce timer for blur
let blurTimer = null

// dedupe + cancel support:
// pendingChecks: username -> Promise<boolean|null>
// pendingControllers: username -> AbortController
const pendingChecks = new Map()
const pendingControllers = new Map()

// cache recent results: username -> { value: boolean, ts: number }
const availabilityCache = new Map()
const CACHE_TTL = 30 * 1000 // 30s cache, adjust as needed

function getCookie(name) {
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)')
  return m ? decodeURIComponent(m.pop()) : ''
}

async function ensureCsrf() {
  if (!getCookie('csrftoken')) {
    try {
      await api.get('/accounts/csrf/', { withCredentials: true })
    } catch (e) { /* ignore */ }
  }
}

// Cancel any pending check for a username (or all if username omitted)
function cancelPendingFor(name) {
  if (name) {
    const ctrl = pendingControllers.get(name)
    if (ctrl) {
      try { ctrl.abort() } catch (e) {}
      pendingControllers.delete(name)
    }
    pendingChecks.delete(name)
  } else {
    // cancel all
    for (const [k, ctrl] of pendingControllers.entries()) {
      try { ctrl.abort() } catch (e) {}
    }
    pendingControllers.clear()
    pendingChecks.clear()
  }
}

// Unified: returns Promise<boolean|null>
// - returns cached value if fresh
// - if an identical request is in-flight, returns that promise
// - otherwise issues one request and stores Promise in pendingChecks
function getUsernameAvailability(name) {
  name = (name || '').toString().trim()
  if (!name) return Promise.resolve(null)

  // if cached and fresh
  const cached = availabilityCache.get(name)
  if (cached && (Date.now() - cached.ts) < CACHE_TTL) {
    return Promise.resolve(cached.value)
  }

  // if there's already a pending request for this username, reuse it
  if (pendingChecks.has(name)) {
    return pendingChecks.get(name)
  }

  // create new controller & promise
  const controller = new AbortController()
  pendingControllers.set(name, controller)

  const p = (async () => {
    checkingUsername.value = true
    try {
      // axios supports signal in modern browsers/axios; fallback to no-signal if unsupported
      const res = await api.get('/accounts/check-username/', {
        params: { username: name },
        withCredentials: true,
        signal: controller.signal
      })
      const data = res && res.data ? res.data : {}
      let val = null
      if (typeof data.exists === 'boolean') val = !data.exists
      else if (typeof data.available === 'boolean') val = !!data.available
      else if (typeof data.is_taken === 'boolean') val = !data.is_taken
      else val = true // fallback assume available

      // cache result
      availabilityCache.set(name, { value: val, ts: Date.now() })
      return val
    } catch (e) {
      // if aborted, return null quietly
      if (e && (e.name === 'AbortError' || e.name === 'CanceledError')) {
        return null
      }
      // network or other error: treat as unknown
      return null
    } finally {
      checkingUsername.value = false
      pendingChecks.delete(name)
      pendingControllers.delete(name)
    }
  })()

  pendingChecks.set(name, p)
  return p
}

// Called when user types in username input
function onUsernameInput() {
  // cancel any pending/queued check for the previous value
  cancelPendingFor(username.value.trim())
  // clear cached value for this input to ensure fresh check later
  availabilityCache.delete(username.value.trim())
  // clear UI state
  usernameAvailable.value = null
  error.value = ''
}

// Debounced blur handler: schedule check after short delay
function onUsernameBlur(event) {
  // skip if suppress window active
  if (Date.now() < suppressUntil.value || isSubmitting.value) return

  // if focus moved to a submit-like element that intentionally wants skip, don't check
  let next = null
  try { next = event && event.relatedTarget ? event.relatedTarget : document.activeElement } catch (e) { next = document.activeElement }
  if (next && next !== document.body) {
    try {
      if (next.closest && next.closest('[data-skip-blur]')) return
    } catch (e) {}
  }

  const name = (username.value || '').toString().trim()
  if (!name) {
    usernameAvailable.value = null
    return
  }

  // clear previous timer + pending checks for same name (we will issue a fresh, deduped one)
  if (blurTimer) { clearTimeout(blurTimer); blurTimer = null }

  // schedule a short delay so submit event (pointerdown/keydown) can cancel it
  blurTimer = setTimeout(async () => {
    blurTimer = null
    const val = await getUsernameAvailability(name)
    // only update UI if input still has that name
    if (username.value.trim() === name && val !== null) {
      usernameAvailable.value = val
    }
  }, 250) // 200-300ms is reasonable
}

// On submit: ensure we await the same unified function (will reuse pending if exists)
// Do NOT cancel a pending check; await it so only one request happens
async function onRegister() {
  error.value = ''
  success.value = ''

  if (password.value !== confirm.value) {
    error.value = '两次密码不一致 / Passwords do not match'
    return
  }

  isSubmitting.value = true
  // short suppress window to prevent blur-triggered checks from racing
  suppressUntil.value = Date.now() + 1200

  const name = (username.value || '').toString().trim()
  if (!name) {
    error.value = '请输入用户名 / Please enter username'
    isSubmitting.value = false
    return
  }

  try {
    // If we have a cached known-false, block early
    const cached = availabilityCache.get(name)
    if (cached && cached.value === false) {
      error.value = '用户名已被占用 / Username already taken'
      return
    }

    // Await the unified availability check (will reuse pending if already in-flight)
    checkingUsername.value = true
    const avail = await getUsernameAvailability(name)
    checkingUsername.value = false

    // If known not available, block
    if (avail === false) {
      usernameAvailable.value = false
      error.value = '用户名已被占用 / Username already taken'
      return
    }
    // if avail === null (network error), we allow submission and let backend decide
    // proceed to register
    loading.value = true
    await ensureCsrf()

    let res
    if (typeof user.register === 'function') {
      res = await user.register({ username: name, password: password.value })
    } else {
      res = await api.post('/accounts/register/', { username: name, password: password.value }, { withCredentials: true })
    }

    if (res && (res.status === 200 || res.status === 201 || res.status === 204)) {
      success.value = '注册成功 / Register successful'
      usernameAvailable.value = false
      // cache final state
      availabilityCache.set(name, { value: false, ts: Date.now() })
      // restore UI after short delay
      setTimeout(() => { suppressUntil.value = 0 }, 1000)
      setTimeout(() => router.replace('/login'), 1000)
    } else {
      error.value = '注册失败，请稍后重试 / Register failed'
    }
  } catch (e) {
    error.value = e?.response?.data?.detail || '注册失败 / Register failed'
  } finally {
    loading.value = false
    isSubmitting.value = false
    checkingUsername.value = false
    // ensure blur suppression eventually cleared
    setTimeout(() => { suppressUntil.value = 0 }, 1200)
  }
}
</script>

<style scoped>
/* 与登录页样式保持一致，视觉统一 */
.login-container {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(120deg, #f5f7fa 0%, #c3cfe2 100%);
}
.login-card {
  background: #fff;
  padding: 42px 32px 32px;
  border-radius: 14px;
  box-shadow: 0 4px 32px rgba(40, 60, 120, 0.15);
  width: 420px;
  max-width: 94vw;
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 22px;
  font-size: 1.6rem;
  color: #3b4a7a;
}
.login-card input {
  display: block;
  width: 100%;
  margin-bottom: 18px;
  border: 1.5px solid #b6c2e3;
  border-radius: 7px;
  padding: 12px 14px;
  font-size: 1.08rem;
  outline: none;
  transition: border 0.2s, box-shadow 0.2s;
}
.login-card input:focus {
  border: 1.5px solid #6a85e6;
  box-shadow: 0 4px 18px rgba(106,133,230,0.08);
}

.username-status {
  position: absolute;
  right: 10px;
  top: 10px;
  font-size: 0.9rem;
  padding: 4px 8px;
  border-radius: 6px;
}
.username-status.checking { color:#666; background:#fffbea; border:1px solid #f0e6b8; }
.username-status.available { color:#155724; background:#e6f4ea; border:1px solid #c7ebd1; }
.username-status.taken { color:#7a1c1c; background:#fdecea; border:1px solid #f5c6cb; }

.login-card button {
  width: 100%;
  padding: 12px;
  background: linear-gradient(90deg, #6a85e6 0%, #43cea2 100%);
  color: #fff;
  font-size: 1.13rem;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  box-shadow: 0 6px 20px rgba(106,133,230,0.12);
  cursor: pointer;
  transition: transform 0.12s ease, opacity 0.12s ease;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}
.login-card button:active:not(:disabled) {
  transform: translateY(1px);
}
.login-card button:disabled {
  background: #cfd8ec;
  cursor: not-allowed;
  opacity: 0.9;
}
.error-tip {
  color: #d32f2f;
  text-align: center;
  margin-top: 6px;
  font-size: 0.98rem;
  letter-spacing: 0.5px;
}
.success-tip {
  color: #388e3c;
  text-align: center;
  margin-top: 6px;
  font-size: 0.98rem;
  letter-spacing: 0.5px;
}
.register-link {
  text-align: center;
  margin-top: 6px;
  color: #3b4a7a;
  font-size: 0.98rem;
}
.register-link a {
  color: #6a85e6;
  text-decoration: underline;
  margin-left: 4px;
  transition: color 0.2s;
}
.register-link a:hover {
  color: #43cea2;
}

/* 手机端微调 */
@media (max-width: 480px) {
  .login-card { width: 92vw; padding: 28px 18px; }
  .login-card button { height: 46px; font-size: 1rem; }
}
</style>