<template>
  <div class="monitor-page">
    <!-- 引入顶部栏组件 -->
    <TopBar />
    
    <!-- 页面标题区域 -->
    <div class="page-title">
      <div class="title-content">
        <div class="title-icon">
          <Camera class="w-8 h-8" />
        </div>
        <div class="title-text">
          <h1>入站人脸监控</h1>
        </div>
      </div>
    </div>
    
    <!-- 视频区域 -->
    <div class="video-container" :class="{ 'sidebar-visible': isSidebarOpen }">
      <div class="video-wrapper">
        <div class="video-content">
          <transition name="video-fade" mode="out-in">
            <div v-if="activeSource === 'webcam'" key="webcam" class="video-frame">
              <img :src="videoSource" alt="摄像头实时画面" class="webcam-feed" />
              <div class="video-overlay">
                <div class="recording-indicator">
                  <div class="recording-dot"></div>
                  <span>实时监控</span>
                </div>
              </div>
            </div>
            
            <div v-else-if="activeSource === 'upload'" key="upload" class="video-frame">
              <img v-if="isImageUrl(videoSource)" :src="videoSource" alt="上传的图像" />
              <video v-else-if="isVideoUrl(videoSource)" :src="videoSource" controls autoplay></video>
              <div class="video-overlay">
                <div class="file-info">
                  <FileImage class="w-4 h-4" />
                  <span>已上传文件</span>
                </div>
              </div>
            </div>
            
            <div v-else-if="activeSource === 'loading'" key="loading" class="loading-state">
              <div class="loading-content">
                <div class="loading-spinner">
                  <Loader2 class="w-8 h-8 animate-spin" />
                </div>
                <p>正在处理文件，请稍候...</p>
                <div class="loading-progress">
                  <div class="progress-bar"></div>
                </div>
              </div>
            </div>
            
            <div v-else key="placeholder" class="video-placeholder">
              <div class="placeholder-content">
                <MonitorSpeaker class="w-16 h-16 text-gray-400" />
                <h3>选择视频源</h3>
                <p>请选择摄像头或上传文件开始监控</p>
              </div>
            </div>
          </transition>
        </div>
      </div>
    </div>
    
    <!-- 可滑动侧边栏控制面板 -->
    <aside 
      class="control-sidebar"
      :class="{ 'sidebar-open': isSidebarOpen }"
    >
      <div class="sidebar-header">
        <div class="header-content">
          <Settings class="w-5 h-5" />
          <h2>控制面板</h2>
        </div>
        <div class="header-actions">
          <button @click="toggleSidebar" class="close-btn">
            <X class="w-4 h-4" />
          </button>
        </div>
      </div>
      
      <div class="sidebar-content">
        <!-- 视频源控制 -->
        <div class="control-section">
          <div class="section-header">
            <PlayCircle class="w-4 h-4" />
            <h3>视频源控制</h3>
          </div>
          <div class="button-group">
            <button 
              @click="connectWebcam" 
              :class="{ active: activeSource === 'webcam' }"
              class="control-btn"
            >
              <Video class="w-4 h-4" />
              <span>摄像头</span>
            </button>
            <button 
              @click="uploadVideoFile" 
              :disabled="activeSource === 'webcam'"
              class="control-btn"
            >
              <Upload class="w-4 h-4" />
              <span>上传文件</span>
            </button>
          </div>
        </div>
        
        <!-- 告警信息 -->
        <div class="control-section">
          <div class="section-header">
            <AlertTriangle class="w-4 h-4" />
            <h3>告警信息</h3>
            <div v-if="newAlertCount > 0" class="alert-badge">
              {{ newAlertCount }}
            </div>
          </div>
          <div class="alerts-container" :class="{ 'has-alerts': alerts.length > 0 }">
            <transition-group name="alert-list" tag="div" class="alert-list">
              <div
                v-for="(alert, index) in alerts"
                :key="`alert-${index}-${alert.timestamp}`"
                class="alert-item"
                :class="{ 'alert-new': alert.isNew }"
                @click="markAsRead(alert, index)"
              >
                <div class="alert-header">
                  <AlertCircle class="w-3 h-3" />
                  <span class="alert-time">{{ formatTime(alert.timestamp) }}</span>
                </div>
                <p class="alert-message">{{ alert.message }}</p>
              </div>
            </transition-group>
            <div v-if="alerts.length === 0" class="empty-state">
              <Shield class="w-8 h-8 text-gray-400" />
              <p>当前无告警信息</p>
            </div>
          </div>
        </div>
        
        <!-- 人员管理 -->
        <div class="control-section">
          <div class="section-header">
            <Users class="w-4 h-4" />
            <h3>人员管理</h3>
            <div class="user-count">{{ registeredUsers.length }}</div>
          </div>
          <button @click="registerFace" class="add-user-btn">
            <UserPlus class="w-4 h-4" />
            <span>添加人员</span>
          </button>
          <div class="user-list-container">
            <transition-group name="user-list" tag="ul" class="user-list">
              <li 
                v-for="user in registeredUsers" 
                :key="user"
                class="user-item"
              >
                <div class="user-info">
                  <User class="w-4 h-4" />
                  <span>{{ user }}</span>
                </div>
                <button @click="deleteFace(user)" class="delete-btn">
                  <Trash2 class="w-4 h-4" />
                </button>
              </li>
            </transition-group>
            <div v-if="registeredUsers.length === 0" class="empty-state">
              <UserX class="w-8 h-8 text-gray-400" />
              <p>未注册任何人员</p>
            </div>
          </div>
        </div>
      </div>
    </aside>
    
    <!-- 可拖动悬浮按钮 -->
    <div 
      class="floating-control"
      :style="floatingButtonStyle"
      @mousedown="startDrag"
      @touchstart="startDrag"
    >
      <button
        class="sidebar-toggle-btn"
        @click.stop="toggleSidebar"
        :class="{ 'sidebar-open': isSidebarOpen }"
      >
        <transition name="icon-rotate" mode="out-in">
          <ChevronLeft v-if="isSidebarOpen" key="close" class="w-5 h-5" />
          <Settings v-else key="open" class="w-5 h-5" />
        </transition>
      </button>
    </div>
    
    <!-- 告警通知 -->
    <transition name="notification">
      <div v-if="showNotification" class="alert-notification">
        <div class="notification-content">
          <AlertTriangle class="w-5 h-5 text-orange-500" />
          <div class="notification-text">
            <p class="notification-title">新告警</p>
            <p class="notification-message">{{ latestAlert }}</p>
          </div>
        </div>
        <button @click="hideNotification" class="notification-close">
          <X class="w-4 h-4" />
        </button>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { useRoute } from 'vue-router'
