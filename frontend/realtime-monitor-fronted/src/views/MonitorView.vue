<template>
  <div class="app-container">
    <!-- 顶部导航栏 -->
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
            <h2>张三</h2>
            <p>管理员</p>
          </div>
        </div>
      </div>
    </header>

    <!-- 新增：人脸注册模态框 -->
    <div v-if="showRegistrationModal" class="registration-modal-overlay">
      <div class="registration-modal-content">
        <h2>正在为 "{{ registrationName }}" 注册人脸</h2>
        <div class="registration-video-container">
          <video ref="registrationVideoEl" autoplay playsinline class="registration-video"></video>
        </div>
        <div class="registration-status">
          <p>状态: {{ registrationStatus }}</p>
          <p>已成功捕获: {{ capturedFramesCount }} 帧</p>
        </div>
        <div class="registration-controls">
          <button @click="captureFrame" class="capture-button">捕获当前帧</button>
          <button @click="closeRegistrationModal" class="finish-button">完成注册</button>
        </div>
      </div>
    </div>

    <!-- 新增：RTMP流连接模态框 -->
    <div v-if="showRtmpConnectionModal" class="rtmp-modal-overlay">
      <div class="rtmp-modal-content">
        <h2>RTMP流连接配置</h2>
        <div class="rtmp-form">
          <div class="form-group">
            <label>流名称:</label>
            <input v-model="rtmpConfig.name" type="text" placeholder="请输入流名称" class="rtmp-input" />
          </div>
          <div class="form-group">
            <label>RTMP地址:</label>
            <input v-model="rtmpConfig.rtmp_url" type="text" placeholder="rtmp://example.com/live/stream" class="rtmp-input" />
          </div>
          <div class="form-group">
            <label>描述 (可选):</label>
            <input v-model="rtmpConfig.description" type="text" placeholder="流描述信息" class="rtmp-input" />
          </div>
          <div class="form-group">
            <label>检测模式:</label>
            <div class="detection-modes">
              <label class="checkbox-label">
                <input type="checkbox" v-model="rtmpConfig.detection_modes" value="object_detection" />
                目标检测
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="rtmpConfig.detection_modes" value="face_only" />
                人脸识别
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="rtmpConfig.detection_modes" value="fall_detection" />
                跌倒检测
              </label>
              <label class="checkbox-label">
                <input type="checkbox" v-model="rtmpConfig.detection_modes" value="smoking_detection" />
                抽烟检测
              </label>
            </div>
          </div>
        </div>
        <div class="rtmp-controls">
          <button @click="connectRtmpStream" class="connect-button" :disabled="!rtmpConfig.name || !rtmpConfig.rtmp_url">连接流</button>
          <button @click="closeRtmpModal" class="cancel-button">取消</button>
        </div>
        <div v-if="rtmpStatus" class="rtmp-status">
          <p>{{ rtmpStatus }}</p>
        </div>
      </div>
    </div>

    <div class="main-content">
      <!-- 引入复用的侧边栏组件 -->
      <Sidebar :currentPath="currentPath" />

      <!-- 主内容区域 - 实时视频监控系统内容 -->
      <main class="content-area">
        <div class="monitor-page">
          <h1>实时视频监控系统</h1>
          
          <div class="monitor-container">
            <div class="video-container">
              <h2>监控视图</h2>
              <div class="video-wrapper">

                <!-- Case 1: Webcam is active -->
                <img v-if="activeSource === 'webcam'" :src="videoSource" alt="摄像头实时画面" class="webcam-feed" />
                
                <!-- Case 2: An upload is active, so we check its type -->
                <template v-else-if="activeSource === 'upload'">
                    <img v-if="isImageUrl(videoSource)" :src="videoSource" alt="上传的图像" class="uploaded-media" />
                    <video v-else-if="isVideoUrl(videoSource)" :src="videoSource" controls autoplay class="uploaded-media"></video>
                </template>

                <!-- Case 3: Loading -->
                <div v-else-if="activeSource === 'loading'" class="loading-state">
                  <p>正在处理文件，请稍候...</p>
                  <div class="loading-spinner"></div>
                </div>
                
                <!-- Case 4: Default placeholder -->
                <div v-else class="video-placeholder">
                  <div class="placeholder-icon">📹</div>
                  <p>加载中或未连接视频源</p>
                </div>
              </div>
              
              <!-- 视频状态指示器 -->
              <div class="video-status">
                <span 
                  class="status-indicator" 
                  :class="{
                    'status-active': activeSource === 'webcam',
                    'status-upload': activeSource === 'upload',
                    'status-pending': activeSource === 'loading',
                    'status-inactive': !activeSource
                  }">
                </span>
                <span class="status-text">
                  {{ activeSource === 'webcam' ? '实时监控中' : 
                     activeSource === 'upload' ? '查看上传内容' : 
                     activeSource === 'loading' ? '处理中' : '未连接' }}
                </span>
              </div>
            </div>
            
                  <div class="control-panel">
                    <h2>控制面板</h2>
                    
                    <!-- 视频源选择 -->
      
              <div class="control-section">
                      <h3>视频源</h3>
                      <div class="button-group">
                        <button @click="connectWebcam" :class="{ active: activeSource === 'webcam' }">开启摄像头</button>
                        <button @click="disconnectWebcam" v-if="activeSource === 'webcam'" class="disconnect-button">关闭摄像头</button>
                        <button @click="uploadVideoFile" :disabled="activeSource === 'webcam'" class="upload-button">上传视频</button>
      
                  <!-- 新增RTMP流连接按钮 -->
                  <button @click="showRtmpModal" :disabled="activeSource === 'webcam'" class="rtmp-button">RTMP流连接</button>

                </div>
                          </div>
            <div class="control-panel">
              <h2>控制面板</h2>
              
              <!-- 视频源选择 -->
              <div class="control-section">
                <h3>视频源</h3>
                <div class="button-group">
                  <button @click="connectWebcam" :class="{ active: activeSource === 'webcam' }">开启摄像头</button>
                  <button @click="disconnectWebcam" v-if="activeSource === 'webcam'" class="disconnect-button">关闭摄像头</button>
                  <button @click="uploadVideoFile" :disabled="activeSource === 'webcam'" class="upload-button">上传视频</button>
                </div>
              </div>
              
              <!-- 检测模式选择 -->
              <div class="control-section">
                <h3>检测模式</h3>
                <div class="button-group mode-buttons">
                  <button 
                    @click="setDetectionMode('object_detection')" 
                    :class="{ active: detectionMode === 'object_detection' }">
                    目标检测
                  </button>
                  <button 
                    @click="setDetectionMode('face_only')" 
                    :class="{ active: detectionMode === 'face_only' }">
                    人脸识别
                  </button>
                  <button 
                    @click="setDetectionMode('fall_detection')" 
                    :class="{ active: detectionMode === 'fall_detection' }">
                    跌倒检测
                  </button>
                  <button 
                    @click="setDetectionMode('smoking_detection')" 
                    :class="{ active: detectionMode === 'smoking_detection' }">
                    抽烟检测
                  </button>
                  <button 
                    @click="setDetectionMode('violence_detection')" 
                    :class="{ active: detectionMode === 'violence_detection' }">
                    暴力检测
                  </button>
                </div>
              </div>
              
              <!-- 危险区域编辑 -->
              <div class="control-section">
                <h3>危险区域设置</h3>
                <div class="button-group">
                  <button @click="toggleEditMode" :class="{ active: editMode }">
                    {{ editMode ? '保存区域' : '编辑区域' }}
                  </button>
                  <button v-if="editMode" @click="cancelEdit" class="cancel-button">取消编辑</button>
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
              <div class="control-section alerts-section">
                <h3>告警信息
                  <span v-if="alerts.length > 0" class="alerts-badge">{{ alerts.length }}</span>
                </h3>
                <div class="alerts-container" :class="{ 'has-alerts': alerts.length > 0 }">
                  <div v-if="alerts.length > 0" class="alert-list">
                    <div v-for="(alert, index) in alerts" :key="index" class="alert-item" :class="{ 'alert-new': index === 0 && alerts.length <= 3 }">
                      <span class="alert-icon">⚠️</span>
                      <span class="alert-text">{{ alert }}</span>
                    </div>
                  </div>
                  <p v-else>当前无告警信息</p>
                </div>
              </div>

              <!-- 人员管理 -->
              <div class="control-section">
                <h3>人员管理</h3>
                <div class="button-group">
                  <button @click="registerFace" class="apply-button register-button">添加人员</button>
                </div>
                <div class="user-list-container">
                  <ul v-if="registeredUsers.length > 0">
                    <li v-for="user in registeredUsers" :key="user">
                      <span class="user-name">{{ user }}</span>
                      <button @click="deleteFace(user)" class="delete-button">
                        <i class="icon-trash">✕</i>
                      </button>
                    </li>
                  </ul>
                  <p v-else>未注册任何人员</p>
                </div>
              </div>

              <!-- 新增：活动流列表 -->
              <div v-if="activeStreams.length > 0" class="control-section">
                <h3>活动RTMP流</h3>
                <div class="stream-list">
                  <div v-for="stream in activeStreams" :key="stream.stream_id" class="stream-item">
                    <div class="stream-info">
                      <h4>{{ stream.name }}</h4>
                      <p>{{ stream.rtmp_url }}</p>
                      <span class="stream-status" :class="stream.status">{{ stream.status }}</span>
                    </div>
                    <div class="stream-controls">
                      <button @click="selectRtmpStream(stream.stream_id)" class="select-button" :class="{ active: currentRtmpStream === stream.stream_id }">选择</button>
                      <button @click="stopRtmpStream(stream.stream_id)" class="stop-button">停止</button>
                      <button @click="deleteRtmpStream(stream.stream_id)" class="delete-button">删除</button>
                    </div>
                  </div>
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
import { useRoute } from 'vue-router'
import { ref, onMounted, onUnmounted, nextTick } from 'vue' // 引入 nextTick
import io from 'socket.io-client'; // 引入 socket.io-client

