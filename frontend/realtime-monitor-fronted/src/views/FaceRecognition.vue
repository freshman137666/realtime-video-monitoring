<template>
  <div class="monitor-page">
    <h1>入站人脸识别</h1>
    
    <div class="monitor-container">
      <!-- 左侧摄像头实时画面区域 -->
      <div class="video-container">
        <h2>实时摄像头画面</h2>
        <div class="video-wrapper">
          <video 
            ref="videoElement" 
            autoplay 
            muted 
            playsinline
            class="camera-feed"
          ></video>
          <div v-if="!isCameraActive" class="video-placeholder"></div>
        </div>
        <div class="button-group" style="margin-top: 15px;">
          <button @click="toggleCamera" :class="{ active: isCameraActive }">
            {{ isCameraActive ? '关闭摄像头' : '启动摄像头' }}
          </button>
          <button @click="captureImage">抓拍人脸</button>
        </div>
      </div>

      <!-- 右侧识别结果区域 -->
      <div class="control-panel">
        <h2>识别结果</h2>
        <div class="control-section">
          <div v-if="recognitionResult" class="result-details">
            <div class="result-item">
              <span class="label">姓名：</span>
              <span class="value">{{ recognitionResult.name }}</span>
            </div>
            <div class="result-item">
              <span class="label">身份证号：</span>
              <span class="value">{{ recognitionResult.idCard }}</span>
            </div>
            <div class="result-item">
              <span class="label">性别：</span>
              <span class="value">{{ recognitionResult.gender }}</span>
            </div>
            <div class="result-item">
              <span class="label">年龄：</span>
              <span class="value">{{ recognitionResult.age }}岁</span>
            </div>
            <div class="result-item">
              <span class="label">识别时间：</span>
              <span class="value">{{ recognitionResult.timestamp }}</span>
            </div>
            <div class="result-item">
              <span class="label">匹配度：</span>
              <span class="value">{{ recognitionResult.matchRate }}%</span>
            </div>
            <div class="result-item status">
              <span class="label">状态：</span>
              <span class="value" :class="recognitionResult.status === '正常' ? 'normal' : 'alert'">
                {{ recognitionResult.status }}
              </span>
            </div>
          </div>
          <div v-else class="result-placeholder">
            <p>未检测到人脸，请对准摄像头</p>
          </div>
        </div>

        <div class="control-section">
          <h3>操作记录</h3>
          <div class="history-list">
            <div v-for="(record, index) in operationHistory" :key="index" class="history-item">
              <span class="time">{{ record.time }}</span>
              <span class="action">{{ record.action }}</span>
            </div>
            <div v-if="operationHistory.length === 0" class="empty-history">
              <p>暂无操作记录</p>
            </div>
          </div>
        </div>

        <div class="control-section">
          <div class="button-group vertical">
            <button @click="goBack">返回首页</button>
            <button @click="clearRecords">清空记录</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, nextTick } from 'vue';
import { useRouter } from 'vue-router';

// 状态变量
const videoElement = ref<HTMLVideoElement | null>(null);
const isCameraActive = ref(false);
const recognitionResult = ref<any>(null);
const operationHistory = ref<any[]>([]);
const router = useRouter();

// 模拟识别结果数据
const mockRecognitionResult = () => ({
  name: '张三',
  idCard: '110101********1234',
  gender: '男',
  age: 32,
  timestamp: new Date().toLocaleString(),
  matchRate: 98.7,
  status: '正常'
});

// 启动/关闭摄像头
const toggleCamera = async () => {
  if (isCameraActive.value) {
    // 关闭摄像头
    if (videoElement.value?.srcObject) {
      (videoElement.value.srcObject as MediaStream).getTracks().forEach(track => track.stop());
    }
    isCameraActive.value = false;
    addOperationRecord('关闭摄像头');
  } else {
    // 启动摄像头
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ 
        video: { width: 1280, height: 720 },
        audio: false 
      });
      await nextTick();
      if (videoElement.value) {
        videoElement.value.srcObject = stream;
        isCameraActive.value = true;
        addOperationRecord('启动摄像头');
      }
    } catch (error) {
      console.error('摄像头访问失败:', error);
      alert('无法访问摄像头，请检查设备权限');
    }
  }
};

// 抓拍人脸并识别
const captureImage = () => {
  if (!isCameraActive.value) {
    alert('请先启动摄像头');
    return;
  }
  
  // 模拟人脸识别过程
  addOperationRecord('开始人脸抓拍识别');
  
  // 模拟识别延迟
  setTimeout(() => {
    recognitionResult.value = mockRecognitionResult();
    addOperationRecord(`识别成功：${recognitionResult.value.name}`);
  }, 1500);
};

// 添加操作记录
const addOperationRecord = (action: string) => {
  operationHistory.value.unshift({
    time: new Date().toLocaleTimeString(),
    action
  });
  
  // 限制记录数量
  if (operationHistory.value.length > 10) {
    operationHistory.value.pop();
  }
};

// 清空记录
const clearRecords = () => {
  operationHistory.value = [];
  recognitionResult.value = null;
  addOperationRecord('清空所有记录');
};

// 返回首页
const goBack = () => {
  // 关闭摄像头再返回
  if (isCameraActive.value) {
    (videoElement.value?.srcObject as MediaStream)?.getTracks().forEach(track => track.stop());
  }
  router.push('/home');
};

// 组件卸载时关闭摄像头
onUnmounted(() => {
  if (isCameraActive.value) {
    (videoElement.value?.srcObject as MediaStream)?.getTracks().forEach(track => track.stop());
  }
});
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

h2 {
  margin-bottom: 15px;
  color: #2c3e50;
}

h3 {
  margin-bottom: 10px;
  color: #2c3e50;
  font-size: 16px;
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

.camera-feed {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* 按钮样式 */
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

/* 控制区域样式 */
.control-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 5px;
  border: 1px solid #eee;
}

/* 识别结果样式 */
.result-details {
  padding: 10px 0;
}

.result-item {
  display: flex;
  padding: 8px 0;
  border-bottom: 1px solid #eee;
}

.result-item:last-child {
  border-bottom: none;
}

.label {
  flex: 0 0 100px;
  font-weight: 500;
  color: #555;
}

.value {
  flex: 1;
  word-break: break-all;
}

.status .value.normal {
  color: #4CAF50;
  font-weight: 500;
}

.status .value.alert {
  color: #f44336;
  font-weight: 500;
}

/* 操作记录样式 */
.history-list {
  max-height: 200px;
  overflow-y: auto;
  margin-top: 10px;
  padding: 10px;
  background-color: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
}

.history-item {
  display: flex;
  padding: 6px 0;
  font-size: 14px;
  border-bottom: 1px dashed #eee;
}

.history-item:last-child {
  border-bottom: none;
}

.time {
  flex: 0 0 80px;
  color: #888;
  font-size: 12px;
}

/* 占位符样式 */
.result-placeholder, .empty-history, .video-placeholder {
  padding: 20px 0;
  color: #999;
  text-align: center;
}

/* 垂直排列按钮组 */
.button-group.vertical {
  flex-direction: column;
}

.button-group.vertical button {
  width: 100%;
  box-sizing: border-box;
}

/* 响应式调整 */
@media (max-width: 1024px) {
  .monitor-container {
    flex-direction: column;
  }
  
  .video-container, .control-panel {
    min-width: 100%;
  }
}
</style>