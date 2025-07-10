<template>
  <div class="app-container">
    <!-- 顶部导航栏（复用） -->
    <header class="top-bar">
      <div class="header-left">
        <h1>车站实时视频监控系统</h1>
      </div>
      <div class="header-right">
        <div class="profile-info">
          <div class="avatar">
            <img src="https://via.placeholder.com/100" alt="用户头像">
          </div>
          <div class="name-role">
            <h2>{{ nickname }}</h2>
            <p>{{ role }}</p>
          </div>
        </div>
      </div>
    </header>

    <div class="main-content">
      <!-- 左侧边栏（复用） -->
      <aside class="sidebar">
        <div class="sidebar-section">
          <h3>操作选项</h3>
          <div class="button-group">
            <button @click="goToFaceRecognitionPage" :class="{ active: $route.path === '/face' }">入站人脸</button>
            <button @click="goToMonitorPage" :class="{ active: $route.path === '/monitor' }">监控大屏</button>
            <button @click="goToAlertPage" :class="{ active: $route.path === '/alert' }">警报处置</button>
            <button @click="goToDevicePage" :class="{ active: $route.path === '/device' }">设备信息</button>
          </div>
        </div>
        
        <div class="sidebar-section">
          <h3>菜单</h3>
          <div class="button-group">
            <button @click="goToAboutPage" :class="{ active: $route.path === '/about' }">关于系统</button>
            <button @click="logout" class="logout-btn">退出登录</button>
          </div>
        </div>
      </aside>

      <!-- 主内容区域 - 入站人脸监控内容 -->
      <main class="content-area">
        <div class="monitor-page">
          <h1>入站人脸监控</h1>
          
          <div class="monitor-container">
            <div class="video-container">
              <h2>监控视图</h2>
              <div class="video-wrapper">
                <!-- 摄像头画面 (使用Canvas优化渲染) -->
                <canvas v-if="activeSource === 'webcam'" ref="videoCanvas" class="webcam-canvas"></canvas>
                
                <!-- 上传文件画面 -->
                <template v-else-if="activeSource === 'upload'">
                    <img v-if="isImageUrl(videoSource)" :src="videoSource" alt="上传的图像" />
                    <video v-else-if="isVideoUrl(videoSource)" :src="videoSource" controls autoplay></video>
                </template>

                <!-- 加载状态 -->
                <div v-else-if="activeSource === 'loading'" class="loading-state">
                  <p>正在处理文件，请稍候...</p>
                  <div class="loading-spinner"></div>
                </div>
                
                <!-- 默认占位 -->
                <div v-else class="video-placeholder">
                  <p>加载中或未连接视频源</p>
                </div>
              </div>
              <!-- 网络状态指示 -->
              <div v-if="activeSource === 'webcam'" class="network-status">
                网络状态: 
                <span :class="connectionQualityClass">{{ connectionQualityText }}</span>
                ({{ frameRate.toFixed(1) }} FPS)
              </div>
            </div>
            
            <div class="control-panel">
              <h2>控制面板</h2>
              
              <!-- 视频源选择 -->
              <div class="control-section">
                <h3>视频源</h3>
                <div class="button-group">
                  <button @click="toggleWebcam" 
                          :class="{ 'active': activeSource === 'webcam', 'stop-btn': activeSource === 'webcam' }">
                    {{ webcamButtonText }}
                  </button>
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
              
              <!-- 告警信息 -->
              <div class="control-section">
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
                <h3>人员管理</h3>
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
      </main>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'

// 路由与用户信息（复用）
const router = useRouter()
const route = useRoute()
const role = ref('管理员')
const nickname = ref('张三')

// 路由跳转方法（复用）
const goToMonitorPage = () => {
  router.push('/monitor')
}

const goToAlertPage = () => {
  router.push('/alert')
}

const goToFaceRecognitionPage = () => {
  router.push('/face');
};

const goToAboutPage = () => {
  router.push('/about')
}