// 导入侧边栏组件

// API端点设置
const SERVER_ROOT_URL = 'http://localhost:5000'
const API_BASE_URL = `${SERVER_ROOT_URL}/api`
const DLIB_API_BASE_URL = `${API_BASE_URL}/dlib`; // 新的 Dlib API 基础路径
const VIDEO_FEED_URL = `${API_BASE_URL}/video_feed`

// --- 新增：注册模态框状态 ---
const showRegistrationModal = ref(false);
const registrationStatus = ref('');
const registrationName = ref('');
const capturedFramesCount = ref(0);
const registrationVideoEl = ref(null); // video 元素的引用
const registrationSocket = ref(null); // 注册用的 WebSocket 实例
const localStream = ref(null); // 本地摄像头流
const wasWebcamActive = ref(false); // 新增：记录注册前摄像头是否开启

// --- 新增：停止媒体流的辅助函数 ---
const stopStream = (stream) => {
  if (stream && stream.getTracks) {
    stream.getTracks().forEach(track => track.stop());
  }
};

// 状态变量
const videoSource = ref('') // 视频源URL
const activeSource = ref('') // 'webcam', 'upload', 'loading', 'rtmp'
const editMode = ref(false)
const alerts = ref([])
const safetyDistance = ref(100)
const loiteringThreshold = ref(2.0)
const detectionMode = ref('object_detection') // 检测模式状态
const originalDangerZone = ref(null)
const registeredUsers = ref([]) // 已注册用户列表
const pollingIntervalId = ref(null) // 用于轮询的定时器ID
const videoTaskId = ref(''); // 保存当前视频处理任务的ID

