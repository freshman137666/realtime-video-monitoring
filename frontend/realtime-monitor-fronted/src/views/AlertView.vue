<template>
  <div class="alert-info-page">
    <h1>告警信息</h1>

    <div class="alert-section">
      <h2>告警信息详情</h2>
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
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';

// API端点设置
const SERVER_ROOT_URL = 'http://localhost:5000';
const API_BASE_URL = `${SERVER_ROOT_URL}/api`;

// 状态变量
const alerts = ref([]);

// 定期轮询告警信息
let alertPollingInterval = null;

const startAlertPolling = () => {
  // 先清除之前的轮询
  if (alertPollingInterval) {
    clearInterval(alertPollingInterval);
  }

  // 开始新的轮询
  alertPollingInterval = setInterval(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/alerts`);
      const data = await response.json();
      alerts.value = data.alerts || [];
    } catch (error) {
      console.error('Error fetching alerts:', error);
    }
  }, 3000);
};

// 生命周期钩子
onMounted(() => {
  startAlertPolling();
});

onUnmounted(() => {
  if (alertPollingInterval) {
    clearInterval(alertPollingInterval);
  }
});
</script>

<style scoped>
.alert-info-page {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

h1 {
  text-align: center;
  margin-bottom: 30px;
  color: #2c3e50;
}

.alert-section {
  margin-top: 30px;
}

.alerts-container {
  max-height: 400px;
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
</style>