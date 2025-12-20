<script setup lang="ts">
import { ref, computed, h, onMounted } from 'vue'

import { useRouter } from 'vue-router'

const router = useRouter()
import {
  Card,
  Table,
  Input,
  Button,
  Space,
  Tag,
  Typography,
  Row,
  Col,
  message
} from 'ant-design-vue'
import {
  PlusOutlined,
  SearchOutlined,
  FileTextOutlined,
  FilterOutlined,
  HomeOutlined
} from '@ant-design/icons-vue'
import type { ColumnsType } from 'ant-design-vue/es/table'
import ScoreCircle from './ScoreCircle.vue'
import apiClient from '../api/axios'

const { Title, Paragraph } = Typography

interface CVItem {
  key: string
  name: string
  email: string
  score: number
  uploadedDate: string
  skills: string[]
}

const cvData = ref<CVItem[]>([])
const loading = ref(false)

const searchText = ref('')
const dateRange = ref<[string, string] | null>(null)
const sortField = ref<string | undefined>(undefined)
const sortOrder = ref<'ascend' | 'descend' | undefined>(undefined)

// Filtered and sorted data
const filteredData = computed(() => {
  let result = [...cvData.value]

  // Search filter
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(cv =>
      cv.name.toLowerCase().includes(search) ||
      cv.email.toLowerCase().includes(search) ||
      cv.skills.some(skill => skill.toLowerCase().includes(search))
    )
  }

  // Date range filter
  if (dateRange.value) {
    const [start, end] = dateRange.value
    result = result.filter(cv => {
      const cvDate = new Date(cv.uploadedDate)
      return cvDate >= new Date(start) && cvDate <= new Date(end)
    })
  }

  // Sorting
  if (sortField.value && sortOrder.value) {
    result.sort((a, b) => {
      const aVal = a[sortField.value as keyof typeof a]
      const bVal = b[sortField.value as keyof typeof b]
      
      if (typeof aVal === 'number' && typeof bVal === 'number') {
        return sortOrder.value === 'ascend' ? aVal - bVal : bVal - aVal
      }
      
      const aStr = String(aVal).toLowerCase()
      const bStr = String(bVal).toLowerCase()
      
      if (sortOrder.value === 'ascend') {
        return aStr < bStr ? -1 : aStr > bStr ? 1 : 0
      } else {
        return aStr > bStr ? -1 : aStr < bStr ? 1 : 0
      }
    })
  }

  return result
})

const handleAddCV = () => {
  router.push('/create-cv')
}

const columns: ColumnsType = [
  {
    title: 'Name',
    dataIndex: 'name',
    key: 'name',
    sorter: true,
    width: 150,
  },
  {
    title: 'Email',
    dataIndex: 'email',
    key: 'email',
    width: 200,
  },
  {
    title: 'Score',
    dataIndex: 'score',
    key: 'score',
    sorter: true,
    width: 150,
    align: 'center',
    customRender: ({ record }: { record: any }) => {
      // @ts-ignore
      return h(ScoreCircle, { score: record.score })
    },
  },
  {
    title: 'Skills',
    dataIndex: 'skills',
    key: 'skills',
    width: 250,
    customRender: ({ record }: { record: any }) => {
      // @ts-ignore
      const tags = record.skills.slice(0, 3).map((skill: string) =>
        h(Tag, { key: skill, color: 'purple' }, () => skill)
      )
      if (record.skills.length > 3) {
        // @ts-ignore
        tags.push(h(Tag, { key: 'more' }, () => `+${record.skills.length - 3}`))
      }
      // @ts-ignore
      return h(Space, { size: 'small', wrap: true }, () => tags)
    },
  },
  {
    title: 'Uploaded Date',
    dataIndex: 'uploadedDate',
    key: 'uploadedDate',
    sorter: true,
    width: 150,
  },
  {
    title: 'Actions',
    key: 'actions',
    width: 120,
    customRender: ({ record }: { record: any }) => {
      // @ts-ignore
      return h(Button, { 
        type: 'link', 
        size: 'small',
        onClick: () => router.push(`/cv/${record.key}`)
      }, () => 'View')
    },
  },
]