// 路由相关
const route = useRoute()
const currentPath = ref(route.path)
const webcamImg = ref(null);

// 新增：RTMP流相关状态
const showRtmpConnectionModal = ref(false)
const rtmpConfig = ref({
  name: '',
  rtmp_url: '',
  description: '',
  detection_modes: ['object_detection']
})
const rtmpStatus = ref('')
const activeStreams = ref([])
const currentRtmpStream = ref('')
const rtmpSocket = ref(null)

// --- API 调用封装 ---
// 使用新的 DLIB_API_BASE_URL
const dlibApiFetch = async (endpoint, options = {}) => {
  try {
    const response = await fetch(`${DLIB_API_BASE_URL}${endpoint}`, options);
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({ message: response.statusText }));
      throw new Error(errorData.message || `服务器错误: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Dlib API调用失败 ${endpoint}:`, error);
    alert(`操作失败: ${error.message}`);
    throw error;
  }
};

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

// --- 检测模式管理 ---
const loadDetectionMode = async () => {
  try {
    const data = await apiFetch('/detection_mode');
    detectionMode.value = data.mode;
    console.log('Detection mode loaded:', data.mode);
  } catch (error) {
    // apiFetch中已处理错误
  }
};

const setDetectionMode = async (mode) => {
  if (detectionMode.value === mode) return; // 如果模式未变，则不执行任何操作
  try {
    const data = await apiFetch('/detection_mode', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ mode: mode })
    });
    detectionMode.value = mode; // 成功后更新前端状态
    
    // 创建一个映射来获取模式的中文名
    const modeNames = {
      'object_detection': '目标检测',
      'face_only': '纯人脸识别',
      'fall_detection': '跌倒检测',
      'smoking_detection': '抽烟检测',
      'violence_detection': '暴力检测'
    };
    alert(`检测模式已切换为: ${modeNames[mode] || mode}`);

    console.log(data.message);
  } catch (error) {
    // apiFetch中已处理错误
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

// --- 人脸管理 (已更新为 Dlib API) ---
const loadRegisteredUsers = async () => {
  try {
    const data = await dlibApiFetch('/faces'); // <--- 更新API地址
    registeredUsers.value = data.names;
  } catch (error) {
    // dlibApiFetch 中已处理错误
  }
};

const deleteFace = async (name) => {
  if (confirm(`确定要删除人员 '${name}' 吗?`)) {
    try {
      const data = await dlibApiFetch(`/faces/${name}`, { method: 'DELETE' }); // <--- 更新API地址
      alert(data.message);
      loadRegisteredUsers(); // 成功后刷新列表
    } catch (error) {
      // dlibApiFetch 中已处理错误
    }
  }
};

// --- 新的交互式注册流程 ---
const registerFace = () => {
  const name = prompt("请输入要注册人员的姓名:");
  if (name && name.trim()) {
    // 检查主摄像头是否正在运行，如果是，则先停止它
    if (activeSource.value === 'webcam') {
      wasWebcamActive.value = true;
      disconnectWebcam();
    } else {
      wasWebcamActive.value = false;
    }

    registrationName.value = name.trim();
    showRegistrationModal.value = true;
    capturedFramesCount.value = 0;
    registrationStatus.value = '准备中...';
    
    // 使用 nextTick 并增加一个短暂延时，以确保摄像头已被释放
    nextTick(() => {
      setTimeout(() => {
        startRegistrationCapture();
      }, 500); // 500ms 延迟，确保后端摄像头完全释放
    });
  }
};

const startRegistrationCapture = async () => {
    if (!registrationVideoEl.value) {
        console.error("注册视频元素尚未准备好。");
        registrationStatus.value = '错误：无法访问视频元素。';
        return;
    }

    // 1. 获取本地摄像头权限
    try {
        localStream.value = await navigator.mediaDevices.getUserMedia({ video: true, audio: false });
        registrationVideoEl.value.srcObject = localStream.value;
    } catch(err) {
        console.error("无法访问摄像头:", err);
        registrationStatus.value = '错误：无法访问摄像头。';
        alert('无法访问摄像头，请检查权限。');
        closeRegistrationModal();
        return;
    }

    // 2. 连接到 WebSocket
    registrationSocket.value = io(`${SERVER_ROOT_URL}/dlib/register`);

    registrationSocket.value.on('connect', () => {
        console.log('已连接到注册 WebSocket');
        registrationStatus.value = '连接成功，正在开始...';
        // 发送开始指令
        registrationSocket.value.emit('start_registration', { name: registrationName.value });
    });

    registrationSocket.value.on('status', (data) => {
        console.log('注册状态:', data.message);
        registrationStatus.value = data.message;
    });

    registrationSocket.value.on('capture_result', (data) => {
        if (data.status === 'success') {
            capturedFramesCount.value = data.count;
            registrationStatus.value = `成功捕获 ${data.count} 帧`;
        } else {
            registrationStatus.value = `捕获失败: ${data.message}`;
        }
    });

    registrationSocket.value.on('error', (data) => {
        console.error('注册 WebSocket 错误:', data.message);
        registrationStatus.value = `错误: ${data.message}`;
    });

    registrationSocket.value.on('disconnect', () => {
        console.log('已从注册 WebSocket断开');
        registrationStatus.value = '连接已断开。';
    });
};

const captureFrame = () => {
    if (!registrationVideoEl.value || !registrationSocket.value) return;

    const canvas = document.createElement('canvas');
    canvas.width = registrationVideoEl.value.videoWidth;
    canvas.height = registrationVideoEl.value.videoHeight;
    const context = canvas.getContext('2d');
    context.drawImage(registrationVideoEl.value, 0, 0, canvas.width, canvas.height);
    
    // 将帧数据转为 base64
    const imageData = canvas.toDataURL('image/jpeg');
    
    // 通过 WebSocket 发送
    registrationSocket.value.emit('frame_for_capture', { image: imageData });
    registrationStatus.value = '已发送捕获请求...';
};

// 在关闭模态框时停止视频流
const closeRegistrationModal = (isUnmounting = false) => {
  showRegistrationModal.value = false;
  registrationName.value = '';
  registrationStatus.value = '';
  capturedFramesCount.value = 0;

  // 停止摄像头
  if (localStream.value && localStream.value.getTracks) {
    localStream.value.getTracks().forEach(track => track.stop());
    localStream.value = null;
  }
  
  // 断开 socket 连接
  if (registrationSocket.value) {
    registrationSocket.value.disconnect();
    registrationSocket.value = null;
  }

  // 如果不是在组件卸载时调用，并且之前摄像头是开启的，则重新连接
  if (!isUnmounting && wasWebcamActive.value) {
    connectWebcam();
    wasWebcamActive.value = false;
  }
};


// --- 视频/图像处理 ---
const connectWebcam = () => {
  stopPolling(); // 如果有正在轮询的任务，先停止
  activeSource.value = 'webcam';
  nextTick(() => {
    if (webcamImg.value) {
      webcamImg.value.src = `${VIDEO_FEED_URL}?t=${new Date().getTime()}`;
    }
  });
  startAlertPolling();
};

const disconnectWebcam = async () => {
  if (activeSource.value !== 'webcam') return;

  try {
    // 向后端发送停止指令
    await fetch(`${API_BASE_URL}/stop_video_feed`, { method: 'POST' });
    console.log("已向后端发送停止摄像头指令。");
  } catch (error) {
    console.error("发送停止指令失败:", error);
  } finally {
    // 无论如何都更新前端UI
    activeSource.value = '';
    if (webcamImg.value) webcamImg.value.src = '';
    stopAlertPolling(); // 停止轮询警报
  }
};

const uploadVideoFile = () => {
  // 动态创建input元素，这是一个更可靠的方法
  const input = document.createElement('input');
  input.type = 'file';
  input.accept = 'video/mp4,image/jpeg,image/jpg';
  input.onchange = handleFileUpload;
  input.click();
};

const handleFileUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  stopPolling(); // 开始新的上传前，停止任何已有的轮询
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
      // 异步处理视频
      const data = await response.json();
      videoTaskId.value = data.task_id;
      startPolling(data.task_id);
    } else if (response.ok) {
      // 同步处理图片
      const data = await response.json();
      videoSource.value = `${SERVER_ROOT_URL}${data.file_url}?t=${new Date().getTime()}`;
      activeSource.value = 'upload';
      alerts.value = data.alerts || [];
      stopAlertPolling(); // 处理完成后停止轮询
    } else {
      // 处理其他HTTP错误
      const errorData = await response.json();
      throw new Error(errorData.message || '文件上传失败');
    }
  } catch (error) {
    activeSource.value = '';
    alert(error.message || '操作失败: Failed to fetch');
    console.error('File upload error:', error);
  }
};

