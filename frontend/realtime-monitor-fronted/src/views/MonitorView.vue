<template>
  <div class="monitor-page">
    <h1>实时视频监控系统</h1>
    
    <div class="monitor-container">
      <div class="video-container">
        <h2>监控视图</h2>
        <div class="video-wrapper">
          <!-- Case 1: Webcam is active -->
          <img v-if="activeSource === 'webcam'" :src="videoSource" alt="摄像头实时画面" />
          
          <!-- Case 2: An upload is active, so we check its type -->
          <template v-else-if="activeSource === 'upload'">
              <img v-if="isImageUrl(videoSource)" :src="videoSource" alt="上传的图像" />
              <video v-else-if="isVideoUrl(videoSource)" :src="videoSource" controls autoplay></video>
          </template>

          <!-- Case 3: Loading -->
          <div v-else-if="activeSource === 'loading'" class="loading-state">
            <p>正在处理文件，请稍候...</p>
            <div class="loading-spinner"></div>
          </div>
          
          <!-- Case 4: Default placeholder -->
          <div v-else class="video-placeholder">
            <p>加载中或未连接视频源</p>
          </div>
        </div>
      </div>
      
      <div class="control-panel">
        <h2>控制面板</h2>
        
        <!-- 视频源选择 -->
        <div class="control-section">
          <h3>视频源</h3>
          <div class="button-group">
            <button @click="connectWebcam" :class="{ active: activeSource === 'webcam' }">摄像头</button>
            <button @click="uploadVideoFile" :class="{ active: activeSource === 'upload' }">上传视频</button>
          </div>
          <input 
            type="file" 
            ref="fileInput"
            accept="video/mp4,image/jpeg,image/jpg"
            style="display:none"
            @change="handleFileUpload"
          />
        </div>
        
        <!-- 危险区域编辑 -->
        <div class="control-section">
          <h3>危险区域设置</h3>
          <div class="button-group">
            <button @click="toggleEditMode" :class="{ active: editMode }">
              {{ editMode ? '保存区域' : '编辑区域' }}
            </button>
            <button v-if="editMode" @click="cancelEdit">取消编辑</button>
          </div>
          <div v-if="editMode" class="edit-instructions">
            <p>点击并拖动区域点以调整位置</p>
            <p>右键点击删除点</p>
            <p>双击添加新点</p>
          </div>
        </div>
        
        <!-- 参数设置 -->
        <div class="control-section">
          <h3>参数设置</h3>
          <div class="setting-row">
            <label>安全距离 (像素)</label>
            <input type="range" v-model="safetyDistance" min="10" max="200" step="5" />
            <span>{{ safetyDistance }}</span>
          </div>
          <div class="setting-row">
            <label>警报阈值 (秒)</label>
            <input type="range" v-model="loiteringThreshold" min="0.5" max="10" step="0.5" />
            <span>{{ loiteringThreshold }}</span>
          </div>
          <button @click="updateSettings" class="apply-button">应用设置</button>
        </div>
        
        <!-- 告警信息 -->
        <div class="alert-section">
          <h3>告警信息</h3>
          <div class="alerts-container" :class="{ 'has-alerts': alerts.length > 0 }">
            <div v-if="alerts.length > 0" class="alert-list">
              <div v-for="(alert, index) in alerts" :key="index" class="alert-item">
                {{ alert }}
              </div>
            </div>
            <p v-else>当前无告警信息</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

// API端点设置
const SERVER_ROOT_URL = 'http://localhost:5000'
const API_BASE_URL = `${SERVER_ROOT_URL}/api`
const VIDEO_FEED_URL = `${API_BASE_URL}/video_feed`

// 状态变量
const videoSource = ref('')
const activeSource = ref('')
const editMode = ref(false)
const alerts = ref([])
const safetyDistance = ref(100)
const loiteringThreshold = ref(2.0)
const originalDangerZone = ref(null)
const fileInput = ref(null)

// 加载配置
const loadConfig = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/config`)
    const data = await response.json()
    safetyDistance.value = data.safety_distance
    loiteringThreshold.value = data.loitering_threshold
    console.log('Configuration loaded:', data)
  } catch (error) {
    console.error('Error loading configuration:', error)
  }
}

// 更新设置
const updateSettings = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/update_thresholds`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        safety_distance: parseInt(safetyDistance.value),
        loitering_threshold: parseFloat(loiteringThreshold.value)
      })
    })
    const data = await response.json()
    alert(data.message)
  } catch (error) {
    console.error('Error updating settings:', error)
    alert('更新设置失败')
  }
}

// 连接摄像头流
const connectWebcam = () => {
  // 关键修复：添加时间戳来防止浏览器缓存
  videoSource.value = `${VIDEO_FEED_URL}?t=${new Date().getTime()}`
  activeSource.value = 'webcam'
  startAlertPolling()
}

// 上传视频文件
const uploadVideoFile = () => {
  fileInput.value.click()
}