const goToDevicePage = () => {
  router.push('/device');
};

const logout = () => {
  localStorage.removeItem('authToken')
  localStorage.removeItem('userInfo')
  router.replace('/')
}

// 视频监控相关逻辑
// API端点设置
const SERVER_ROOT_URL = 'http://localhost:5000'
const API_BASE_URL = `${SERVER_ROOT_URL}/api`
const VIDEO_FEED_URL = `${API_BASE_URL}/video_feed`
const WEBSOCKET_URL = `ws://${window.location.hostname}:5000/ws/video_feed`

// 状态变量
const videoSource = ref('')
const activeSource = ref('')
const alerts = ref([])
const fileInput = ref(null)
const registeredUsers = ref([])
const webcamButtonText = ref('开启摄像头')
const isWebcamActive = ref(false)
const videoCanvas = ref(null)
const connectionQualityText = ref('良好')
const connectionQualityClass = ref('quality-good')
const frameRate = ref(0)

// 视频优化相关变量
let alertPollingInterval = null
let websocket = null
let frameBuffer = [] // 帧缓冲队列
let lastFrameTime = 0
let frameCount = 0
let fpsUpdateTimer = null
let imageLoadThrottle = 300 // 动态调整的帧间隔(ms)
const MIN_THROTTLE = 100 // 最小帧间隔
const MAX_THROTTLE = 1000 // 最大帧间隔
const BUFFER_SIZE = 5 // 最大缓冲帧数

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
    throw error;
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
  } catch (error) {
    // apiFetch中已处理错误
  }
};

const deleteFace = async (name) => {
  if (confirm(`确定要删除人员 '${name}' 吗?`)) {
    try {
      const data = await apiFetch(`/faces/${name}`, { method: 'DELETE' });
      alert(data.message);
      loadRegisteredUsers();
    } catch (error) {
      // apiFetch中已处理错误
    }
  }
};

// --- 视频/图像处理 ---
const toggleWebcam = () => {
  if (isWebcamActive.value) {
    stopWebcam()
  } else {
    startWebcam()
  }
}

const startWebcam = async () => {
  activeSource.value = 'webcam';
  isWebcamActive.value = true;
  webcamButtonText.value = '关闭摄像头';
  
  // 初始化Canvas
  await nextTick();
  if (videoCanvas.value) {
    const ctx = videoCanvas.value.getContext('2d');
    ctx.clearRect(0, 0, videoCanvas.value.width, videoCanvas.value.height);
  }
  
  // 启动帧率计算
  startFpsMonitoring();
  
  // 优先尝试WebSocket连接
  if (window.WebSocket) {
    startWebSocketStream();
  } else {
    // 降级使用HTTP轮询
    startHttpStreamFallback();
  }
  
  startAlertPolling();
}

const stopWebcam = () => {
  // 停止WebSocket
  if (websocket) {
    websocket.close();
    websocket = null;
  }
  
  // 清空状态
  activeSource.value = '';
  isWebcamActive.value = false;
  webcamButtonText.value = '开启摄像头';
  frameBuffer = [];
  frameRate.value = 0;
  
  // 清除定时器
  stopAlertPolling();
  if (fpsUpdateTimer) {
    clearInterval(fpsUpdateTimer);
    fpsUpdateTimer = null;
  }
  
  // 清除Canvas
  if (videoCanvas.value) {
    const ctx = videoCanvas.value.getContext('2d');
    ctx.clearRect(0, 0, videoCanvas.value.width, videoCanvas.value.height);
  }
}