const startPolling = (taskId) => {
  pollingIntervalId.value = setInterval(() => {
    pollTaskStatus(taskId);
  }, 2000); // 每2秒轮询一次
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
      // 任务完成
      stopPolling();
      const data = await response.json();
      videoSource.value = `${SERVER_ROOT_URL}${data.file_url}?t=${new Date().getTime()}`;
      activeSource.value = 'upload';
      alerts.value = data.alerts || [];
    } else if (response.status === 202) {
      // 任务仍在进行中
      console.log('Video processing...');
    } else {
      // 任务失败或出现其他错误
      stopPolling();
      const errorData = await response.json();
      throw new Error(errorData.message || '视频处理失败');
    }
  } catch (error) {
    stopPolling();
    activeSource.value = '';
    alert(error.message);
    console.error('Polling error:', error);
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

// --- RTMP流管理 ---
const showRtmpModal = () => {
  showRtmpConnectionModal.value = true
  rtmpConfig.value = {
    name: '',
    rtmp_url: '',
    description: '',
    detection_modes: ['object_detection']
  }
  rtmpStatus.value = ''
}

const closeRtmpModal = () => {
  showRtmpConnectionModal.value = false
  rtmpStatus.value = ''
}

const connectRtmpStream = async () => {
  if (!rtmpConfig.value.name || !rtmpConfig.value.rtmp_url) {
    alert('请填写流名称和RTMP地址')
    return
  }

  rtmpStatus.value = '正在连接RTMP流...'
  
  try {
    const response = await fetch(`${API_BASE_URL}/streams`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(rtmpConfig.value)
    })

    if (response.ok) {
      const data = await response.json()
      rtmpStatus.value = '流创建成功，正在启动...'
      
      // 启动流处理
      await startRtmpStream(data.stream_id)
      
      // 刷新流列表
      await loadActiveStreams()
      
      closeRtmpModal()
    } else {
      const errorData = await response.json()
      rtmpStatus.value = `连接失败: ${errorData.detail || '未知错误'}`
    }
  } catch (error) {
    rtmpStatus.value = `连接失败: ${error.message}`
    console.error('RTMP连接错误:', error)
  }
}

