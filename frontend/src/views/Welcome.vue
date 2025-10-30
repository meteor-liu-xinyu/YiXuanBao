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
            <el-col :xs="24" :sm="24" :md="8" class="feature-col">
              <el-card class="feature-card" shadow="hover">
                <div class="card-inner">
                  <h3>个性化档案</h3>
                  <p class="card-text">上传头像、填写联系信息，一键管理你的个人资料。</p>
                </div>
              </el-card>
            </el-col>

            <el-col :xs="24" :sm="24" :md="8" class="feature-col">
              <el-card class="feature-card" shadow="hover">
                <div class="card-inner">
                  <h3>智能匹配医院</h3>
                  <p class="card-text">按地区/专科/病种筛选，快速找到合适的就医机构。</p>
                </div>
              </el-card>
            </el-col>

            <el-col :xs="24" :sm="24" :md="8" class="feature-col">
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
.site-main {
  padding: 48px 6% 80px;
  box-sizing: border-box;
}

.welcome-page { 
  min-height: 100vh; 
  background: linear-gradient(180deg,#f5f9ff 0,#eef6ff 100%); 
}

.hero { 
  text-align:center; 
  margin-bottom: 36px; 
}

.hero h2 { 
  font-size:2rem; 
  color:#114; 
  margin-bottom:8px; 
}

.lead { 
  color:#3a5572; 
  margin-bottom:18px; 
}

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

.features { 
  max-width:1200px; 
  margin:0 auto; 
  padding-top: 20px; 
}

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

.card-inner h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #1a3a52;
  text-align: center;
}

.card-text {
  margin: 0;
  color: #475c6b;
  line-height: 1.6;
  text-align: center;
  font-size: 0.95rem;
}

/* 移动端优化 */
@media (max-width: 768px) {
  .site-main {
    padding: 32px 16px 60px;
  }

  .hero h2 {
    font-size: 1.5rem;
  }

  .lead {
    font-size: 0.95rem;
    padding: 0 10px;
  }

  .hero-buttons {
    flex-direction: column;
    align-items: center;
    gap: 12px;
    padding: 0 20px;
    max-width: 100%;
  }

  .hero-buttons .el-button.cta {
    width: 100%;
    max-width: 400px;
    height: 48px;
    line-height: 48px;
    font-size: 16px;
    padding: 0 24px;
    margin: 0;
  }

  .features {
    padding-top: 30px;
  }

  .feature-row {
    flex-direction: column;
    gap: 16px;
  }

  .feature-col {
    width: 100%;
  }

  .feature-card {
    width: 100%;
    padding: 24px 20px;
  }

  .card-inner h3 {
    font-size: 1.15rem;
  }

  .card-text {
    font-size: 0.9rem;
  }
}

/* 超小屏幕优化 */
@media (max-width: 480px) {
  .site-main {
    padding: 24px 12px 50px;
  }

  .hero {
    margin-bottom: 28px;
  }

  .hero h2 {
    font-size: 1.35rem;
  }

  .hero-buttons {
    padding: 0 16px;
  }

  .hero-buttons .el-button.cta {
    max-width: 100%;
    font-size: 15px;
  }

  .feature-card {
    padding: 20px 16px;
  }
}

.site-footer { 
  text-align:center; 
  padding:18px; 
  color:#667; 
  background:transparent; 
}
</style>