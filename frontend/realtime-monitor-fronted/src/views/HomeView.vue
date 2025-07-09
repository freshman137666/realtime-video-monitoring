<template>
  <div class="monitor-page">
    <h1>车站实时视频监控系统</h1>
    <div class="monitor-container">
      <!-- 中间按钮区域 -->
      <div class="button-container">
        <div class="control-section">
          <h3>操作选项</h3>
          <div class="button-group">
            <button @click="goToFaceRecognitionPage" :class="{ active: false }">入站人脸</button>
            <button @click="goToMonitorPage" :class="{ active: false }">监控大屏</button>
            <button @click="goToAlertPage" :class="{ active: false }">警报处置</button>
            <button @click="goToDevicePage" :class="{ active: false }">设备信息</button>
          </div>
        </div>
      </div>
      <!-- 右侧个人信息区域 -->
      <div class="control-panel">
        <div class="control-section">
          <h3>个人信息</h3>
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
        <div class="control-section">
          <h3>菜单</h3>
          <div class="button-group">
            <button @click="goToAboutPage">关于系统</button>
            <button @click="logout" class="logout-btn">退出登录</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const role = ref('管理员')
const nickname = ref('张三')

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
  // 清除本地存储的登录状态
  localStorage.removeItem('authToken')
  localStorage.removeItem('userInfo')
  
  // 跳转到登录页并替换历史记录
  router.replace('/')
}
</script>

<style scoped>
.monitor-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
  min-height: 100vh;
  background-color: var(--color-background);
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: var(--color-heading);
  font-size: 28px;
}

.monitor-container {
  display: flex;
  gap: 20px;
  justify-content: center;
}

.button-container {
  flex: 2;
  min-width: 640px;
  max-width: 800px;
}

.control-panel {
  flex: 1;
  min-width: 300px;
  max-width: 350px;
}

.control-section {
  margin-bottom: 20px;
  padding: 20px;
  background-color: var(--color-background-soft);
  border-radius: 8px;
  border: 1px solid var(--color-border);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

h3 {
  margin-bottom: 15px;
  color: var(--color-heading);
  font-size: 18px;
  font-weight: 600;
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.button-group.vertical {
  flex-direction: column;
}

button {
  padding: 12px 16px;
  background-color: var(--vt-c-indigo);
  color: white;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  transition: all 0.3s ease;
  text-align: center;
}

button:hover {
  background-color: #1a2a3a;
  transform: translateY(-2px);
}

button.active {
  background-color: #2196F3;
}

.profile-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  overflow: hidden;
  border: 3px solid var(--color-border);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.name-role h2 {
  margin: 0;
  font-size: 20px;
  color: var(--color-heading);
}

.name-role p {
  margin: 5px 0 0;
  color: var(--color-text);
  font-size: 14px;
}

.logout-btn {
  background-color: #f44336 !important;
  margin-top: 10px;
}

.logout-btn:hover {
  background-color: #d32f2f !important;
}

@media (max-width: 1024px) {
  .monitor-container {
    flex-direction: column;
  }
  
  .button-container,
  .control-panel {
    min-width: 100%;
    max-width: 100%;
  }
}
</style>