const startRtmpStream = async (streamId) => {
  try {
    const response = await fetch(`${API_BASE_URL}/streams/${streamId}/start`, {
      method: 'POST'
    })
    
    if (response.ok) {
      console.log('RTMP流启动成功')
    } else {
      throw new Error('启动流失败')
    }
  } catch (error) {
    console.error('启动RTMP流错误:', error)
    alert(`启动流失败: ${error.message}`)
  }
}

const loadActiveStreams = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/streams`)
    if (response.ok) {
      const data = await response.json()
      activeStreams.value = data
    }
  } catch (error) {
    console.error('加载流列表错误:', error)
  }
}

const selectRtmpStream = (streamId) => {
  currentRtmpStream.value = streamId
  // 切换到RTMP流显示
  activeSource.value = 'rtmp'
  videoSource.value = `${API_BASE_URL}/streams/${streamId}/feed?t=${new Date().getTime()}`
  
  // 开始接收该流的检测结果
  connectToRtmpSocket(streamId)
}

const connectToRtmpSocket = (streamId) => {
  if (rtmpSocket.value) {
    rtmpSocket.value.disconnect()
  }
  
  rtmpSocket.value = io(`${SERVER_ROOT_URL}/rtmp`)
  
  rtmpSocket.value.on('connect', () => {
    console.log('已连接到RTMP WebSocket')
    rtmpSocket.value.emit('join_stream', { stream_id: streamId })
  })
  
  rtmpSocket.value.on('detection_result', (data) => {
    if (data.stream_id === currentRtmpStream.value) {
      // 更新检测结果和告警
      alerts.value = data.alerts || []
    }
  })
  
  rtmpSocket.value.on('error', (error) => {
    console.error('RTMP WebSocket错误:', error)
  })
}

const stopRtmpStream = async (streamId) => {
  try {
    console.log(`正在停止流: ${streamId}`);
    const response = await fetch(`${API_BASE_URL}/streams/${streamId}/stop`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    console.log('停止流响应状态:', response.status);
    
    if (response.ok) {
      const result = await response.json();
      console.log('停止流成功:', result);
      
      if (currentRtmpStream.value === streamId) {
        activeSource.value = ''
        videoSource.value = ''
        currentRtmpStream.value = ''
        if (rtmpSocket.value) {
          rtmpSocket.value.disconnect()
          rtmpSocket.value = null
        }
      }
      await loadActiveStreams()
      alert('流停止成功!');
    } else {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP ${response.status}`);
    }
  } catch (error) {
    console.error('停止RTMP流错误:', error)
    alert(`停止流失败: ${error.message}`)
  }
}

const deleteRtmpStream = async (streamId) => {
  if (confirm('确定要删除这个RTMP流吗？')) {
    try {
      console.log(`正在删除流: ${streamId}`);
      const response = await fetch(`${API_BASE_URL}/streams/${streamId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      console.log('删除流响应状态:', response.status);
      
      if (response.ok) {
        const result = await response.json();
        console.log('删除流成功:', result);
        
        if (currentRtmpStream.value === streamId) {
          activeSource.value = ''
          videoSource.value = ''
          currentRtmpStream.value = ''
          if (rtmpSocket.value) {
            rtmpSocket.value.disconnect()
            rtmpSocket.value = null
          }
        }
        await loadActiveStreams()
        alert('流删除成功!');
      } else {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP ${response.status}`);
      }
    } catch (error) {
      console.error('删除RTMP流错误:', error)
      alert(`删除流失败: ${error.message}`)
    }
  }
}

// 生命周期钩子
onMounted(() => {
  loadConfig()
  loadRegisteredUsers() // 页面加载时获取已注册用户
  loadDetectionMode() // 新增：页面加载时获取当前检测模式
  loadActiveStreams() // 新增：加载活动流列表
})

