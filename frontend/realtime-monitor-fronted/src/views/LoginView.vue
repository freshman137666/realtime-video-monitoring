<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1>登录</h1>
      <form @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="email">邮箱</label>
          <input id="email" type="email" v-model="email" required placeholder="请输入邮箱" />
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            type="password"
            v-model="password"
            required
            placeholder="请输入密码"
          />
        </div>

        <!-- 拼图验证码 -->
        <div class="captcha-group">
          <label>请拖动拼图完成验证</label>
          <button type="button" @click="onShow">开始验证</button>
          <Vcode :show="isShow" @success="onSuccess" @close="onClose" />
        </div>

        <button type="submit" :disabled="!isVerified">登录</button>
      </form>

      <div class="auth-footer">
        <span>还没有账号？</span>
        <router-link to="/register" class="register-link">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import Vcode from "vue3-puzzle-vcode"

const email = ref('admin@qq.com')
const password = ref('')
const router = useRouter()
const isShow = ref(false)
const isVerified = ref(false) // 验证状态标志位

// 显示验证码
const onShow = () => {
  isShow.value = true
}

// 关闭验证码
const onClose = () => {
  isShow.value = false
}

// 验证成功回调
const onSuccess = () => {
  isVerified.value = true // 标记验证成功
  onClose() // 关闭验证模态框
}

// 登录处理逻辑
const handleLogin = () => {
  if (!isVerified.value) {
    alert('请先完成拼图验证！') // 提示用户完成验证
    return
  }

  console.log('登录信息:', { email: email.value, password: password.value })
  router.push('/home')
}
</script>

<style scoped>
.auth-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background-color: #f0f9eb;
}

.auth-card {
  background: #fff;
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  width: 400px;
  text-align: center;
}

.form-group,
button,
input {
  width: 320px;
  margin: 0 auto 1.5rem;
}

.captcha-group {
  width: 340px;
  margin: 0 auto 1.5rem;
}

button:disabled {
  background-color: #ccc;
  cursor: not-allowed;
}

/* 验证按钮样式 */
.captcha-group button {
  background-color: #4caf50;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 8px 16px;
  cursor: pointer;
}

.captcha-group button:hover {
  background-color: #45a049;
}
</style>