// 处理文件上传
const handleFileUpload = async (event) => {
  const file = event.target.files[0]
  if (!file) return
  
  // 显示加载状态
  videoSource.value = ''
  activeSource.value = 'loading'
  
  // 检查文件类型
  const fileType = file.type
  if (!fileType.includes('video/mp4') && !fileType.includes('image/jpeg') && !fileType.includes('image/jpg')) {
    alert('只支持MP4视频或JPG图片文件')
    activeSource.value = ''
    return
  }
  
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    console.log('开始上传文件:', file.name, '类型:', file.type)
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData
    })
    
    console.log('上传响应状态:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`服务器返回错误状态 ${response.status}: ${errorText}`)
    }
    
    const data = await response.json()
    console.log('上传响应数据:', data)
    
    if (data.status === 'success') {
      console.log('文件处理成功，URL:', data.file_url)
      // 确保URL路径正确，使用服务器根URL拼接
      videoSource.value = `${SERVER_ROOT_URL}${data.file_url}`
      activeSource.value = 'upload'
      alerts.value = data.alerts || []
      
      // 如果是视频，需要不断刷新告警
      if (data.media_type === 'video') {
        startAlertPolling()
      }
    } else {
      alert(`上传失败: ${data.message || '未知错误'}`)
      activeSource.value = ''
    }
  } catch (error) {
    console.error('上传文件错误:', error)
    alert(`上传文件出错: ${error.message}`)
    activeSource.value = ''
  }
}

// 危险区域编辑模式
const toggleEditMode = async () => {
  if (!editMode.value) {
    // 进入编辑模式
    try {
      // 保存原始危险区域以便取消时恢复
      const response = await fetch(`${API_BASE_URL}/config`)
      const data = await response.json()
      originalDangerZone.value = data.danger_zone
      
      // 切换到编辑模式
      await fetch(`${API_BASE_URL}/toggle_edit_mode`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ edit_mode: true })
      })
      
      editMode.value = true
    } catch (error) {
      console.error('Error entering edit mode:', error)
      alert('无法进入编辑模式')
    }
  } else {
    // 退出编辑模式，保存更改
    try {
      // 获取更新后的危险区域
      const response = await fetch(`${API_BASE_URL}/config`)
      const data = await response.json()
      
      // 保存新的危险区域
      await fetch(`${API_BASE_URL}/update_danger_zone`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ danger_zone: data.danger_zone })
      })
      
      // 退出编辑模式
      await fetch(`${API_BASE_URL}/toggle_edit_mode`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ edit_mode: false })
      })
      
      editMode.value = false
      alert('危险区域已保存')
    } catch (error) {
      console.error('Error saving danger zone:', error)
      alert('保存危险区域失败')
    }
  }
}

// 取消编辑，恢复原始危险区域
const cancelEdit = async () => {
  if (!originalDangerZone.value) return
  
  try {
    // 恢复原始危险区域
    await fetch(`${API_BASE_URL}/update_danger_zone`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ danger_zone: originalDangerZone.value })
    })
    
    // 退出编辑模式
    await fetch(`${API_BASE_URL}/toggle_edit_mode`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({ edit_mode: false })
    })
    
    editMode.value = false
  } catch (error) {
    console.error('Error canceling edit:', error)
    alert('取消编辑失败')
  }
}

// 判断URL是否为图像
const isImageUrl = (url) => {
  const lowerUrl = url.toLowerCase();
  return lowerUrl.includes('.jpg') || lowerUrl.includes('.jpeg')
}

// 判断URL是否为视频
const isVideoUrl = (url) => {
  return url.toLowerCase().includes('.mp4')
}

// 定期轮询告警信息
let alertPollingInterval = null

const startAlertPolling = () => {
  // 先清除之前的轮询
  if (alertPollingInterval) {
    clearInterval(alertPollingInterval)
  }
  
  // 开始新的轮询
  alertPollingInterval = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts`)
      const data = await response.json()
      alerts.value = data.alerts || []
    } catch (error) {
      console.error('Error fetching alerts:', error)
    }
  }, 3000)
}

// 生命周期钩子
onMounted(() => {
  loadConfig()
})

onUnmounted(() => {
  if (alertPollingInterval) {
    clearInterval(alertPollingInterval)
  }
})
</script>

<style>
.monitor-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #2c3e50;
}

.monitor-container {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.video-container {
  flex: 2;
  min-width: 640px;
}

.control-panel {
  flex: 1;
  min-width: 300px;
}

.video-wrapper {
  width: 100%;
  height: 480px;
  background-color: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 5px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}

.video-wrapper img {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}

.video-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #999;
}

.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #555;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-top: 10px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.control-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 5px;
  border: 1px solid #eee;
}

h2 {
  margin-bottom: 15px;
  color: #2c3e50;
}

h3 {
  margin-bottom: 10px;
  color: #2c3e50;
  font-size: 16px;
}

.button-group {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

button {
  padding: 8px 12px;
  background-color: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

button:hover {
  background-color: #45a049;
}

button.active {
  background-color: #2196F3;
}

.setting-row {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
  gap: 10px;
}

.setting-row label {
  flex: 1;
}

.setting-row input {
  flex: 2;
}

.setting-row span {
  flex: 0 0 40px;
  text-align: right;
}

.apply-button {
  width: 100%;
  margin-top: 10px;
}

.alert-section {
  margin-top: 30px;
}

.alerts-container {
  max-height: 200px;
  overflow-y: auto;
  padding: 10px;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.has-alerts {
  border-color: #f44336;
}

.alert-item {
  padding: 8px;
  margin-bottom: 5px;
  border-radius: 3px;
  background-color: #ffebee;
  border-left: 3px solid #f44336;
  font-size: 14px;
}

.edit-instructions {
  margin-top: 10px;
  padding: 8px;
  background-color: #fff3cd;
  border-left: 3px solid #ffc107;
  font-size: 12px;
}

.edit-instructions p {
  margin: 5px 0;
}
</style> 