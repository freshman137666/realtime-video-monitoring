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
            <!-- 头像 -->
            <div class="avatar">
              <img src="https://via.placeholder.com/100" alt="Avatar">
            </div>
            <!-- 昵称和角色 -->
            <div class="name-role">
              <h2>{{ nickname }}</h2>
              <p>{{ role }}</p>
            </div>
          </div>
        </div>
        <div class="control-section">
          <h3>菜单</h3>
          <div class="button-group vertical">
            <button @click="goToAboutPage">关于</button>
            <button @click="logout">退出登录</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { useRouter } from 'vue-router';

const router = useRouter();
const role = ref('管理员');
const nickname = ref('张三');

const goToMonitorPage = () => {
  router.push('/monitor');
};

const goToAlertPage = () => {
  router.push('/alert');
};

const goToFaceRecognitionPage = () => {
  router.push('/face');
};

const goToAboutPage = () => {
  router.push('/about');
};

const goToDevicePage = () => {
  router.push('/device');
};

const logout = () => {
  localStorage.removeItem('role');
  router.push('/login');
};
</script>

<style scoped>
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

.button-container {
  flex: 2;
  min-width: 640px;
}

.control-panel {
  flex: 1;
  min-width: 300px;
}

.control-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 5px;
  border: 1px solid #eee;
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

.button-group.vertical {
  flex-direction: column;
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

.profile-info {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.name-role h2 {
  margin: 0;
  font-size: 20px;
}

.name-role p {
  margin: 5px 0 0;
  color: #777;
}

.control-panel ul {
  list-style-type: none;
  padding: 0;
  margin: 0;
}

.control-panel li {
  padding: 8px 0;
  cursor: pointer;
  transition: color 0.3s ease;
}

.control-panel li:hover {
  color: #2196F3;
}
</style>