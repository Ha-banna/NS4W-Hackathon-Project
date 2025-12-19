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
  MailOutlined,
  BuildOutlined,
  FileTextOutlined,
  ArrowLeftOutlined,
  SendOutlined
} from '@ant-design/icons-vue'

const router = useRouter()
const { Title, Paragraph } = Typography

const name = ref('')
const email = ref('')
const company = ref('')
const message = ref('')
const loading = ref(false)

const validateEmail = (email: string) => {
  const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
  return emailRegex.test(email)
}

const handleSubmit = async () => {
  // Clear previous errors
  let hasError = false

  // Validate name
  if (!name.value.trim()) {
    message.error('Please enter your name')
    hasError = true
  }

  // Validate email
  if (!email.value.trim()) {
    message.error('Please enter your email address')
    hasError = true
  } else if (!validateEmail(email.value)) {
    message.error('Please enter a valid email address')
    hasError = true
  }

  // Validate company
  if (!company.value.trim()) {
    message.error('Please enter your company name')
    hasError = true
  }

  // Validate message
  if (!message.value.trim()) {
    message.error('Please enter a message')
    hasError = true
  } else if (message.value.trim().length < 20) {
    message.error('Message must be at least 20 characters long')
    hasError = true
  }

  if (hasError) {
    return
  }

  loading.value = true
  
  try {
    // Simulate API call - replace with actual request API
    await new Promise(resolve => setTimeout(resolve, 1500))
    
    message.success('Request submitted successfully! We will get back to you soon.')
    
    // Reset form
    name.value = ''
    email.value = ''
    company.value = ''
    message.value = ''
    
    // Optionally navigate back to landing page after a delay
    setTimeout(() => {
      router.push('/')
    }, 2000)
  } catch (error) {
    message.error('Failed to submit request. Please try again.')
    console.error('Request error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="request-page">
    <!-- Animated Background Elements -->
    <div class="animated-bg">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
    </div>

    <div class="request-container">
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
            <SendOutlined /> Request to Join
          </Title>
          <Paragraph class="page-subtitle">
            Fill out the form below to request access to the Busted platform
          </Paragraph>
        </div>
      </div>

      <!-- Request Card -->
      <Card class="request-card">
        <Form layout="vertical" class="request-form" @submit.prevent="handleSubmit">
          <Form.Item 
            label="Full Name" 
            required
            class="form-item"
          >
            <Input
              v-model:value="name"
              type="text"
              placeholder="Enter your full name"
              size="large"
              class="form-input"
            >
              <template #prefix>
                <UserOutlined />
              </template>
            </Input>
          </Form.Item>

          <Form.Item 
            label="Email Address" 
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
                <MailOutlined />
              </template>
            </Input>
          </Form.Item>

          <Form.Item 
            label="Company Name" 
            required
            class="form-item"
          >
            <Input
              v-model:value="company"
              type="text"
              placeholder="Enter your company name"
              size="large"
              class="form-input"
            >
              <template #prefix>
                <BuildOutlined />
              </template>
            </Input>
          </Form.Item>

          <Form.Item 
            label="Message" 
            required
            class="form-item"
          >
            <Input.TextArea
              v-model:value="message"
              placeholder="Tell us about your company and why you'd like to join the platform..."
              :rows="6"
              class="form-textarea"
              :maxlength="500"
              show-count
            />
          </Form.Item>

          <Form.Item class="form-actions">
            <Button 
              type="primary" 
              size="large" 
              class="submit-button"
              :loading="loading"
              @click="handleSubmit"
              block
            >
              <template #icon>
                <SendOutlined />
              </template>
              Submit Request
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.request-page {
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

.request-container {
  max-width: 600px;
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

.request-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.request-card :deep(.ant-card-body) {
  padding: 40px;
}

.request-form {
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

.form-textarea :deep(.ant-input) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(114, 46, 209, 0.3);
  color: rgba(255, 255, 255, 0.9);
  font-size: 1rem;
  padding: 12px 16px;
  resize: vertical;
}

.form-textarea :deep(.ant-input):focus {
  border-color: #722ed1;
  box-shadow: 0 0 0 2px rgba(114, 46, 209, 0.2);
}

.form-textarea :deep(.ant-input)::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.form-textarea :deep(.ant-input) {
  min-height: 120px;
}

.form-textarea :deep(.ant-input-count) {
  color: rgba(255, 255, 255, 0.5);
  background: transparent;
}

.form-actions {
  margin-top: 32px;
  margin-bottom: 0;
}

.submit-button {
  height: 48px;
  font-weight: 600;
  font-size: 1rem;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(114, 46, 209, 0.4);
  transition: all 0.3s ease;
}

.submit-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(114, 46, 209, 0.5);
}

.submit-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* Responsive */
@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }

  .request-card :deep(.ant-card-body) {
    padding: 24px;
  }
}
</style>