import { ref, onMounted, onUnmounted, computed, reactive } from 'vue'
import TopBar from '../components/TopBar.vue'

// 导入图标
import { 
  Camera, Video, Upload, Square, Settings, ChevronLeft, X, 
  PlayCircle, AlertTriangle, AlertCircle, Shield, Users, 
  UserPlus, User, UserX, Trash2, FileImage, MonitorSpeaker,
  Loader2
} from 'lucide-vue-next'

// 路由和状态变量
const route = useRoute()
const windowWidth = ref(window.innerWidth)
const isSidebarOpen = ref(windowWidth.value >= 992)

// 悬浮按钮相关
const floatingButton = reactive({
  x: 24,
  y: 120,
  isDragging: false,
  offsetX: 0,
  offsetY: 0
})

// API端点设置
const SERVER_ROOT_URL = 'http://localhost:5000'
const API_BASE_URL = `${SERVER_ROOT_URL}/api`
const VIDEO_FEED_URL = `${API_BASE_URL}/video_feed`

// 状态变量
const videoSource = ref('')
const activeSource = ref('')
const alerts = ref([])
const registeredUsers = ref([])
const pollingIntervalId = ref(null)
const videoTaskId = ref('')
const newAlertCount = ref(0)

// 通知相关
const showNotification = ref(false)
const latestAlert = ref('')

// 计算属性
const statusIndicatorClass = computed(() => ({
  active: activeSource.value === 'webcam'
}))

const statusText = computed(() => {
  return activeSource.value === 'webcam' ? '实时监控中' : '监控已停止'
})