// WebSocket视频流 (优先方案)
const startWebSocketStream = () => {
  try {
    websocket = new WebSocket(WEBSOCKET_URL);
    
    websocket.onopen = () => {
      console.log('WebSocket连接已建立');
      connectionQualityText.value = '良好';
      connectionQualityClass.value = 'quality-good';
    };
    
    websocket.onmessage = (event) => {
      // 处理收到的帧数据
      if (event.data instanceof Blob) {
        const img = new Image();
        img.onload = () => {
          addFrameToBuffer(img);
        };
        img.src = URL.createObjectURL(event.data);
      }
    };
    
    websocket.onerror = (error) => {
      console.error('WebSocket错误:', error);
      connectionQualityText.value = '连接错误';
      connectionQualityClass.value = 'quality-poor';
      // 降级到HTTP方案
      if (isWebcamActive.value) {
        startHttpStreamFallback();
      }
    };
    
    websocket.onclose = () => {
      console.log('WebSocket连接已关闭');
      if (isWebcamActive.value) {
        connectionQualityText.value = '连接断开';
        connectionQualityClass.value = 'quality-poor';
        // 尝试重连
        setTimeout(() => startWebSocketStream(), 3000);
      }
    };
    
  } catch (error) {
    console.error('WebSocket初始化失败:', error);
    startHttpStreamFallback();
  }
}

// HTTP轮询 fallback方案
const startHttpStreamFallback = () => {
  console.log('使用HTTP轮询模式');
  
  const loadNextFrame = () => {
    if (!isWebcamActive.value) return;
    
    const img = new Image();
    const startTime = Date.now();
    
    img.onload = () => {
      // 计算加载时间，动态调整间隔
      const loadTime = Date.now() - startTime;
      adjustThrottleBasedOnLoadTime(loadTime);
      
      addFrameToBuffer(img);
      
      // 安排下一帧加载
      setTimeout(loadNextFrame, imageLoadThrottle);
    };
    
    img.onerror = () => {
      console.error('帧加载失败，尝试重试');
      connectionQualityText.value = '加载失败';
      connectionQualityClass.value = 'quality-poor';
      // 延长重试间隔
      setTimeout(loadNextFrame, imageLoadThrottle * 2);
    };
    
    // 添加时间戳防止缓存
    img.src = `${VIDEO_FEED_URL}?t=${Date.now()}`;
  };
  
  // 开始加载第一帧
  loadNextFrame();
}

// 添加帧到缓冲队列
const addFrameToBuffer = (img) => {
  // 限制缓冲队列大小
  if (frameBuffer.length >= BUFFER_SIZE) {
    frameBuffer.shift(); // 移除最旧的帧
  }
  frameBuffer.push(img);
  
  // 如果没有正在渲染，立即开始渲染
  if (frameBuffer.length === 1) {
    renderNextFrame();
  }
  
  // 更新连接质量
  updateConnectionQuality();
}

// 渲染缓冲队列中的下一帧
const renderNextFrame = () => {
  if (!isWebcamActive.value || !videoCanvas.value || frameBuffer.length === 0) {
    return;
  }
  
  // 使用requestAnimationFrame优化渲染时机
  requestAnimationFrame(() => {
    const img = frameBuffer.shift();
    const ctx = videoCanvas.value.getContext('2d');
    
    if (ctx && img) {
      // 调整图像大小以适应Canvas
      const canvasWidth = videoCanvas.value.clientWidth;
      const canvasHeight = videoCanvas.value.clientHeight;
      
      // 设置Canvas实际尺寸以匹配显示尺寸（解决模糊问题）
      videoCanvas.value.width = canvasWidth;
      videoCanvas.value.height = canvasHeight;
      
      // 保持宽高比绘制
      const aspectRatio = img.width / img.height;
      let drawWidth, drawHeight;
      
      if (canvasWidth / canvasHeight > aspectRatio) {
        drawHeight = canvasHeight;
        drawWidth = canvasHeight * aspectRatio;
      } else {
        drawWidth = canvasWidth;
        drawHeight = canvasWidth / aspectRatio;
      }
      
      // 居中绘制
      const x = (canvasWidth - drawWidth) / 2;
      const y = (canvasHeight - drawHeight) / 2;
      
      ctx.clearRect(0, 0, canvasWidth, canvasHeight);
      ctx.drawImage(img, x, y, drawWidth, drawHeight);
      
      // 更新帧计数
      frameCount++;
    }
    
    // 如果还有缓冲帧，继续渲染
    if (frameBuffer.length > 0) {
      renderNextFrame();
    }
  });
}

