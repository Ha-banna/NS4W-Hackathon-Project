<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import {
  Card,
  Form,
  Button,
  Upload,
  Space,
  Typography,
  message
} from 'ant-design-vue'
import {
  UploadOutlined,
  ArrowLeftOutlined,
  FileTextOutlined
} from '@ant-design/icons-vue'
import type { UploadFile, UploadProps } from 'ant-design-vue'
import apiClient from '../api/axios'

const router = useRouter()
const { Title, Paragraph } = Typography

const fileList = ref<UploadFile[]>([])
const uploading = ref(false)

const handleFileChange: UploadProps['onChange'] = (info) => {
  fileList.value = info.fileList
  if (info.file.status === 'done') {
    message.success(`${info.file.name} file uploaded successfully`)
  } else if (info.file.status === 'error') {
    message.error(`${info.file.name} file upload failed`)
  }
}

const handleSubmit = async () => {
  if (fileList.value.length === 0 || !fileList.value[0]) {
    message.error('Please upload a CV file')
    return
  }

  const file = fileList.value[0]
  const originFile = file.originFileObj
  if (!originFile) {
    message.error('Please select a valid file')
    return
  }

  uploading.value = true

  try {
    const formData = new FormData()
    formData.append('file', originFile)

    const response = await apiClient.post('/analysis/upload-cv', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })

    message.success('CV submitted successfully!')
    console.log('Upload response:', response.data)
    
    // Navigate back to dashboard after submission
    setTimeout(() => {
      router.push('/dashboard')
    }, 1500)
  } catch (error: any) {
    console.error('Error uploading CV:', error)
    message.error(error.response?.data?.detail || 'Failed to upload CV. Please try again.')
  } finally {
    uploading.value = false
  }
}

const uploadProps: UploadProps = {
  name: 'file',
  accept: '.pdf',
  multiple: false,
  maxCount: 1,
  beforeUpload: (file) => {
    const isPDF = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    
    if (!isPDF) {
      message.error('You can only upload PDF files!')
      return false
    }
    
    const isLt50M = file.size / 1024 / 1024 < 50
    if (!isLt50M) {
      message.error('File must be smaller than 50MB!')
      return false
    }
    
    // Prevent automatic upload - we'll handle it manually in handleSubmit
    return false
  },
  onChange: handleFileChange,
}
</script>

<template>
  <div class="create-cv-page">
    <!-- Animated Background Elements -->
    <div class="animated-bg">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
    </div>

    <div class="create-cv-container">
      <!-- Header -->
      <div class="page-header">
        <Button type="text" size="large" class="back-button" @click="router.push('/dashboard')">
          <template #icon>
            <ArrowLeftOutlined />
          </template>
          Back to Dashboard
        </Button>
        <div class="header-content">
          <Title :level="2" class="page-title">
            <FileTextOutlined /> Upload CV
          </Title>
          <Paragraph class="page-subtitle">
            Upload a candidate's CV for evaluation
          </Paragraph>
        </div>
      </div>

      <!-- Form Card -->
      <Card class="form-card">
        <Form layout="vertical" class="cv-form">
          <Form.Item 
            label="CV File" 
            required
            class="form-item"
          >
            <Upload
              v-model:file-list="fileList"
              v-bind="uploadProps"
              class="upload-component"
              :drag="true"
            >
              <div class="upload-area">
                <p class="upload-icon">
                  <UploadOutlined />
                </p>
                <p class="upload-text">Click or drag PDF file to this area to upload</p>
                <p class="upload-hint-text">PDF only (Max 50MB)</p>
              </div>
            </Upload>
          </Form.Item>

          <Form.Item class="form-actions">
            <Space size="large">
              <Button 
                type="primary" 
                size="large" 
                class="submit-button"
                :loading="uploading"
                @click="handleSubmit"
              >
                Submit CV
              </Button>
              <Button 
                size="large" 
                class="cancel-button"
                @click="router.push('/dashboard')"
              >
                Cancel
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>
    </div>
  </div>
</template>

<style scoped>
.create-cv-page {
  width: 100%;
  min-height: 100vh;
  background: transparent;
  position: relative;
  padding: 40px 20px;
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

.create-cv-container {
  max-width: 800px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.page-header {
  margin-bottom: 32px;
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

.form-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.form-card :deep(.ant-card-body) {
  padding: 40px;
}

.cv-form {
  max-width: 600px;
  margin: 0 auto;
}

.form-item {
  margin-bottom: 32px;
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
  padding: 12px 16px;
}

.form-input :deep(.ant-input):focus {
  border-color: #722ed1;
  box-shadow: 0 0 0 2px rgba(114, 46, 209, 0.2);
}

.form-input :deep(.ant-input)::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.upload-component {
  width: 100%;
  display: flex;
  justify-content: center;
}

.upload-component :deep(.ant-upload-drag) {
  background: rgba(255, 255, 255, 0.05);
  border: 2px dashed rgba(114, 46, 209, 0.5);
  border-radius: 12px;
  padding: 60px 40px;
  transition: all 0.3s ease;
  width: 100%;
  max-width: 600px;
  margin: 0 auto;
}

.upload-component :deep(.ant-upload-drag:hover) {
  background: rgba(114, 46, 209, 0.1);
  border-color: #722ed1;
}

.upload-component :deep(.ant-upload-drag.ant-upload-drag-hover) {
  background: rgba(114, 46, 209, 0.15);
  border-color: #b37feb;
  border-style: solid;
}

.upload-area {
  text-align: center;
  padding: 20px;
}

.upload-icon {
  font-size: 4rem;
  color: #722ed1;
  margin: 0 0 24px 0;
  display: flex;
  justify-content: center;
  align-items: center;
}

.upload-text {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.1rem;
  font-weight: 500;
  margin: 0 0 12px 0;
}

.upload-hint-text {
  color: rgba(255, 255, 255, 0.6);
  font-size: 0.9rem;
  margin: 0;
}

.form-actions {
  margin-top: 40px;
  margin-bottom: 0;
  text-align: center;
}

.submit-button {
  height: 48px;
  padding: 0 40px;
  font-weight: 600;
  font-size: 1rem;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(114, 46, 209, 0.4);
  transition: all 0.3s ease;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(114, 46, 209, 0.5);
}

.cancel-button {
  height: 48px;
  padding: 0 40px;
  font-weight: 600;
  font-size: 1rem;
  background: transparent;
  border: 2px solid rgba(114, 46, 209, 0.5);
  color: rgba(255, 255, 255, 0.9);
  transition: all 0.3s ease;
}

.cancel-button:hover {
  background: rgba(114, 46, 209, 0.1);
  border-color: #722ed1;
  color: #b37feb;
}

.upload-component :deep(.ant-upload-list) {
  margin-top: 16px;
}

.upload-component :deep(.ant-upload-list-item) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(114, 46, 209, 0.3);
  border-radius: 8px;
  color: rgba(255, 255, 255, 0.9);
}

.upload-component :deep(.ant-upload-list-item-name) {
  color: rgba(255, 255, 255, 0.9);
}

.upload-component :deep(.ant-upload-list-item-actions button) {
  color: rgba(255, 255, 255, 0.7);
}

.upload-component :deep(.ant-upload-list-item-actions button:hover) {
  color: #b37feb;
}

/* Responsive */
@media (max-width: 768px) {
  .page-title {
    font-size: 2rem;
  }

  .form-card :deep(.ant-card-body) {
    padding: 24px;
  }

  .form-actions {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .submit-button,
  .cancel-button {
    width: 100%;
  }
}
</style>