const floatingButtonStyle = computed(() => ({
  left: `${floatingButton.x}px`,
  top: `${floatingButton.y}px`,
  cursor: floatingButton.isDragging ? 'grabbing' : 'grab'
}))

// 格式化时间
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  return date.toLocaleTimeString()
}

// 标记告警为已读
const markAsRead = (alert, index) => {
  if (alert.isNew) {
    alerts.value[index].isNew = false
    newAlertCount.value--
  }
}

// API调用封装
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
    throw error;
  }
};

// 人脸管理方法
const loadRegisteredUsers = async () => {
  try {
    const data = await apiFetch('/faces/');
    registeredUsers.value = data.names;
  } catch (error) {}
};

const registerFace = () => {
  const name = prompt("请输入要注册人员的姓名:");
  if (name) {
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
    loadRegisteredUsers();
  } catch (error) {}
};

const deleteFace = async (name) => {
  if (confirm(`确定要删除人员 '${name}' 吗?`)) {
    try {
      const data = await apiFetch(`/faces/${name}`, { method: 'DELETE' });
      alert(data.message);
      loadRegisteredUsers();
    } catch (error) {}
  }
};

// 视频控制方法
const connectWebcam = () => {
  stopPolling();
  videoSource.value = `${VIDEO_FEED_URL}?t=${new Date().getTime()}`;
  activeSource.value = 'webcam';
  startAlertPolling();
};

const disconnectWebcam = async () => {
  try {
    await apiFetch('/stop_video_feed', { method: 'POST' });
    videoSource.value = '';
    activeSource.value = '';
    stopAlertPolling();
  } catch (error) {
    console.error('关闭摄像头失败:', error);
    alert('关闭摄像头失败。');
  }
};

const uploadVideoFile = () => {
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'video/mp4,image/jpeg,image/jpg';
  input.onchange = handleFileUpload;
  input.click();
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  stopPolling();
  videoSource.value = '';
  activeSource.value = 'loading';
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const response = await fetch(`${API_BASE_URL}/upload`, {
      method: 'POST',
      body: formData
    });
    
    if (response.status === 202) {
      const data = await response.json();
      videoTaskId.value = data.task_id;
      startPolling(data.task_id);
    } else if (response.ok) {
      const data = await response.json();
      videoSource.value = `${SERVER_ROOT_URL}${data.file_url}?t=${new Date().getTime()}`;
      activeSource.value = 'upload';
      
      alerts.value = (data.alerts || []).map(alert => ({
        message: alert,
        timestamp: new Date(),
        isNew: true
      }));
      newAlertCount.value = alerts.value.length;
      stopAlertPolling();
    } else {
      const errorData = await response.json();
      throw new Error(errorData.message || '文件上传失败');
    }
  } catch (error) {
    activeSource.value = '';
    alert(error.message || '操作失败');
  }
};

// 轮询相关方法
const startPolling = (taskId) => {
  pollingIntervalId.value = setInterval(() => {
    pollTaskStatus(taskId);
  }, 2000);
};

const stopPolling = () => {
  if (pollingIntervalId.value) {
    clearInterval(pollingIntervalId.value);
    pollingIntervalId.value = null;
    videoTaskId.value = '';
  }
};