const handleTableChange = (_pagination: any, _filters: any, sorter: any) => {
  if (sorter.field) {
    sortField.value = sorter.field
    sortOrder.value = sorter.order
  } else {
    sortField.value = undefined
    sortOrder.value = undefined
  }
}

const clearFilters = () => {
  searchText.value = ''
  dateRange.value = null
  sortField.value = undefined
  sortOrder.value = undefined
}

const fetchCVs = async () => {
  loading.value = true
  try {
    const response = await apiClient.get('/cv-results')
    // Transform the API response to match our data structure
    const data = Array.isArray(response.data) ? response.data : [response.data]
    
    cvData.value = data.map((cv: any) => {
      const candidate = cv.cv?.candidate || {};
      const skills = cv.cv?.skills || {};
      const technicalSkills = skills.technical || [];
      
      return {
        key: String(cv._id || Math.random()),
        name: candidate.full_name || 'Unknown',
        email: candidate.contact?.email || '',
        score: Math.round(cv.projects_authenticity?.overall_authenticity_score || 0),
        uploadedDate: cv.cv?.meta?.last_updated || new Date().toISOString().split('T')[0],
        skills: technicalSkills.slice(0, 10) // Limit to first 10 skills
      }
    })
  } catch (error: any) {
    console.error('Error fetching CVs:', error)
    message.error('Failed to load CVs. Please try again later.')
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchCVs()
})
</script>

<template>
  <div class="dashboard-page">
    <!-- Animated Background Elements -->
    <div class="animated-bg">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
    </div>

    <div class="dashboard-container">
      <!-- Header -->
      <div class="dashboard-header">
        <div class="header-content">
          <div class="header-top">
            <Button type="text" size="large" class="back-button" @click="router.push('/')">
              <template #icon>
                <HomeOutlined />
              </template>
              Home
            </Button>
          </div>
          <Title :level="2" class="dashboard-title">
            <FileTextOutlined /> CV Dashboard
          </Title>
          <Paragraph class="dashboard-subtitle">
            Manage and evaluate candidate CVs
          </Paragraph>
        </div>
        <Button type="primary" size="large" class="add-cv-button" @click="handleAddCV">
          <template #icon>
            <PlusOutlined />
          </template>
          Add CV
        </Button>
      </div>

      <!-- Filters Card -->
      <Card class="filters-card">
        <Row :gutter="[16, 16]">
          <Col :xs="24" :sm="12" :md="8" :lg="6">
            <Input
              v-model:value="searchText"
              placeholder="Search CVs..."
              size="large"
              class="search-input"
            >
              <template #prefix>
                <SearchOutlined />
              </template>
            </Input>
          </Col>
          <Col :xs="24" :sm="12" :md="8" :lg="6">
            <Space>
              <Button size="large" @click="clearFilters">
                <FilterOutlined /> Clear Filters
              </Button>
            </Space>
          </Col>
        </Row>
      </Card>

      <!-- Table Card -->
      <Card class="table-card">
        <Table
          :columns="columns"
          :data-source="filteredData"
          :loading="loading"
          :pagination="{ pageSize: 10, showSizeChanger: true, showTotal: (total) => `Total ${total} CVs` }"
          @change="handleTableChange"
          class="cv-table"
        />
      </Card>
    </div>
  </div>
</template>

<style scoped>
.dashboard-page {
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

.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  flex-wrap: wrap;
  gap: 20px;
}

.header-content {
  flex: 1;
}

.header-top {
  margin-bottom: 16px;
}

.back-button {
  color: rgba(255, 255, 255, 0.7);
  padding: 8px 16px;
  height: auto;
}