onUnmounted(() => {
  // 清除定时器
  if (pollingIntervalId.value) {
    clearInterval(pollingIntervalId.value)
  }
  
  // 停止所有正在运行的视频流
  disconnectWebcam(); // 这个函数现在会处理摄像头关闭
  closeRegistrationModal(true); // 组件卸载时确保清理, 并告知函数不要重启摄像头
  
  // 新增：清理RTMP WebSocket连接
  if (rtmpSocket.value) {
    rtmpSocket.value.disconnect()
  }
});
</script>

<style scoped>
/* 复用的布局样式 */
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  background-color: #121212;
  color: #e0e0e0;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

/* 顶部导航栏样式 */
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 20px;
  height: 60px;
  background-color: #1e1e1e;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.3);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid #333;
}

.header-left h1 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #e0e0e0;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
}

.header-right {
  display: flex;
  align-items: center;
}

.profile-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 5px 10px;
  border-radius: 6px;
  transition: background-color 0.2s;
}

.profile-info:hover {
  background-color: #2a2a2a;
}

.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  overflow: hidden;
  border: 2px solid rgba(255, 255, 255, 0.1);
  transition: transform 0.3s, border-color 0.3s;
}

.avatar:hover {
  transform: scale(1.05);
  border-color: rgba(255, 255, 255, 0.3);
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

/* 内容区域样式 */
.content-area {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
  background-color: #121212;
}

/* 实时视频监控页面特有样式 */
.monitor-page {
  width: 100%;
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  color: #fff;
  background-color: #1a1a1a;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
  transition: transform 0.3s, box-shadow 0.3s;
}

.monitor-page:hover {
  box-shadow: 0 6px 25px rgba(0, 0, 0, 0.4);
}

.monitor-page h1 {
  text-align: center;
  margin-bottom: 2rem;
  color: #e0e0e0;
  font-weight: 500;
  position: relative;
  padding-bottom: 10px;
}

.monitor-page h1::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 120px;
  height: 3px;
  background: linear-gradient(90deg, #4CAF50, #8BC34A);
  border-radius: 3px;
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
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
  transition: transform 0.2s, box-shadow 0.2s;
}

.video-container:hover, .control-panel:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.video-container h2, .control-panel h2 {
  margin-top: 0;
  margin-bottom: 1.5rem;
  border-bottom: 1px solid #444;
  padding-bottom: 0.5rem;
  color: #e0e0e0;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 8px;
}

.video-container h2::before, .control-panel h2::before {
  content: '';
  display: inline-block;
  width: 4px;
  height: 20px;
  background-color: #4CAF50;
  border-radius: 2px;
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
  box-shadow: inset 0 0 15px rgba(0, 0, 0, 0.5);
}

.webcam-feed {
  width: 100%;
  height: 100%;
  object-fit: contain;
  display: block;
  transition: opacity 0.3s;
}

.video-wrapper img, .video-wrapper video {
  max-width: 100%;
  max-height: 100%;
  object-fit: contain;
  transition: all 0.3s ease;
}

.video-wrapper:hover img, .video-wrapper:hover video {
  filter: brightness(1.05);
}

.video-placeholder, .loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #888;
  text-align: center;
  padding: 20px;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 15px;
  color: #555;
  transition: transform 0.3s, color 0.3s;
}

.video-placeholder:hover .placeholder-icon {
  transform: scale(1.1);
  color: #666;
}

.loading-spinner {
  border: 4px solid rgba(76, 175, 80, 0.2);
  border-top: 4px solid #4CAF50;
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
  padding-bottom: 1rem;
  border-bottom: 1px dashed #444;
}

.control-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.control-section h3 {
  margin-bottom: 1rem;
  color: #ccc;
  font-size: 16px;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 6px;
}

.control-section h3::before {
  content: '•';
  color: #4CAF50;
}

/* 控制面板按钮组样式 */
.control-panel .button-group {
  display: flex;
  gap: 1rem;
  margin-bottom: 1rem;
  flex-wrap: wrap;
}

.control-panel .button-group button, .apply-button {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  background-color: #4CAF50;
  color: white;
  cursor: pointer;
  transition: all 0.2s;
  font-size: 14px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  position: relative;
  overflow: hidden;
}

.control-panel .button-group button::after, .apply-button::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  transition: 0.5s;
}

.control-panel .button-group button:hover::after, .apply-button:hover::after {
  left: 100%;
}

