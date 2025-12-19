<script setup lang="ts">
import { ref } from 'vue'
import { Button, message, Card, Space } from 'ant-design-vue'
import apiClient from './api/axios'

const loading = ref(false)
const data = ref<string | null>(null)

const handleTestApi = async () => {
  loading.value = true
  try {
    // Example API call - replace with your actual endpoint
    const response = await apiClient.get('/test')
    data.value = JSON.stringify(response.data, null, 2)
    message.success('API call successful!')
  } catch (error) {
    message.error('API call failed. Check console for details.')
    console.error('API Error:', error)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="container">
    <Card title="Vue 3 + TypeScript + Ant Design + Axios">
      <Space direction="vertical" size="large" style="width: 100%">
        <p>Welcome to your Vue project with TypeScript, Ant Design Vue, and Axios configured!</p>
        
        <Button type="primary" :loading="loading" @click="handleTestApi">
          Test API Call
        </Button>

        <div v-if="data" style="background: #f5f5f5; padding: 16px; border-radius: 4px;">
          <pre>{{ data }}</pre>
        </div>
      </Space>
    </Card>
  </div>
</template>

<style scoped>
.container {
  max-width: 800px;
  margin: 50px auto;
  padding: 20px;
}
</style>
