<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1>注册</h1>
      <form @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="name">用户名</label>
          <input 
            id="name" 
            type="text" 
            v-model="name" 
            required
            placeholder="请输入用户名"
          >
        </div>
        <div class="form-group">
          <label for="email">邮箱</label>
          <input 
            id="email" 
            type="email" 
            v-model="email" 
            required
            placeholder="请输入邮箱"
          >
        </div>
        <div class="form-group">
          <label for="password">密码</label>
          <input
            id="password"
            type="password"
            v-model="password"
            required
            placeholder="请输入密码"
          >
        </div>
        <div class="form-group">
          <label for="confirmPassword">确认密码</label>
          <input
            id="confirmPassword"
            type="password"
            v-model="confirmPassword"
            required
            placeholder="请再次输入密码"
          >
        </div>
        <button type="submit">注册</button>
      </form>
      
      <div class="auth-footer">
        <span>已有账号？</span>
        <router-link to="/login" class="login-link">立即登录</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const name = ref('')
const email = ref('')
const password = ref('')
const confirmPassword = ref('')
const router = useRouter()

const handleRegister = () => {
  // 简单验证密码是否一致
  if (password.value !== confirmPassword.value) {
    alert('两次输入的密码不一致')
    return
  }
  
  // 模拟注册成功
  console.log('注册信息:', { 
    name: name.value,
    email: email.value,
    password: password.value
  })
  
  // 注册成功后跳转到登录页
  router.push('/')
}
</script>

<style scoped>
/* 复用登录页的样式 */
.auth-container,
.auth-card,
h1,
.form-group,
label,
input,
button,
.auth-footer {
  /* 保持与登录页相同的样式 */
}

.login-link {
  color: var(--vt-c-indigo);
  font-weight: 500;
  margin-left: 0.5rem;
  text-decoration: none;
}

.login-link:hover {
  text-decoration: underline;
}
</style>