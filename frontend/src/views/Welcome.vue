<template>
  <div class="welcome-page">
    <el-container>
      <el-main class="site-main">
        <div class="hero">
          <h2>智能推荐 · 精准就医</h2>
          <p class="lead">
            根据地区与病种快速推荐合适医院，支持头像上传与个人资料管理。
          </p>

          <div class="hero-buttons">
            <el-button class="cta cta--primary" size="large" type="success" @click="$router.push('/recommend')">
              立即开始
            </el-button>

            <!-- 根据登录状态显示不同按钮 -->
            <el-button
              class="cta"
              size="large"
              @click="onSecondaryClick"
            >
              {{ isLoggedIn ? '查看个人中心' : '登录/注册' }}
            </el-button>

            <!-- 仅在登录时显示历史记录按钮 -->
            <el-button
              v-if="isLoggedIn"
              class="cta"
              size="large"
              @click="onHistoryClick"
            >
              历史记录
            </el-button>
          </div>
        </div>

        <div class="features">
          <div class="feature-row">
            <el-col :span="8" class="feature-col">
              <el-card class="feature-card" shadow="hover">
                <div class="card-inner">
                  <h3>个性化档案</h3>
                  <p class="card-text">上传头像、填写联系信息，一键管理你的个人资料。</p>
                </div>
              </el-card>
            </el-col>

            <el-col :span="8" class="feature-col">
              <el-card class="feature-card" shadow="hover">
                <div class="card-inner">
                  <h3>智能匹配医院</h3>
                  <p class="card-text">按地区/专科/病种筛选，快速找到合适的就医机构。</p>
                </div>
              </el-card>
            </el-col>

            <el-col :span="8" class="feature-col">
              <el-card class="feature-card" shadow="hover">
                <div class="card-inner">
                  <h3>安全会话</h3>
                  <p class="card-text">使用 Django session 与 CSRF 保护，数据通信安全可靠。</p>
                </div>
              </el-card>
            </el-col>
          </div>
        </div>
      </el-main>

      <el-footer class="site-footer">
        <div>© {{ new Date().getFullYear() }} 医选宝 — 智能医疗推荐</div>
      </el-footer>
    </el-container>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const user = useUserStore()
const isLoggedIn = computed(() => !!(user.username))

onMounted(async () => {
  if (typeof user.fetchUser === 'function') {
    try { await user.fetchUser() } catch (e) { /* ignore */ }
  }
})

function onSecondaryClick() {
  if (isLoggedIn.value) {
    router.push('/profile')
  } else {
    router.push('/login')
  }
}

function onHistoryClick() {
  router.push('/history')
}
</script>

<style scoped>
/* 保持原样式 */
.site-main {
  --center-max-width: 520px;
  padding: 48px 6% 80px;
  box-sizing: border-box;
}

.welcome-page { min-height: 100vh; background: linear-gradient(180deg,#f5f9ff 0,#eef6ff 100%); }
.hero { text-align:center; margin-bottom: 36px; }
.hero h2 { font-size:2rem; color:#114; margin-bottom:8px; }
.lead { color:#3a5572; margin-bottom:18px; }

.hero-buttons {
  display:flex;
  gap:16px;
  justify-content:center;
  margin-top:16px;
  align-items:center;
}

.hero-buttons .el-button.cta {
  height: 60px;
  line-height: 60px;
  padding: 0 32px;
  font-size: 18px;
  border-radius: 12px;
  font-weight: 700;
  box-shadow: 0 12px 30px rgba(34, 68, 120, 0.12);
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

@media (max-width: 768px) {
  .hero-buttons {
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 0 20px;
  }
  .hero-buttons .el-button.cta {
    width: 100%;
    max-width: var(--center-max-width);
    height: 48px;
    line-height: 48px;
    font-size: 16px;
  }
}

.features { max-width:1200px; margin:0 auto; padding-top: 20px; }
.feature-row {
  display: flex;
  gap: 20px;
  align-items: stretch;
}
.feature-col {
  display: flex;
  flex-direction: column;
  flex: 1 1 0;
  min-width: 0;
}
.feature-card {
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  padding: 20px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}
.card-inner {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1 1 auto;
}
.card-text {
  margin: 0;
  color: #475c6b;
  line-height: 1.6;
  text-align: center;
}

@media (max-width: 768px) {
  .feature-row {
    flex-direction: column;
    gap: 14px;
    align-items: center;
  }

  .feature-col {
    width: 100%;
    display: flex;
    justify-content: center;
  }

  .feature-card {
    width: 100%;
    max-width: var(--center-max-width);
    height: auto;
  }
}

.site-footer { text-align:center; padding:18px; color:#667; background:transparent; }
</style>