.control-panel .button-group button:hover, .apply-button:hover {
  background-color: #45a049;
  transform: translateY(-2px);
  box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

.control-panel .button-group button:active, .apply-button:active {
  transform: translateY(0);
  box-shadow: none;
}

.control-panel .button-group button.active {
  background-color: #007BFF;
}

.control-panel .button-group button.active:hover {
  background-color: #0069D9;
}

.control-panel .button-group button:disabled {
  background-color: #555;
  cursor: not-allowed;
  opacity: 0.7;
  transform: none;
  box-shadow: none;
}

.control-panel .button-group button:disabled:hover::after {
  left: -100%;
}

/* 关闭摄像头按钮样式 */
.disconnect-button {
  background-color: #f44336 !important;
}

.disconnect-button:hover {
  background-color: #d32f2f !important;
}

.upload-button {
  background-color: #2196F3 !important;
}

.upload-button:hover {
  background-color: #0b7dda !important;
}

.mode-buttons {
  gap: 0.5rem;
}

.mode-buttons button {
  flex: 1;
  min-width: 80px;
  justify-content: center;
}

.edit-instructions {
  font-size: 0.9rem;
  color: #aaa;
  margin-top: 1rem;
  background-color: #2a2a2e;
  padding: 0.8rem;
  border-radius: 4px;
  border-left: 3px solid #007BFF;
  transition: all 0.2s;
}

.edit-instructions:hover {
  transform: translateX(2px);
  box-shadow: 0 1px 5px rgba(0, 0, 0, 0.1);
}

.setting-row {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 0.5rem;
  padding: 0.5rem 0;
}

.setting-row label {
  flex-basis: 120px;
  color: #ddd;
  font-size: 14px;
}

.setting-row input[type="range"] {
  flex-grow: 1;
  accent-color: #4CAF50;
  height: 6px;
  border-radius: 3px;
  background: #444;
  outline: none;
  transition: all 0.2s;
}

.setting-row input[type="range"]:hover {
  accent-color: #45a049;
}

.setting-row input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #4CAF50;
  cursor: pointer;
  transition: all 0.2s;
}

.setting-row input[type="range"]::-webkit-slider-thumb:hover {
  transform: scale(1.1);
  box-shadow: 0 0 5px rgba(76, 175, 80, 0.5);
}

.setting-row span {
  min-width: 40px;
  text-align: center;
  color: #ddd;
  background-color: #3a3a3a;
  padding: 0.2rem 0.5rem;
  border-radius: 3px;
  font-size: 14px;
}

.alerts-section {
  position: relative;
}

.alerts-badge {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background-color: #f44336;
  color: white;
  font-size: 12px;
  margin-left: 5px;
  transform: translateY(-2px);
  transition: transform 0.2s;
}

.alerts-container {
  height: 150px;
  overflow-y: auto;
  border: 1px solid #444;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: #2a2a2e;
  transition: all 0.2s;
}

.alerts-container.has-alerts {
  border-color: rgba(244, 67, 54, 0.5);
}

.alert-list {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.alert-item {
  background-color: rgba(244, 67, 54, 0.1);
  padding: 0.5rem;
  border-radius: 4px;
  color: #ffcccc;
  border-left: 3px solid #f44336;
  animation: fadeIn 0.3s ease-in-out;
  display: flex;
  align-items: center;
  gap: 8px;
  transition: all 0.2s;
}

.alert-item:hover {
  background-color: rgba(244, 67, 54, 0.15);
  transform: translateX(2px);
}

.alert-new {
  animation: pulse 1.5s infinite;
}

@keyframes pulse {
  0% { box-shadow: 0 0 0 0 rgba(244, 67, 54, 0.4); }
  70% { box-shadow: 0 0 0 8px rgba(244, 67, 54, 0); }
  100% { box-shadow: 0 0 0 0 rgba(244, 67, 54, 0); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateX(-10px); }
  to { opacity: 1; transform: translateX(0); }
}

.user-list-container {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #444;
  padding: 0.5rem;
  border-radius: 4px;
  background-color: #2a2a2e;
  transition: all 0.2s;
}

.user-list-container:hover {
  border-color: #555;
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
  transition: all 0.2s;
}

.user-list-container li:last-child {
  border-bottom: none;
}

.user-list-container li:hover {
  background-color: #3a3a3a;
  transform: translateX(2px);
}

.user-name {
  display: flex;
  align-items: center;
  gap: 6px;
}

.user-name::before {
  content: '👤';
  font-size: 14px;
}

.delete-button {
  padding: 0.2rem 0.5rem;
  background-color: rgba(244, 67, 54, 0.8);
  color: white;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  transition: all 0.2s;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 24px;
  height: 24px;
  opacity: 0.7;
}

.delete-button:hover {
  background-color: #f44336;
  transform: scale(1.05);
  opacity: 1;
}

.video-status {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  padding: 6px 10px;
  background-color: rgba(0, 0, 0, 0.3);
  border-radius: 4px;
  font-size: 14px;
}

.status-indicator {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  display: inline-block;
}

.status-active {
  background-color: #4CAF50;
  animation: pulse-active 2s infinite;
}

.status-upload {
  background-color: #2196F3;
}

.status-pending {
  background-color: #FFC107;
  animation: blink 1s infinite;
}

.status-inactive {
  background-color: #666;
}

@keyframes pulse-active {
  0% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0.4); }
  70% { box-shadow: 0 0 0 6px rgba(76, 175, 80, 0); }
  100% { box-shadow: 0 0 0 0 rgba(76, 175, 80, 0); }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.cancel-button {
  background-color: #6c757d !important;
}

.cancel-button:hover {
  background-color: #5a6268 !important;
}

.register-button {
  background-color: #9C27B0 !important;
}

.register-button:hover {
  background-color: #7B1FA2 !important;
}

.uploaded-media {
  transition: all 0.3s ease;
}

.uploaded-media:hover {
  filter: brightness(1.05);
  transform: scale(1.01);
}