.back-button:hover {
  color: #b37feb;
  background: rgba(114, 46, 209, 0.1);
}

.dashboard-title {
  margin-bottom: 8px !important;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2.5rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
}

.dashboard-subtitle {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.1rem;
  margin: 0;
}

.add-cv-button {
  height: 48px;
  padding: 0 32px;
  font-weight: 600;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(114, 46, 209, 0.4);
  transition: all 0.3s ease;
}

.add-cv-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(114, 46, 209, 0.5);
}

.filters-card,
.table-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 16px;
  margin-bottom: 24px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.filters-card :deep(.ant-card-body) {
  padding: 24px;
}

.table-card :deep(.ant-card-body) {
  padding: 0;
}

.search-input,
.filter-select {
  width: 100%;
}

.search-input :deep(.ant-input) {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(114, 46, 209, 0.3);
  color: rgba(255, 255, 255, 0.9);
}

.search-input :deep(.ant-input):focus {
  border-color: #722ed1;
  box-shadow: 0 0 0 2px rgba(114, 46, 209, 0.2);
}

.search-input :deep(.ant-input)::placeholder {
  color: rgba(255, 255, 255, 0.5);
}

.filter-select :deep(.ant-select-selector) {
  background: rgba(255, 255, 255, 0.05) !important;
  border: 1px solid rgba(114, 46, 209, 0.3) !important;
  color: rgba(255, 255, 255, 0.9) !important;
}

.filter-select :deep(.ant-select-selector):hover {
  border-color: #722ed1 !important;
}

.filter-select :deep(.ant-select-selection-placeholder) {
  color: rgba(255, 255, 255, 0.5) !important;
}

.cv-table {
  background: transparent;
}

.cv-table :deep(.ant-table) {
  background: transparent;
  color: rgba(255, 255, 255, 0.9);
}

.cv-table :deep(.ant-table-thead > tr > th) {
  background: rgba(114, 46, 209, 0.1) !important;
  border-bottom: 1px solid rgba(114, 46, 209, 0.3) !important;
  color: rgba(255, 255, 255, 0.9) !important;
  font-weight: 600;
}

.cv-table :deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid rgba(114, 46, 209, 0.1) !important;
  color: rgba(255, 255, 255, 0.8) !important;
}

.cv-table :deep(.ant-table-tbody > tr:hover > td) {
  background: rgba(114, 46, 209, 0.1) !important;
}

.cv-table :deep(.ant-table-tbody > tr) {
  transition: all 0.3s ease;
}

.cv-table :deep(.ant-pagination) {
  padding: 16px 24px;
  background: rgba(114, 46, 209, 0.05);
  border-top: 1px solid rgba(114, 46, 209, 0.2);
}

.cv-table :deep(.ant-pagination-item) {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(114, 46, 209, 0.3);
}

.cv-table :deep(.ant-pagination-item a) {
  color: rgba(255, 255, 255, 0.8);
}

.cv-table :deep(.ant-pagination-item-active) {
  background: #722ed1;
  border-color: #722ed1;
}

.cv-table :deep(.ant-pagination-item-active a) {
  color: white;
}

.cv-table :deep(.ant-pagination-prev),
.cv-table :deep(.ant-pagination-next) {
  color: rgba(255, 255, 255, 0.8);
}

.cv-table :deep(.ant-pagination-prev:hover),
.cv-table :deep(.ant-pagination-next:hover) {
  color: #b37feb;
}

/* Score Circle */
.score-circle-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  min-height: 100px;
  padding: 10px 0;
}

.score-text {
  position: absolute;
  font-size: 16px;
  font-weight: 700;
  line-height: 80px;
  width: 80px;
  text-align: center;
  pointer-events: none;
}

/* Responsive */
@media (max-width: 768px) {
  .dashboard-header {
    flex-direction: column;
  }

  .dashboard-title {
    font-size: 2rem;
  }

  .add-cv-button {
    width: 100%;
  }
}
</style>
