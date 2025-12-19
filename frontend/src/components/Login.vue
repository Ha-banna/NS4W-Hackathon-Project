<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Card,
  Form,
  Input,
  Button,
  Typography,
  message
} from 'ant-design-vue'
import {
  UserOutlined,
  LockOutlined,
  ArrowLeftOutlined,
  LoginOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const { Title, Paragraph } = Typography

const email = ref('')
const password = ref('')
const loading = ref(false)

const validateEmail = (email: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const handleLogin = async () => {
  // Clear previous errors
  let hasError = false

  // Validate email
  if (!email.value.trim()) {
    message.error('Please enter your email address')
    hasError = true
  } else if (!validateEmail(email.value)) {
    message.error('Please enter a valid email address')
    hasError = true
  }

  // Validate password
  if (!password.value.trim()) {
    message.error('Please enter your password')
    hasError = true
  } else if (password.value.length < 6) {
    message.error('Password must be at least 6 characters long')
    hasError = true
  }

  if (hasError) {
    return
  }

  loading.value = true
  
  try {
    // Simulate API call - replace with actual login API
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    message.success('Login successful!')
    
    // Navigate to dashboard after successful login
    setTimeout(() => {
      router.push('/dashboard')
    }, 500)
  } catch (error) {
    message.error('Login failed. Please check your credentials.')
    console.error('Login error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <!-- Animated Background Elements -->
    <div class="animated-bg">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
    </div>

    <div class="login-container">
      <!-- Header -->
      <div class="page-header">
        <Button type="text" size="large" class="back-button" @click="router.push('/')">
          <template #icon>
            <ArrowLeftOutlined />
          </template>
          Back to Home
        </Button>
        <div class="header-content">
          <Title :level="2" class="page-title">
            <LoginOutlined /> Login
          </Title>
          <Paragraph class="page-subtitle">
            Sign in to access your CV evaluation dashboard
          </Paragraph>
        </div>
      </div>

      <!-- Login Card -->
      <Card class="login-card">
        <Form layout="vertical" class="login-form" @submit.prevent="handleLogin">
          <Form.Item 
            label="Email" 
            required
            class="form-item"
          >
            <Input
              v-model:value="email"
              type="email"
              placeholder="Enter your email address"
              size="large"
              class="form-input"
            >
              <template #prefix>
                <UserOutlined />
              </template>
            </Input>
          </Form.Item>

          <Form.Item 
            label="Password" 
            required
            class="form-item"
          >
            <Input
              v-model:value="password"
              type="password"
              placeholder="Enter your password"
              size="large"
              class="form-input"
            >
              <template #prefix>
                <LockOutlined />
              </template>
            </Input>
          </Form.Item>

          <Form.Item class="form-actions">
            <Button 
              type="primary" 
              size="large" 
              class="login-button"
              :loading="loading"
              @click="handleLogin"
              block
            >
              <template #icon>
                <LoginOutlined />
              </template>
              Login
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  width: 100%;
  min-height: 100vh;
  background: transparent;
  position: relative;
  padding: 40px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

/* Animated Background */
.animated-bg {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
  pointer-events: none;
  overflow: hidden;
}

.bg-circle {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.4;
}

.circle-1 {
  width: 500px;
  height: 500px;
  background: radial-gradient(circle, #722ed1 0%, transparent 70%);
  animation: float1 25s ease-in-out infinite;
}

.circle-2 {
  width: 400px;
  height: 400px;
  background: radial-gradient(circle, #b37feb 0%, transparent 70%);
  animation: float2 30s ease-in-out infinite;
}

.circle-3 {
  width: 600px;
  height: 600px;
  background: radial-gradient(circle, #722ed1 0%, transparent 70%);
  animation: float3 35s ease-in-out infinite;
}

@keyframes float1 {
  0% {
    transform: translate(-200px, -200px) scale(1);
  }
  25% {
    transform: translate(100px, 150px) scale(1.2);
  }
  50% {
    transform: translate(300px, -100px) scale(0.9);
  }
  75% {
    transform: translate(50px, 200px) scale(1.1);
  }
  100% {
    transform: translate(-200px, -200px) scale(1);
  }
}

@keyframes float2 {
  0% {
    transform: translate(calc(100vw + 150px), calc(50vh - 200px)) scale(1);
  }
  25% {
    transform: translate(calc(100vw - 100px), calc(50vh + 100px)) scale(1.1);
  }
  50% {
    transform: translate(calc(100vw - 400px), calc(50vh - 300px)) scale(0.8);
  }
  75% {
    transform: translate(calc(100vw - 200px), calc(50vh + 200px)) scale(1.2);
  }
  100% {
    transform: translate(calc(100vw + 150px), calc(50vh - 200px)) scale(1);
  }
}

@keyframes float3 {
  0% {
    transform: translate(calc(20vw - 300px), calc(100vh + 300px)) scale(1);
  }
  25% {
    transform: translate(calc(20vw + 200px), calc(100vh - 100px)) scale(1.3);
  }
  50% {
    transform: translate(calc(20vw + 500px), calc(100vh - 400px)) scale(0.9);
  }
  75% {
    transform: translate(calc(20vw + 100px), calc(100vh - 200px)) scale(1.1);
  }
  100% {
    transform: translate(calc(20vw - 300px), calc(100vh + 300px)) scale(1);
  }
}

.login-container {
  max-width: 500px;
  width: 100%;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.page-header {
  margin-bottom: 32px;
  text-align: center;
}

.back-button {
  color: rgba(255, 255, 255, 0.7);
  padding: 8px 16px;
  height: auto;
  margin-bottom: 24px;
}

.back-button:hover {
  color: #b37feb;
  background: rgba(114, 46, 209, 0.1);
}

.header-content {
  text-align: center;
}

.page-title {
  margin-bottom: 8px !important;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.page-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.1rem;
  margin: 0;
}

.login-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.login-card :deep(.ant-card-body) {
  padding: 40px;
}

.login-form {
  width: 100%;
}

.form-item {
  margin-bottom: 24px;
}

.form-item :deep(.ant-form-item-label > label) {
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 1rem;
}

.form-input :deep(.ant-input) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(114, 46, 209, 0.3);
  color: rgba(255, 255, 255, 0.9);
  font-size: 1rem;
  padding: 12px 16px 12px 40px;
}

.form-input :deep(.ant-input):focus {
  border-color: #722ed1;
  box-shadow: 0 0 0 2px rgba(114, 46, 209, 0.2);
}

.form-input :deep(.ant-input)::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.form-input :deep(.ant-input-prefix) {
  color: rgba(255, 255, 255, 0.6);
  margin-right: 12px;
}

.form-input :deep(.ant-input):focus + .ant-input-prefix,
.form-input :deep(.ant-input):focus ~ .ant-input-prefix {
  color: #722ed1;
}

.form-actions {
  margin-top: 32px;
  margin-bottom: 0;
}

.login-button {
  height: 48px;
  font-weight: 600;
  font-size: 1rem;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(114, 46, 209, 0.4);
  transition: all 0.3s ease;
}

.login-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(114, 46, 209, 0.5);
}

.login-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }

  .login-card :deep(.ant-card-body) {
    padding: 24px;
  }
}
</style>
