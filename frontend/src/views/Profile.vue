<template>
  <div class="page">
    <el-card style="max-width:900px;margin:20px auto;padding:20px">
      <h2>个人信息</h2>
      <div style="display:flex;align-items:center;gap:16px">
        <img :src="avatarSrc" alt="avatar" style="width:100px;height:100px;border-radius:50%;object-fit:cover;border:2px solid #6a85e6" />
        <div>
          <div style="font-weight:600">{{ user.username }}</div>
          <el-button @click="triggerFile">修改头像</el-button>
          <input ref="fileInput" type="file" accept="image/*" @change="onFileChange" style="display:none" />
        </div>
      </div>
    </el-card>

    <!-- 裁剪弹窗 -->
    <div v-if="cropVisible" class="cropper-modal">
      <div class="cropper-body">
        <img ref="cropperImg" :src="cropImageUrl" class="cropper-img" />
        <div style="margin-top:12px;text-align:center">
          <el-button type="primary" @click="confirmCrop">确定</el-button>
          <el-button @click="closeCrop">取消</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, nextTick, computed, onMounted } from 'vue'
import Cropper from 'cropperjs'
import 'cropperjs/dist/cropper.css'
import { useUserStore } from '@/stores/user'
import api from '@/api/api'
import { ElMessage } from 'element-plus'

const user = useUserStore()
onMounted(()=>user.fetchUser())

const fileInput = ref(null)
const cropper = ref(null)
const cropperImg = ref(null)
const cropVisible = ref(false)
const cropImageUrl = ref('')

const avatarSrc = computed(()=> {
  return (user.avatar || '/default-avatar.png') + '?t=' + user.avatarTimestamp
})

function triggerFile(){ fileInput.value && fileInput.value.click() }
function onFileChange(e){
  const file = e.target.files && e.target.files[0]
  if (!file) return
  cropImageUrl.value = URL.createObjectURL(file)
  cropVisible.value = true
  nextTick(()=> {
    if (cropper.value) { cropper.value.destroy(); cropper.value = null }
    cropper.value = new Cropper(cropperImg.value, {
      aspectRatio: 1,
      viewMode: 1,
      autoCropArea: 1,
      background: false
    })
  })
}
function closeCrop(){ cropVisible.value = false; if (cropper.value) { cropper.value.destroy(); cropper.value=null } cropImageUrl.value=''; if (fileInput.value) fileInput.value.value='' }

async function confirmCrop(){
  if (!cropper.value) return
  const canvas = cropper.value.getCroppedCanvas({ width: 300, height: 300, imageSmoothingQuality: 'high' })
  canvas.toBlob(async blob=>{
    if (!blob) return
    const fd = new FormData()
    fd.append('avatar', blob, 'avatar.jpg')
    try {
      const res = await api.patch('accounts/userinfo/', fd, { headers: {'Content-Type': 'multipart/form-data'} })
      const newUrl = res.data.avatar
      user.refreshAvatar(newUrl)
      ElMessage.success('头像已更新')
      closeCrop()
    } catch (e) {
      console.error(e)
      ElMessage.error('上传失败')
    }
  }, 'image/jpeg', 0.9)
}
</script>

<style scoped>
.cropper-modal { position:fixed;left:0;top:0;width:100vw;height:100vh;background:#fff;display:flex;align-items:center;justify-content:center;z-index:9999 }
.cropper-body { background:#fff;padding:16px;border-radius:8px;box-shadow:0 6px 20px rgba(0,0,0,.12); display:flex;flex-direction:column;align-items:center }
.cropper-img { max-width:360px; max-height:360px; border-radius:6px; }
</style>