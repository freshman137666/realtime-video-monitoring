<template>
  <div class="auth-container">
    <div class="auth-card">
      <h1>登录</h1>
      <form @submit.prevent="handleLogin">
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
        
        <!-- 验证码区域 -->
        <div class="captcha-group">
          <label>验证码</label>
          <div class="captcha-row">
            <input
              v-model="captchaInput"
              type="text"
              placeholder="请输入验证码"
              required
              class="captcha-input"
            >
            <canvas 
              ref="captchaCanvas" 
              @click="generateCaptcha"
              class="captcha-canvas"
            ></canvas>
          </div>
        </div>
        
        <button type="submit">登录</button>
      </form>
      
      <div class="auth-footer">
        <span>还没有账号？</span>
        <router-link to="/register" class="register-link">立即注册</router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const email = ref('admin@qq.com')  // 预设邮箱
const password = ref('')
const captchaInput = ref('')
const captchaCanvas = ref(null)
const captchaText = ref('')
const router = useRouter()

// 生成随机验证码文本（增加复杂度）
const generateRandomText = () => {
  const chars = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ' // 去除易混淆字符
  let result = ''
  for (let i = 0; i < 5; i++) {  // 增加到5位
    result += chars.charAt(Math.floor(Math.random() * chars.length))
  }
  return result
}

// 增强版绘制验证码
const drawCaptcha = () => {
  const canvas = captchaCanvas.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  
  // 清空画布
  ctx.clearRect(0, 0, width, height)
  
 // 极限干扰背景
const gradient = ctx.createLinearGradient(
  width * 0.2,  // 起点偏移20%
  height * 0.2, 
  width * 0.8,   // 终点偏移80%
  height * 0.8
)
gradient.addColorStop(0, getRandomColor(150, 190))  // 降低亮度范围
gradient.addColorStop(1, getRandomColor(150, 190))
ctx.fillStyle = gradient
ctx.fillRect(0, 0, width, height)


// 随机波浪干扰线（500条）
for (let i = 0; i < 300; i++) {
  ctx.strokeStyle = getRandomColor(30, 150, 0.7);
  ctx.lineWidth = Math.random() * 14 + 1;
  
  const startX = Math.random() * width * 1.5 - width * 0.25;
  const startY = Math.random() * height * 1.5 - height * 0.25;
  const endX = Math.random() * width * 1.5 - width * 0.25;
  const endY = Math.random() * height * 1.5 - height * 0.25;
  
  ctx.beginPath();
  ctx.moveTo(startX, startY);
  
  // 将直线变为极度扭曲的贝塞尔曲线
const cp1x = startX + (endX - startX) * 0.05 + (Math.random() - 0.5) * width * 0.6;  // 控制点1更靠近起点且随机偏移更大
const cp1y = startY + (endY - startY) * 0.05 + (Math.random() - 0.5) * height * 0.8; // 垂直方向偏移更大

const cp2x = startX + (endX - startX) * 0.95 + (Math.random() - 0.5) * width * 0.6;  // 控制点2更靠近终点
const cp2y = startY + (endY - startY) * 0.95 + (Math.random() - 0.5) * height * 0.8;

// 添加两个中间控制点制造复杂波浪
const cpMid1x = (startX + endX)/2 + (Math.random() - 0.5) * width * 0.8;
const cpMid1y = (startY + endY)/2 + (Math.random() - 0.5) * height * 1.2;

const cpMid2x = (startX + endX)/3 + (Math.random() - 0.5) * width * 0.7;
const cpMid2y = (startY + endY)/3 + (Math.random() - 0.5) * height * 1.0;

// 绘制更复杂的曲线
ctx.beginPath();
ctx.moveTo(startX, startY);
ctx.bezierCurveTo(cp1x, cp1y, cpMid1x, cpMid1y, (startX + endX)/2, (startY + endY)/2);
ctx.bezierCurveTo(cpMid2x, cpMid2y, cp2x, cp2y, endX, endY);
ctx.stroke();
}

// // 高密度干扰点（80个更大的点）
// for (let i = 0; i < 500; i++) {
//   ctx.fillStyle = getRandomColor(0, 255, 0.4)  // 更高透明度
//   ctx.beginPath()
//   ctx.arc(
//     Math.random() * width,
//     Math.random() * height,
//     Math.random() * 4,  // 更大的点半径
//     0,
//     Math.PI * 2
//   )
//   ctx.fill()
// }

// 极限扭曲文本
for (let i = 0; i < captchaText.value.length; i++) {
  ctx.font = `bold ${30 + Math.random() * 20}px Arial`  // 更大字体波动范围
  ctx.fillStyle = getRandomColor(15, 80)  // 更低对比度
  
  // 极端位置偏移
  const x = (width / (captchaText.value.length + 2)) * (i + 1.5)
  const y = height / 2 +50+ (Math.random() * 15 - 7.5)
  
  // 增强扭曲参数
  const angle = (Math.random() - 0.5)   // 更大旋转角度 (±68度)
  const wave1 = 15 * Math.sin(Date.now()/400 + i*120)  // 更快波动
  const wave2 = 15 * Math.cos(Date.now()/300 + i*90)
  
  ctx.save()
  ctx.translate(x, y)
  ctx.rotate(angle)
  ctx.transform(
    1, 
    wave1/15,  // 增强水平扭曲
    wave2/15,  // 增强垂直扭曲
    3,       // 轻微缩放
    0, 
    0
  )
  ctx.fillText(captchaText.value.charAt(i), 
    Math.random() * 5 - 1.5,  // 横向微偏移
    Math.random() * 5 - 1.5    // 纵向微偏移
  )
  ctx.restore()
}
}

// 增强随机颜色（支持透明度）
const getRandomColor = (min, max, alpha) => {
  const r = min + Math.floor(Math.random() * (max - min))
  const g = min + Math.floor(Math.random() * (max - min))
  const b = min + Math.floor(Math.random() * (max - min))
  return alpha ? `rgba(${r}, ${g}, ${b}, ${alpha})` : `rgb(${r}, ${g}, ${b})`
}


// 生成新验证码
const generateCaptcha = () => {
  captchaText.value = generateRandomText()
  drawCaptcha()
}

// 验证验证码
const validateCaptcha = () => {
  return captchaInput.value.toUpperCase() === captchaText.value
}

const handleLogin = () => {
  if (!validateCaptcha()) {
    alert('验证码错误，请重新输入！')
    generateCaptcha()
    captchaInput.value = ''
    return
  }
  
  // 验证码正确，继续登录流程
  console.log('登录信息:', { email: email.value, password: password.value })
  router.push('/home')
}

// 初始化验证码
onMounted(() => {
  generateCaptcha()
})
</script>

<style scoped>
/* 统一所有表单组宽度 */
.form-group, button,input {
  width: 320px;
  margin: 0 auto 1.5rem;
}



/* 增强验证码区域 */
.captcha-canvas {
  width: 120px; /* 稍宽 */
  height: 45px; /* 稍高 */
  background: linear-gradient(135deg, #f5f5f5 0%, #e0e0e0 100%);
  border: 1px solid #ddd;
}

.captcha-row {
  width: 320px;
  margin: 0 auto 1.5rem;
}

.captcha-input {
  width: calc(100% - 130px) !important; /* 精确计算宽度 */
}

/* 保持其他原有样式不变 */
.auth-container {
  background-color: #f0f9eb;
}
</style>