// 基于加载时间动态调整间隔
const adjustThrottleBasedOnLoadTime = (loadTime) => {
  // 如果加载时间超过当前间隔的80%，说明需要延长间隔
  if (loadTime > imageLoadThrottle * 0.8) {
    imageLoadThrottle = Math.min(imageLoadThrottle + 50, MAX_THROTTLE);
  } 
    // 如果加载时间很短，可以缩短间隔
  else if (loadTime < imageLoadThrottle * 0.3 && imageLoadThrottle > MIN_THROTTLE) {
    imageLoadThrottle = Math.max(imageLoadThrottle - 20, MIN_THROTTLE);
  }
}

// 更新连接质量显示
const updateConnectionQuality = () => {
  const fps = frameRate.value;
  
  if (fps > 15) {
    connectionQualityText.value = '优秀';
    connectionQualityClass.value = 'quality-excellent';
  } else if (fps > 10) {
    connectionQualityText.value = '良好';
    connectionQualityClass.value = 'quality-good';
  } else if (fps > 5) {
    connectionQualityText.value = '一般';
    connectionQualityClass.value = 'quality-fair';
  } else {
    connectionQualityText.value = '较差';
    connectionQualityClass.value = 'quality-poor';
  }
}

// 启动帧率监控
const startFpsMonitoring = () => {
  frameCount = 0;
  lastFrameTime = Date.now();
  
  if (fpsUpdateTimer) {
    clearInterval(fpsUpdateTimer);
  }
  
  // 每秒更新一次帧率
  fpsUpdateTimer = setInterval(() => {
    const now = Date.now();
    const elapsed = (now - lastFrameTime) / 1000; // 秒
    frameRate.value = frameCount / elapsed;
    
    // 重置计数
    frameCount = 0;
    lastFrameTime = now;
  }, 1000);
}

// 上传视频文件处理
const uploadVideoFile = () => {
  if (isWebcamActive.value) {
    stopWebcam()
  }
  fileInput.value.click();
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;
  
  activeSource.value = 'loading';
  
  const formData = new FormData();
  formData.append('file', file);
  
  try {
    const data = await apiFetch('/upload', {
      method: 'POST',
      body: formData
    });
    
    videoSource.value = `${SERVER_ROOT_URL}${data.file_url}?t=${new Date().getTime()}`;
    activeSource.value = 'upload';
    alerts.value = data.alerts || [];
    stopAlertPolling();

  } catch (error) {
    activeSource.value = '';
  }
};

// 告警轮询控制
const stopAlertPolling = () => {
  if (alertPollingInterval) {
    clearInterval(alertPollingInterval);
    alertPollingInterval = null;
  }
}

