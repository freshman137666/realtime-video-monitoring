<template>
  <div class="app-layout">
    <!-- 顶部栏 -->
    <header class="header">
      <div class="header-title">
        <h1>{{ pageTitle }}</h1>
      </div>
      <div class="header-profile">
        <div class="profile-info">
          <div class="avatar">
            <img src="https://via.placeholder.com/100" alt="用户头像">
          </div>
          <div class="name-role">
            <h2>{{ nickname }}</h2>
            <p>{{ role }}</p>
          </div>
        </div>
        <div class="menu-buttons">
          <button @click="goToAboutPage">关于</button>
          <button @click="logout">退出登录</button>
        </div>
      </div>
    </header>

    <div class="content-container">
      <!-- 左侧边栏 -->
      <aside class="sidebar">
        <div class="control-section">
          <h3>功能导航</h3>
          <div class="button-group vertical">
            <button @click="goToFaceRecognitionPage" :class="{ active: currentRoute === '/face' }">入站人脸</button>
            <button @click="goToMonitorPage" :class="{ active: currentRoute === '/monitor' }">监控大屏</button>
            <button @click="goToAlertPage" :class="{ active: currentRoute === '/alert' }">警报处置</button>
            <button @click="goToDevicePage" :class="{ active: currentRoute === '/device' }">设备信息</button>
          </div>
        </div>
      </aside>

      <!-- 主内容区域 -->
      <main class="main-content">
        <slot /> <!-- 其他页面内容将在这里显示 -->
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';

const router = useRouter();
const route = useRoute();
const pageTitle = ref('车站实时视频监控系统');
const role = ref('管理员');
const nickname = ref('张三');
const currentRoute = computed(() => route.path);

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

// 页面加载时设置当前活动路由
onMounted(() => {
  console.log('当前路由:', currentRoute.value);
});
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background-color: #f9f9f9;
  border-bottom: 1px solid #eee;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.header-title h1 {
  margin: 0;
  color: #2c3e50;
  font-size: 24px;
}

.header-profile {
  display: flex;
  align-items: center;
  gap: 20px;
}

.profile-info {
  display: flex;
  align-items: center;
}

.avatar {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  overflow: hidden;
  margin-right: 10px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.name-role h2 {
  margin: 0;
  font-size: 18px;
}

.name-role p {
  margin: 5px 0 0;
  color: #777;
  font-size: 14px;
}

.menu-buttons {
  display: flex;
  gap: 10px;
}

.content-container {
  display: flex;
  flex: 1;
}

.sidebar {
  width: 220px;
  padding: 20px 15px;
  background-color: #f9f9f9;
  border-right: 1px solid #eee;
}

.control-section {
  margin-bottom: 20px;
  padding: 15px;
  background-color: white;
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
  transition: background-color 0.3s;
}

button:hover {
  background-color: #45a049;
}

button.active {
  background-color: #2196F3;
}

.main-content {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}
</style>    