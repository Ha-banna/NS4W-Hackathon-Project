<script setup lang="ts">
import { ref, computed, h } from 'vue'

import { useRouter } from 'vue-router'

const router = useRouter()
import {
  Card,
  Table,
  Input,
  Button,
  Space,
  Select,
  Tag,
  Typography,
  Row,
  Col,
  Progress
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

const { Title, Paragraph } = Typography

// Mock data - replace with actual API data
const cvData = ref([
  {
    key: '1',
    name: 'John Doe',
    email: 'john.doe@example.com',
    position: 'Senior Developer',
    score: 85,
    uploadedDate: '2024-01-15',
    skills: ['React', 'TypeScript', 'Node.js']
  },
  {
    key: '2',
    name: 'Jane Smith',
    email: 'jane.smith@example.com',
    position: 'Frontend Developer',
    score: 92,
    uploadedDate: '2024-01-14',
    skills: ['Vue', 'JavaScript', 'CSS']
  },
  {
    key: '3',
    name: 'Bob Johnson',
    email: 'bob.johnson@example.com',
    position: 'Full Stack Developer',
    score: 68,
    uploadedDate: '2024-01-13',
    skills: ['Python', 'Django', 'PostgreSQL']
  },
  {
    key: '4',
    name: 'Alice Williams',
    email: 'alice.williams@example.com',
    position: 'DevOps Engineer',
    score: 78,
    uploadedDate: '2024-01-12',
    skills: ['Docker', 'Kubernetes', 'AWS']
  },
  {
    key: '5',
    name: 'Charlie Brown',
    email: 'charlie.brown@example.com',
    position: 'Backend Developer',
    score: 88,
    uploadedDate: '2024-01-11',
    skills: ['Java', 'Spring Boot', 'MySQL']
  }
])

const searchText = ref('')
const positionFilter = ref<string | undefined>(undefined)
const dateRange = ref<[string, string] | null>(null)
const sortField = ref<string | undefined>(undefined)
const sortOrder = ref<'ascend' | 'descend' | undefined>(undefined)

// Get unique positions for filter
const positions = computed(() => {
  const unique = new Set(cvData.value.map(cv => cv.position))
  return Array.from(unique)
})

// Filtered and sorted data
const filteredData = computed(() => {
  let result = [...cvData.value]

  // Search filter
  if (searchText.value) {
    const search = searchText.value.toLowerCase()
    result = result.filter(cv =>
      cv.name.toLowerCase().includes(search) ||
      cv.email.toLowerCase().includes(search) ||
      cv.position.toLowerCase().includes(search) ||
      cv.skills.some(skill => skill.toLowerCase().includes(search))
    )
  }

  // Position filter
  if (positionFilter.value) {
    result = result.filter(cv => cv.position === positionFilter.value)
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
  // Handle add CV action
  console.log('Add CV clicked')
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
    title: 'Position',
    dataIndex: 'position',
    key: 'position',
    sorter: true,
    width: 180,
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
    customRender: () => {
      // @ts-ignore
      return h(Space, {}, () => [
        // @ts-ignore
        h(Button, { type: 'link', size: 'small' }, () => 'View')
      ])
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
  positionFilter.value = undefined
  dateRange.value = null
  sortField.value = undefined
  sortOrder.value = undefined
}
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
            <Select
              v-model:value="positionFilter"
              placeholder="Filter by Position"
              size="large"
              allow-clear
              class="filter-select"
            >
              <Select.Option v-for="position in positions" :key="position" :value="position">
                {{ position }}
              </Select.Option>
            </Select>
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
