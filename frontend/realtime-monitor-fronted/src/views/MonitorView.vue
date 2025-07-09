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

        <!-- 人员管理 -->
        <div class="control-section">
          <h3>人员管理 (Face Management)</h3>
          <div class="button-group">
            <button @click="registerFace" class="apply-button">添加人员</button>
          </div>
          <div class="user-list-container">
            <ul v-if="registeredUsers.length > 0">
              <li v-for="user in registeredUsers" :key="user">
                <span>{{ user }}</span>
                <button @click="deleteFace(user)" class="delete-button">删除</button>
              </li>
            </ul>
            <p v-else>未注册任何人员</p>
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
const faceFileInput = ref(null) // 用于人脸注册的文件输入
const registeredUsers = ref([]) // 已注册用户列表

// --- API 调用封装 ---
const apiFetch = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, options);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `服务器错误: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`API调用失败 ${endpoint}:`, error);
    alert(`操作失败: ${error.message}`);
    throw error; // 重新抛出错误以便调用者可以捕获
  }
};


// --- 配置管理 ---
const loadConfig = async () => {
  try {
    const data = await apiFetch('/config');
    safetyDistance.value = data.safety_distance;
    loiteringThreshold.value = data.loitering_threshold;
    console.log('Configuration loaded:', data);
  } catch (error) {
    // apiFetch中已处理错误
  }
};

const updateSettings = async () => {
  try {
    const data = await apiFetch('/update_thresholds', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        safety_distance: parseInt(safetyDistance.value),
        loitering_threshold: parseFloat(loiteringThreshold.value)
      })
    });
    alert(data.message);
  } catch (error) {
     // apiFetch中已处理错误
  }
};

// --- 人脸管理 ---
const loadRegisteredUsers = async () => {
  try {
    const data = await apiFetch('/faces/');
    registeredUsers.value = data.names;
  } catch (error) {
    // apiFetch中已处理错误
  }
};

const registerFace = () => {
  const name = prompt("请输入要注册人员的姓名:");
  if (name) {
    // 触发隐藏的文件输入框
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/jpeg,image/jpg,image/png';
    input.onchange = async (e) => {
      const file = e.target.files[0];
      if (file) {
        handleFaceUpload(file, name);
      }
    };
    input.click();
  }
};

const handleFaceUpload = async (file, name) => {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('name', name);

  try {
    const data = await apiFetch('/faces/register', {
      method: 'POST',
      body: formData,
    });
    alert(data.message);
    loadRegisteredUsers(); // 成功后刷新列表
  } catch (error) {
    // apiFetch中已处理错误
  }
};

const deleteFace = async (name) => {
  if (confirm(`确定要删除人员 '${name}' 吗?`)) {
    try {
      const data = await apiFetch(`/faces/${name}`, { method: 'DELETE' });
      alert(data.message);
      loadRegisteredUsers(); // 成功后刷新列表
    } catch (error) {
      // apiFetch中已处理错误
  }
}
};


// --- 视频/图像处理 ---
const connectWebcam = () => {
  // 添加时间戳来防止浏览器缓存
  videoSource.value = `${VIDEO_FEED_URL}?t=${new Date().getTime()}`;
  activeSource.value = 'webcam';
  startAlertPolling();
};

const uploadVideoFile = () => {
  fileInput.value.click();
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  // 显示加载状态
  videoSource.value = '';
  activeSource.value = 'loading';
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const data = await apiFetch('/upload', {
      method: 'POST',
      body: formData
    });
    
    // 使用时间戳确保视频/图像被重新加载
    videoSource.value = `${SERVER_ROOT_URL}${data.file_url}?t=${new Date().getTime()}`;
    activeSource.value = 'upload';
    
    // 加载返回的告警信息
    alerts.value = data.alerts || [];
    stopAlertPolling(); // 处理完成后停止轮询

  } catch (error) {
    // apiFetch中已处理alert，这里重置状态
    activeSource.value = '';
  }
};


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

const stopAlertPolling = () => {
  if (alertPollingInterval) {
    clearInterval(alertPollingInterval);
    alertPollingInterval = null;
  }
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
      // 如果获取告警失败（例如服务器重启），则停止轮询
      stopAlertPolling();
    }
  }, 2000) // 轮询频率调整为2秒
}

// 生命周期钩子
onMounted(() => {
  loadConfig()
  loadRegisteredUsers() // 页面加载时获取已注册用户
})

onUnmounted(() => {
  if (alertPollingInterval) {
    clearInterval(alertPollingInterval)
  }
})
</script>

<style scoped>
.monitor-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.monitor-page h1 {
  text-align: center;
  margin-bottom: 2rem;
  color: #e0e0e0;
}
.monitor-container {
  display: flex;
  gap: 2rem;
  flex-wrap: wrap;
}
.video-container, .control-panel {
  flex: 1;
  min-width: 300px;
  border-radius: 8px;
  padding: 1.5rem;
}
.video-container h2, .control-panel h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #444;
  padding-bottom: 0.5rem;
}
.video-wrapper {
  width: 100%;
  height: 480px;
  background-color: #000;
  border: 1px solid #444;
  border-radius: 4px;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.video-wrapper img, .video-wrapper video {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
}
.video-placeholder, .loading-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #888;
}

.loading-spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #3498db;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-top: 1rem;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.control-section {
  margin-bottom: 2rem;
}
.control-section h3 {
  margin-bottom: 1rem;
  color: #ccc;
}
.button-group {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}
.button-group button, .apply-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  background-color: #4CAF50;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}
.button-group button:hover, .apply-button:hover {
  background-color: #45a049;
}
.button-group button.active {
  background-color: #007BFF;
}

.edit-instructions {
  font-size: 0.9rem;
  color: #aaa;
  margin-top: 1rem;
}

.setting-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
}

.setting-row label {
  flex-basis: 120px;
}

.setting-row input[type="range"] {
  flex-grow: 1;
}

.alerts-container {
  height: 150px;
  overflow-y: auto;
  border: 1px solid #444;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: #2a2a2e;
}

.alerts-container.has-alerts {
  border-color: #f44336;
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.alert-item {
  background-color: #533;
  padding: 0.5rem;
  border-radius: 4px;
  color: #ffcccc;
}

.user-list-container {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #444;
  padding: 0.5rem;
  border-radius: 4px;
}

.user-list-container ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.user-list-container li {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0.5rem;
  border-bottom: 1px solid #333;
}

.user-list-container li:last-child {
  border-bottom: none;
}

.delete-button {
  padding: 0.2rem 0.5rem;
  background-color: #f44336;
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
}

.delete-button:hover {
  background-color: #d32f2f;
}
</style> 