const startAlertPolling = () => {
  if (alertPollingInterval) {
    clearInterval(alertPollingInterval)
  }
  
  alertPollingInterval = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts`)
      const data = await response.json()
      alerts.value = data.alerts || []
    } catch (error) {
      console.error('Error fetching alerts:', error)
      stopAlertPolling();
    }
  }, 2000) // 每2秒轮询一次
}

// 判断URL类型
const isImageUrl = (url) => {
  const lowerUrl = url.toLowerCase();
  return lowerUrl.includes('.jpg') || lowerUrl.includes('.jpeg') || lowerUrl.includes('.png')
}

const isVideoUrl = (url) => {
  return url.toLowerCase().includes('.mp4') || url.toLowerCase().includes('.mov') || 
         url.toLowerCase().includes('.webm') || url.toLowerCase().includes('.avi')
}

// 生命周期钩子
onMounted(() => {
  loadRegisteredUsers() // 页面加载时获取已注册用户
})

onUnmounted(() => {
  stopWebcam() // 组件卸载时确保关闭摄像头
  stopAlertPolling()
})
</script>

<style scoped>
/* 复用的布局样式 */
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #121212;
  color: #e0e0e0;
}

/* 顶部导航栏样式 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  background-color: #1e1e1e;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
  position: sticky;
  top: 0;
  z-index: 100;
}

.header-left h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #e0e0e0;
}

.header-right {
  display: flex;
  align-items: center;
}

.profile-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.3);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.name-role h2 {
  margin: 0;
  font-size: 16px;
  color: #e0e0e0;
}

.name-role p {
  margin: 0;
  font-size: 12px;
  color: rgba(255, 255, 255, 0.6);
}

/* 主内容区域样式 */
.main-content {
  display: flex;
  flex: 1;
  height: calc(100vh - 60px);
}

/* 侧边栏样式 */
.sidebar {
  width: 220px;
  background-color: #1e1e1e;
  border-right: 1px solid #333;
  padding: 20px 0;
  overflow-y: auto;
}

.sidebar-section {
  margin-bottom: 30px;
  padding: 0 15px;
}

.sidebar-section h3 {
  margin: 0 0 15px 10px;
  color: #ccc;
  font-size: 16px;
  font-weight: 600;
  padding-bottom: 8px;
  border-bottom: 1px solid #333;
}

.sidebar .button-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.sidebar .button-group button {
  width: 100%;
  padding: 12px 15px;
  background-color: transparent;
  color: #ccc;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  text-align: left;
  transition: all 0.3s ease;
}

.sidebar .button-group button:hover {
  background-color: rgba(0, 123, 255, 0.2);
  color: #007bff;
}

.sidebar .button-group button.active {
  background-color: #007bff;
  color: white;
}

.logout-btn {
  margin-top: 10px;
  color: #f44336 !important;
}

.logout-btn:hover {
  background-color: rgba(244, 67, 54, 0.1) !important;
  color: #f44336 !important;
}

/* 内容区域样式 */
.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #121212;
}

/* 入站人脸页面特有样式 */
.monitor-page {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  color: #fff;
  background-color: #1a1a1a;
  border-radius: 8px;
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
  background-color: #2d2d2d;
}
.video-container h2, .control-panel h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #444;
  padding-bottom: 0.5rem;
  color: #e0e0e0;
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
  position: relative;
}

.webcam-canvas {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
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
/* 控制面板按钮组样式（与侧边栏区分） */
.control-panel .button-group {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
}
.control-panel .button-group button, .apply-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  background-color: #4CAF50;
  color: white;
  cursor: pointer;
  transition: background-color 0.3s;
}
.control-panel .button-group button:hover, .apply-button:hover {
  background-color: #45a049;
}
.control-panel .button-group button.active {
  background-color: #007BFF;
}

/* 关闭摄像头按钮样式 */
.stop-btn {
  background-color: #f44336 !important;
}
.stop-btn:hover {
  background-color: #d32f2f !important;
}

/* 网络状态指示样式 */
.network-status {
  margin-top: 1rem;
  font-size: 0.9rem;
  color: #ccc;
  padding: 0.3rem 0;
}

.quality-excellent {
  color: #4CAF50;
  font-weight: bold;
}

.quality-good {
  color: #8BC34A;
}

.quality-fair {
  color: #FFC107;
}

.quality-poor {
  color: #F44336;
  font-weight: bold;
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
  background-color: #2a2a2e;
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
  background-color: #d32f2d;
}

/* 响应式适配 */
@media (max-width: 768px) {
  .sidebar {
    width: 60px;
    padding: 20px 0;
  }

  .sidebar-section h3 {
    display: none;
  }

  .sidebar .button-group button {
    justify-content: center;
    text-align: center;
    padding: 12px 0;
    font-size: 0; /* 隐藏文字 */
    position: relative;
  }
  
  /* 可以在这里添加图标替代文字 */
  .sidebar .button-group button::after {
    content: attr(data-icon);
    font-size: 16px;
  }

  .header-left h1 {
    font-size: 16px;
  }
}
</style>