/* 响应式适配 */
@media (max-width: 768px) {
  .header-left h1 {
    font-size: 16px;
  }
  
  .monitor-container {
    flex-direction: column;
  }
  
  .video-wrapper {
    height: 320px;
  }
  
  .setting-row {
    flex-wrap: wrap;
  }
  
  .setting-row label {
    flex-basis: 100%;
    margin-bottom: 0.5rem;
  }
  
  .control-panel .button-group {
    gap: 0.5rem;
  }
  
  .control-panel .button-group button {
    padding: 0.4rem 0.8rem;
    font-size: 13px;
  }
  
  .status-text {
    font-size: 13px;
  }
}

/* 新增：注册模态框样式 */
.registration-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.registration-modal-content {
  background-color: #2c2c2c;
  padding: 30px;
  border-radius: 10px;
  border: 1px solid #444;
  color: #fff;
  width: 800px;
  max-width: 90%;
  text-align: center;
}

.registration-modal-content h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.8em;
  color: #4CAF50; /* 主题绿色 */
}

.registration-video-container {
  width: 100%;
  margin-bottom: 20px;
  background-color: #000;
  border-radius: 5px;
  overflow: hidden;
}

.registration-video {
  width: 100%;
  height: auto;
  display: block;
}

.registration-status {
  margin-bottom: 20px;
  font-size: 1.1em;
  background-color: #333;
  padding: 10px;
  border-radius: 5px;
}

.registration-controls {
  display: flex;
  justify-content: center;
  gap: 20px;
}

.registration-controls button {
  padding: 12px 25px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1.1em;
  transition: background-color 0.3s ease;
}

.capture-button {
  background-color: #007bff;
  color: white;
}
.capture-button:hover {
  background-color: #0056b3;
}

.finish-button {
  background-color: #4CAF50;
  color: white;
}
.finish-button:hover {
  background-color: #45a049;
}

/* 新增：RTMP模态框样式 */
.rtmp-modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.rtmp-modal-content {
  background-color: #2c2c2c;
  padding: 30px;
  border-radius: 10px;
  border: 1px solid #444;
  color: #fff;
  width: 600px;
  max-width: 90%;
}

.rtmp-modal-content h2 {
  margin-top: 0;
  margin-bottom: 20px;
  font-size: 1.8em;
  color: #FF9800;
  text-align: center;
}

.rtmp-form {
  margin-bottom: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  color: #ddd;
  font-weight: bold;
}

.rtmp-input {
  width: 100%;
  padding: 10px;
  border: 1px solid #555;
  border-radius: 5px;
  background-color: #333;
  color: #fff;
  font-size: 14px;
}

.rtmp-input:focus {
  outline: none;
  border-color: #FF9800;
}

.detection-modes {
  display: flex;
  flex-wrap: wrap;
  gap: 15px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 5px;
  color: #ddd;
  cursor: pointer;
}

.checkbox-label input[type="checkbox"] {
  accent-color: #FF9800;
}

.rtmp-controls {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-bottom: 15px;
}

.connect-button {
  background-color: #4CAF50;
  color: white;
  padding: 12px 25px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1.1em;
  transition: background-color 0.3s ease;
}

.connect-button:hover:not(:disabled) {
  background-color: #45a049;
}

.connect-button:disabled {
  background-color: #555;
  cursor: not-allowed;
}

.cancel-button {
  background-color: #f44336;
  color: white;
  padding: 12px 25px;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 1.1em;
  transition: background-color 0.3s ease;
}

.cancel-button:hover {
  background-color: #d32f2f;
}

.rtmp-status {
  text-align: center;
  padding: 10px;
  background-color: #333;
  border-radius: 5px;
  color: #ddd;
}

/* RTMP流连接按钮样式 */
.rtmp-button {
  background-color: #FF9800 !important;
}
.rtmp-button:hover {
  background-color: #F57C00 !important;
}

/* 活动流列表样式 */
.stream-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #444;
  border-radius: 5px;
  background-color: #2a2a2e;
}

.stream-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  border-bottom: 1px solid #333;
  transition: background-color 0.2s;
}

.stream-item:hover {
  background-color: #3a3a3a;
}

.stream-item:last-child {
  border-bottom: none;
}

.stream-info h4 {
  margin: 0 0 5px 0;
  color: #e0e0e0;
}

.stream-info p {
  margin: 0 0 5px 0;
  color: #aaa;
  font-size: 0.9em;
  word-break: break-all;
}

.stream-status {
  padding: 3px 8px;
  border-radius: 3px;
  font-size: 0.8em;
  font-weight: bold;
}

.stream-status.active {
  background-color: #4CAF50;
  color: white;
}

.stream-status.inactive {
  background-color: #757575;
  color: white;
}

.stream-status.error {
  background-color: #f44336;
  color: white;
}

.stream-controls {
  display: flex;
  gap: 8px;
}

.select-button, .stop-button {
  padding: 6px 12px;
  border: none;
  border-radius: 3px;
  cursor: pointer;
  font-size: 0.9em;
  transition: background-color 0.2s;
}

.select-button {
  background-color: #2196F3;
  color: white;
}

.select-button:hover {
  background-color: #1976D2;
}

.select-button.active {
  background-color: #FF9800;
}

.stop-button {
  background-color: #FF5722;
  color: white;
}

.stop-button:hover {
  background-color: #E64A19;
}

.stream-controls .delete-button {
  background-color: #dc3545;
  color: white;
}

.stream-controls .delete-button:hover {
  background-color: #c82333;
}
</style>