const pollTaskStatus = async (taskId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/video/task_status/${taskId}`);
          if (response.status === 200) {
        stopPolling();
        const data = await response.json();
        videoSource.value = `${SERVER_ROOT_URL}${data.file_url}`;
        activeSource.value = 'upload';
        alerts.value = (data.alerts || []).map(alert => ({
          message: alert,
          timestamp: new Date(),
          isNew: true
        }));
        newAlertCount.value = alerts.value.length;
      } else if (response.status === 202) {
        console.log('视频处理中...');
      } else {
        stopPolling();
        const errorData = await response.json();
        throw new Error(errorData.message || '视频处理失败');
      }
    } catch (error) {
      stopPolling();
      activeSource.value = '';
      alert(error.message);
    }
  };
  
  // 告警轮询
  let alertPollingInterval = null;
  
  const startAlertPolling = () => {
    if (alertPollingInterval) clearInterval(alertPollingInterval);
    
    alertPollingInterval = setInterval(async () => {
      try {
        const response = await fetch(`${API_BASE_URL}/alerts`);
        const data = await response.json();
        
        if (data.alerts && data.alerts.length) {
          const newAlerts = data.alerts
            .filter(alert => !alerts.value.some(a => a.message === alert))
            .map(alert => ({
              message: alert,
              timestamp: new Date(),
              isNew: true
            }));
          
          if (newAlerts.length) {
            alerts.value = [...alerts.value, ...newAlerts];
            newAlertCount.value += newAlerts.length;
            
            // 显示通知
            if (windowWidth.value < 768 && !isSidebarOpen.value) {
              showAlertNotification(newAlerts[0].message);
            }
          }
        }
      } catch (error) {
        console.error('获取告警失败:', error);
        stopAlertPolling();
      }
    }, 2000);
  };
  
  const stopAlertPolling = () => {
    if (alertPollingInterval) {
      clearInterval(alertPollingInterval);
      alertPollingInterval = null;
    }
  };
  
  // 通知相关方法
  const showAlertNotification = (message) => {
    latestAlert.value = message;
    showNotification.value = true;
    
    setTimeout(() => {
      hideNotification();
    }, 5000);
  };
  
  const hideNotification = () => {
    showNotification.value = false;
  };
  
  // 模式设置
  const forceFaceOnlyMode = async () => {
    try {
      await apiFetch('/detection_mode', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ mode: 'face_only' })
      });
    } catch (error) {
      console.error('设置人脸识别模式失败:', error);
    }
  };
  
  // 侧边栏控制
  const toggleSidebar = () => {
    isSidebarOpen.value = !isSidebarOpen.value;
  };
  
  // 悬浮按钮拖动控制
  const startDrag = (e) => {
    e.preventDefault();
    
    const touchEvent = e.touches?.[0] || e;
    const rect = e.currentTarget.getBoundingClientRect();
    
    floatingButton.isDragging = true;
    floatingButton.offsetX = touchEvent.clientX - rect.left;
    floatingButton.offsetY = touchEvent.clientY - rect.top;
    
    document.addEventListener('mousemove', handleDrag);
    document.addEventListener('mouseup', stopDrag);
    document.addEventListener('touchmove', handleDrag, { passive: false });
    document.addEventListener('touchend', stopDrag);
  };
  
  const handleDrag = (e) => {
    if (!floatingButton.isDragging) return;
    
    const touchEvent = e.touches?.[0] || e;
    
    // 计算新位置，确保按钮不会移出可视区域
    let newX = touchEvent.clientX - floatingButton.offsetX;
    let newY = touchEvent.clientY - floatingButton.offsetY;
    
    // 边界检查
    const buttonWidth = 48; // 按钮宽度
    const buttonHeight = 48; // 按钮高度
    const maxX = window.innerWidth - buttonWidth;
    const maxY = window.innerHeight - buttonHeight;
    
    newX = Math.max(0, Math.min(newX, maxX));
    newY = Math.max(0, Math.min(newY, maxY));
    
    floatingButton.x = newX;
    floatingButton.y = newY;
  };
  
  const stopDrag = () => {
    floatingButton.isDragging = false;
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', stopDrag);
    document.removeEventListener('touchmove', handleDrag);
    document.removeEventListener('touchend', stopDrag);
  };
  
  // 窗口大小响应
  const handleResize = () => {
    const newWidth = window.innerWidth;
    windowWidth.value = newWidth;
    
    if (newWidth >= 992 && !isSidebarOpen.value) {
      isSidebarOpen.value = true;
    }
  };
  
  // 生命周期
  onMounted(() => {
    window.addEventListener('resize', handleResize);
    handleResize();
    
    loadRegisteredUsers();
    forceFaceOnlyMode();
  });
  
  onUnmounted(() => {
    window.removeEventListener('resize', handleResize);
    if (alertPollingInterval) clearInterval(alertPollingInterval);
    stopPolling();
    document.removeEventListener('mousemove', handleDrag);
    document.removeEventListener('mouseup', stopDrag);
    document.removeEventListener('touchmove', handleDrag);
    document.removeEventListener('touchend', stopDrag);
  });
  
  // 辅助方法
  const isImageUrl = (url) => {
    const lowerUrl = url.toLowerCase();
    return lowerUrl.includes('.jpg') || lowerUrl.includes('.jpeg') || lowerUrl.includes('.png');
  };
  
  const isVideoUrl = (url) => {
    return url.toLowerCase().includes('.mp4') || url.toLowerCase().includes('.webm');
  };
</script>

<style scoped>
/* 全局样式重置与基础设置 */
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
  font-family: 'Inter', 'Segoe UI', Roboto, sans-serif;
}

/* 页面标题样式 */
.page-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  margin-bottom: 24px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
}

.title-content {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  gap: 16px;
}

.title-icon {
  padding: 12px;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 12px;
  backdrop-filter: blur(10px);
}

.page-title h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.title-actions {
  display: flex;
  gap: 16px;
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  transition: all 0.3s ease;
}

.status-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  animation: pulse 2s infinite;
}

.status-indicator.active .status-dot {
  background: #22c55e;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

/* 视频容器样式 */
.video-container {
  position: relative;
  width: 100%;
  height: calc(100vh - 320px);
  padding: 24px;
  background: white;
  border-radius: 16px;
  box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
  transition: all 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* 侧边栏打开时调整视频区域 */
.video-container.sidebar-visible {
  width: calc(100% - 400px);
  transition: width 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

@media (max-width: 1200px) {
  .video-container.sidebar-visible {
    width: calc(100% - 360px);
  }
}

@media (max-width: 992px) {
  .video-container.sidebar-visible {
    width: calc(100% - 340px);
  }
}

@media (max-width: 768px) {
  .video-container.sidebar-visible {
    width: 100%;
  }
}

.video-wrapper {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.video-content {
  flex: 1;
  position: relative;
  border-radius: 12px;
  overflow: hidden;
  background: #000;
}

.video-frame {
  width: 100%;
  height: 100%;
  position: relative;
}

.webcam-feed,
.video-frame img,
.video-frame video {
  width: 100%;
  height: 100%;
  object-fit: contain;
  background: #000;
}

.video-overlay {
  position: absolute;
  top: 16px;
  left: 16px;
  z-index: 10;
}

.recording-indicator {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(239, 68, 68, 0.9);
  color: white;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(10px);
}

.recording-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: white;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: rgba(34, 197, 94, 0.9);
  color: white;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 500;
  backdrop-filter: blur(10px);
}

/* 加载状态 */
.loading-state {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  height: 100%;
  color: #6b7280;
  gap: 20px;
}

.loading-content {
  text-align: center;
}

.loading-spinner {
  margin-bottom: 16px;
  color: #667eea;
}

.loading-progress {
  width: 200px;
  height: 4px;
  background: #e5e7eb;
  border-radius: 2px;
  overflow: hidden;
  margin-top: 16px;
}

.progress-bar {
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, #667eea, #764ba2);
  animation: progress 2s ease-in-out infinite;
}

@keyframes progress {
  0% { transform: translateX(-100%); }
  100% { transform: translateX(100%); }
}

/* 占位符状态 */
.video-placeholder {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
}

.placeholder-content {
  text-align: center;
  color: #64748b;
}

.placeholder-content h3 {
  margin: 16px 0 8px;
  font-size: 20px;
  font-weight: 600;
}

.placeholder-content p {
  font-size: 14px;
  opacity: 0.8;
}

/* 视频淡入淡出动画 */
.video-fade-enter-active,
.video-fade-leave-active {
  transition: all 0.5s ease;
}

.video-fade-enter-from,
.video-fade-leave-to {
  opacity: 0;
  transform: scale(0.95);
}

/* 快捷操作按钮 */
.action-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  white-space: nowrap;
  font-weight: 500;
  font-size: 14px;
  position: relative;
  overflow: hidden;
}

.action-btn::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.action-btn:hover::before {
  left: 100%;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.action-btn:active {
  transform: translateY(0);
}

.action-btn.primary {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.action-btn.secondary {
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(16, 185, 129, 0.3);
}

.action-btn.danger {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3);
}

.action-btn.active {
  box-shadow: 0 0 0 2px rgba(255, 255, 255, 0.5), 0 4px 15px rgba(59, 130, 246, 0.4);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

/* 侧边栏样式 */
.control-sidebar {
  position: fixed;
  top: 60px;
  right: 0;
  height: calc(100vh - 60px);
  width: 400px;
  background: white;
  box-shadow: -4px 0 30px rgba(0, 0, 0, 0.1);
  transform: translateX(100%);
  transition: transform 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 70;
  overflow: hidden;
  border-left: 1px solid #e5e7eb;
}

.control-sidebar.sidebar-open {
  transform: translateX(0);
}

.sidebar-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px;
  background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
  border-bottom: 1px solid #e5e7eb;
}

.header-content {
  display: flex;
  align-items: center;
  gap: 12px;
}

.header-content h2 {
  margin: 0;
  color: #1f2937;
  font-size: 20px;
  font-weight: 600;
}

.close-btn {
  padding: 8px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  color: #6b7280;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.sidebar-content {
  height: calc(100% - 80px);
  overflow-y: auto;
  padding: 24px;
  scrollbar-width: thin;
  scrollbar-color: #d1d5db #f9fafb;
}

.sidebar-content::-webkit-scrollbar {
  width: 6px;
}

.sidebar-content::-webkit-scrollbar-track {
  background: #f9fafb;
}

.sidebar-content::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 3px;
}

/* 控制面板区域 */
.control-section {
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 1px solid #f3f4f6;
}

.control-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 16px;
  position: relative;
}

.section-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
  flex: 1;
}

.alert-badge,
.user-count {
  background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
  color: white;
  font-size: 12px;
  font-weight: 600;
  padding: 4px 8px;
  border-radius: 10px;
  min-width: 20px;
  text-align: center;
}

.user-count {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
}

.button-group {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 16px;
}

.control-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 16px;
  border: 2px solid #e5e7eb;
  border-radius: 10px;
  background: white;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 14px;
}

.control-btn:hover {
  border-color: #3b82f6;
  color: #3b82f6;
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.15);
}

.control-btn.active {
  background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%);
  color: white;
  border-color: #3b82f6;
  box-shadow: 0 4px 15px rgba(59, 130, 246, 0.3);
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
}

/* 告警容器 */
.alerts-container {
  height: 200px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #f9fafb;
  scrollbar-width: thin;
  scrollbar-color: #d1d5db #f9fafb;
}

.alerts-container::-webkit-scrollbar {
  width: 4px;
}

.alerts-container::-webkit-scrollbar-thumb {
  background: #d1d5db;
  border-radius: 2px;
}

.alert-list {
  padding: 12px;
}

.alert-item {
  padding: 12px;
  margin-bottom: 8px;
  background: white;
  border-radius: 8px;
  border-left: 3px solid #3b82f6;
  transition: all 0.3s ease;
  cursor: pointer;
}

.alert-item:hover {
  background: #f0f9ff;
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.alert-item.alert-new {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-left-color: #f59e0b;
  animation: newAlert 0.5s ease;
}

@keyframes newAlert {
  0% { transform: translateX(-10px); opacity: 0; }
  100% { transform: translateX(0); opacity: 1; }
}

.alert-header {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 4px;
}

.alert-time {
  font-size: 11px;
  color: #6b7280;
  font-weight: 500;
}

.alert-message {
  margin: 0;
  font-size: 13px;
  color: #374151;
  line-height: 1.4;
}

/* 列表动画 */
.alert-list-enter-active,
.alert-list-leave-active {
  transition: all 0.3s ease;
}

.alert-list-enter-from,
.alert-list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.alert-list-move {
  transition: transform 0.3s ease;
}

/* 用户管理 */
.add-user-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  width: 100%;
  padding: 12px 16px;
  background: linear-gradient(135deg, #10b981 0%, #059669 100%);
  color: white;
  border: none;
  border-radius: 10px;
  cursor: pointer;
  margin-bottom: 16px;
  transition: all 0.3s ease;
  font-weight: 500;
  font-size: 14px;
}

.add-user-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(16, 185, 129, 0.3);
}

.user-list-container {
  max-height: 240px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #f9fafb;
  scrollbar-width: thin;
}

.user-list {
  list-style: none;
  padding: 12px;
}

.user-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px;
  background: white;
  border-radius: 8px;
  margin-bottom: 8px;
  transition: all 0.3s ease;
}

.user-item:hover {
  background: #f0f9ff;
  transform: translateX(2px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.1);
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #374151;
  font-weight: 500;
}

.delete-btn {
  background: transparent;
  border: none;
  color: #ef4444;
  cursor: pointer;
  padding: 6px;
  border-radius: 6px;
  transition: all 0.2s ease;
}

.delete-btn:hover {
  background: #fef2f2;
  transform: scale(1.1);
}

.user-list-enter-active,
.user-list-leave-active {
  transition: all 0.3s ease;
}

.user-list-enter-from,
.user-list-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

.user-list-move {
  transition: transform 0.3s ease;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 32px 16px;
  text-align: center;
  color: #6b7280;
}

.empty-state p {
  margin: 8px 0 0;
  font-size: 14px;
}

/* 告警通知 */
.alert-notification {
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 12px;
  width: 320px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.15);
  z-index: 2000;
  backdrop-filter: blur(10px);
}

.notification-content {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  flex: 1;
}

.notification-text {
  flex: 1;
}

.notification-title {
  margin: 0 0 4px;
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.notification-message {
  margin: 0;
  font-size: 13px;
  color: #6b7280;
  line-height: 1.4;
}

.notification-close {
  background: transparent;
  border: none;
  color: #6b7280;
  cursor: pointer;
  padding: 4px;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.notification-close:hover {
  background: #f3f4f6;
  color: #374151;
}

.notification-enter-active,
.notification-leave-active {
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
}

.notification-enter-from,
.notification-leave-to {
  opacity: 0;
  transform: translateY(20px) scale(0.95);
}

/* 可拖动悬浮按钮 */
.floating-control {
  position: fixed;
  z-index: 80;
  user-select: none;
  touch-action: none;
}

.floating-control .sidebar-toggle-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  cursor: pointer;
  box-shadow: 0 4px 20px rgba(102, 126, 234, 0.4);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  backdrop-filter: blur(10px);
}

.floating-control .sidebar-toggle-btn:hover {
  transform: translateY(-2px) scale(1.05);
  box-shadow: 0 8px 30px rgba(102, 126, 234, 0.5);
}

.floating-control .sidebar-toggle-btn:active {
  transform: translateY(0) scale(0.98);
}

.floating-control .sidebar-toggle-btn.sidebar-open {
  background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
}

/* 响应式适配 */
@media (max-width: 1200px) {
  .control-sidebar {
    width: 360px;
  }
}

@media (max-width: 992px) {
  .control-sidebar {
    width: 340px;
  }
  
  .page-title {
    padding: 20px 24px;
  }
  
  .video-container {
    padding: 20px;
  }
}

@media (max-width: 768px) {
  .control-sidebar {
    width: 100%;
  }
  
  .page-title {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
    padding: 16px 20px;
  }
  
  .title-content {
    gap: 12px;
  }
  
  .page-title h1 {
    font-size: 24px;
  }
  
  .title-actions {
    gap: 12px;
  }
  
  .action-btn {
    padding: 10px 16px;
    font-size: 13px;
  }
  
  .video-container {
    height: calc(100vh - 280px);
    padding: 16px;
  }
  
  .alert-notification {
    width: calc(100% - 32px);
    max-width: 350px;
  }
}

@media (max-width: 576px) {
  .page-title h1 {
    font-size: 20px;
  }
  
  .title-actions {
    gap: 8px;
  }
  
  .action-btn {
    padding: 8px 12px;
    gap: 6px;
  }
  
  .action-btn span {
    display: none;
  }
  
  .video-container {
    height: calc(100vh - 260px);
    padding: 12px;
  }
  
  .sidebar-content {
    padding: 16px;
  }
  
  .control-section {
    margin-bottom: 24px;
  }
  
  .button-group {
    grid-template-columns: 1fr;
    gap: 8px;
  }
}
</style>