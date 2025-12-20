<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Card,
  Button,
  Typography,
  Divider,
  Tag,
  Space
} from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import ScoreCircle from './ScoreCircle.vue'

const router = useRouter()
const route = useRoute()
const { Title, Paragraph, Text } = Typography

// Mock CV data - in real app, fetch based on route params
interface CVItem {
  id: string
  name: string
  value: string
  authenticityScore: number
}

interface Category {
  name: string
  items: CVItem[]
}

interface CVData {
  id: string
  name: string
  email: string
  uploadedDate: string
  overallScore: number
  categories: Category[]
}

// Mock data - replace with API call
const cvData = ref<CVData | null>(null)
const loading = ref(true)

// Generate mock dynamic categories based on CV ID
const generateMockCategories = (cvId: string): Category[] => {
  // Different CVs can have different categories
  const categoryTemplates: Record<string, Category[]> = {
    '1': [
      {
        name: 'Technical Skills',
        items: [
          { id: '1', name: 'React', value: 'Expert level with 5+ years experience', authenticityScore: 92 },
          { id: '2', name: 'TypeScript', value: 'Advanced proficiency, used in 10+ projects', authenticityScore: 88 },
          { id: '3', name: 'Node.js', value: 'Strong backend development skills', authenticityScore: 85 },
          { id: '4', name: 'Redux', value: 'State management expertise', authenticityScore: 78 }
        ]
      },
      {
        name: 'Projects',
        items: [
          { id: '5', name: 'E-commerce Platform', value: 'Full-stack application with payment integration', authenticityScore: 90 },
          { id: '6', name: 'Task Management App', value: 'React-based collaborative tool', authenticityScore: 82 },
          { id: '7', name: 'API Gateway', value: 'Microservices architecture implementation', authenticityScore: 75 }
        ]
      },
      {
        name: 'Education',
        items: [
          { id: '8', name: 'Computer Science Degree', value: 'Bachelor of Science, 2018-2022', authenticityScore: 95 },
          { id: '9', name: 'React Certification', value: 'Meta React Developer Certificate', authenticityScore: 88 }
        ]
      },
      {
        name: 'Work Experience',
        items: [
          { id: '10', name: 'Senior Developer', value: 'TechCorp Inc., 2020-Present', authenticityScore: 92 },
          { id: '11', name: 'Junior Developer', value: 'StartupXYZ, 2018-2020', authenticityScore: 85 }
        ]
      }
    ],
    '2': [
      {
        name: 'Frontend Skills',
        items: [
          { id: '1', name: 'Vue.js', value: 'Expert in Vue 3 Composition API', authenticityScore: 95 },
          { id: '2', name: 'JavaScript', value: 'ES6+ proficiency', authenticityScore: 90 },
          { id: '3', name: 'CSS/SCSS', value: 'Advanced styling and animations', authenticityScore: 88 }
        ]
      },
      {
        name: 'Design Tools',
        items: [
          { id: '4', name: 'Figma', value: 'UI/UX design experience', authenticityScore: 80 },
          { id: '5', name: 'Adobe XD', value: 'Prototyping skills', authenticityScore: 75 }
        ]
      },
      {
        name: 'Projects',
        items: [
          { id: '6', name: 'Portfolio Website', value: 'Personal portfolio with animations', authenticityScore: 88 },
          { id: '7', name: 'Dashboard UI', value: 'Admin dashboard component library', authenticityScore: 85 }
        ]
      }
    ],
    '3': [
      {
        name: 'Backend Skills',
        items: [
          { id: '1', name: 'Python', value: 'Advanced Python programming', authenticityScore: 90 },
          { id: '2', name: 'Django', value: 'Full-stack framework expertise', authenticityScore: 88 },
          { id: '3', name: 'PostgreSQL', value: 'Database design and optimization', authenticityScore: 85 }
        ]
      },
      {
        name: 'DevOps',
        items: [
          { id: '4', name: 'Docker', value: 'Containerization experience', authenticityScore: 82 },
          { id: '5', name: 'CI/CD', value: 'GitHub Actions, Jenkins', authenticityScore: 78 }
        ]
      }
    ]
  }

  // Default categories if CV ID not found
  return categoryTemplates[cvId] || [
    {
      name: 'Skills',
      items: [
        { id: '1', name: 'General Skills', value: 'Various technical skills', authenticityScore: 75 }
      ]
    }
  ]
}

const loadCVData = () => {
  const cvId = route.params.id as string
  
  // Mock CV data - replace with API call
  const mockCVs: Record<string, Omit<CVData, 'categories'>> = {
    '1': {
      id: '1',
      name: 'John Doe',
      email: 'john.doe@example.com',
      uploadedDate: '2024-01-15',
      overallScore: 85
    },
    '2': {
      id: '2',
      name: 'Jane Smith',
      email: 'jane.smith@example.com',
      uploadedDate: '2024-01-14',
      overallScore: 92
    },
    '3': {
      id: '3',
      name: 'Bob Johnson',
      email: 'bob.johnson@example.com',
      uploadedDate: '2024-01-13',
      overallScore: 68
    }
  }

  const baseData = mockCVs[cvId] || {
    id: cvId,
    name: 'Unknown Candidate',
    email: 'unknown@example.com',
    uploadedDate: new Date().toISOString().split('T')[0],
    overallScore: 75
  }

  cvData.value = {
    ...baseData,
    categories: generateMockCategories(cvId)
  }

  loading.value = false
}

onMounted(() => {
  loadCVData()
})

const getScoreColor = (score: number) => {
  if (score >= 85) return '#52c41a'
  if (score >= 70) return '#faad14'
  return '#ff4d4f'
}

const getScoreLabel = (score: number) => {
  if (score >= 85) return 'High'
  if (score >= 70) return 'Medium'
  return 'Low'
}
</script>

<template>
  <div class="cv-results-page">
    <!-- Animated Background Elements -->
    <div class="animated-bg">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
    </div>

    <div class="results-container" v-if="!loading && cvData">
      <!-- Main Content Area -->
      <div class="main-content">
        <!-- Header -->
        <div class="page-header">
          <Button 
            type="text" 
            size="large" 
            class="back-button" 
            @click="router.push('/dashboard')"
          >
            <template #icon>
              <ArrowLeftOutlined />
            </template>
            Back to Dashboard
          </Button>
          <div class="header-content">
            <Title :level="2" class="page-title">
              <FileTextOutlined /> CV Evaluation Results
            </Title>
            <div class="candidate-info">
              <Space size="large" wrap>
                <div>
                  <Text type="secondary">Candidate:</Text>
                  <Text strong class="info-text">{{ cvData.name }}</Text>
                </div>
                <div>
                  <Text type="secondary">Email:</Text>
                  <Text strong class="info-text">{{ cvData.email }}</Text>
                </div>
                <div>
                  <Text type="secondary">Uploaded:</Text>
                  <Text strong class="info-text">{{ cvData.uploadedDate }}</Text>
                </div>
              </Space>
            </div>
          </div>
        </div>

        <!-- CV Preview Card -->
        <Card class="cv-preview-card">
          <Title :level="4" class="section-title">CV Document</Title>
          <div class="cv-preview">
            <div class="cv-placeholder">
              <FileTextOutlined class="cv-icon" />
              <Paragraph class="cv-placeholder-text">
                CV Document Preview
              </Paragraph>
              <Text type="secondary">PDF viewer would be integrated here</Text>
            </div>
          </div>
        </Card>
      </div>

      <!-- Results Sidebar -->
      <div class="results-sidebar">
        <Card class="sidebar-card">
          <div class="sidebar-header">
            <Title :level="4" class="sidebar-title">Evaluation Results</Title>
            <div class="overall-score">
              <Text type="secondary" class="overall-label">Overall Score</Text>
              <ScoreCircle :score="cvData.overallScore" />
            </div>
          </div>

          <Divider />

          <!-- Dynamic Categories -->
          <div class="categories-container">
            <div 
              v-for="(category, categoryIndex) in cvData.categories" 
              :key="categoryIndex"
              class="category-section"
            >
              <Title :level="5" class="category-title">
                {{ category.name }}
              </Title>
              
              <div class="category-items">
                <div 
                  v-for="item in category.items" 
                  :key="item.id"
                  class="category-item"
                >
                  <div class="item-content">
                    <div class="item-header">
                      <Text strong class="item-name">{{ item.name }}</Text>
                      <ScoreCircle :score="item.authenticityScore" :size="60" />
                    </div>
                    <Text class="item-value">{{ item.value }}</Text>
                    <div class="item-footer">
                      <Tag 
                        :color="getScoreColor(item.authenticityScore)"
                        class="authenticity-tag"
                      >
                        {{ getScoreLabel(item.authenticityScore) }} Authenticity
                      </Tag>
                    </div>
                  </div>
                </div>
              </div>

              <Divider v-if="categoryIndex < cvData.categories.length - 1" />
            </div>
          </div>
        </Card>
      </div>
    </div>

    <!-- Loading State -->
    <div v-else class="loading-container">
      <Text>Loading CV data...</Text>
    </div>
  </div>
</template>

<style scoped>
.cv-results-page {
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

.results-container {
  max-width: 1600px;
  width: 100%;
  margin: 0 auto;
  position: relative;
  z-index: 1;
  display: flex;
  gap: 24px;
  align-items: flex-start;
}

.main-content {
  flex: 1;
  min-width: 0;
}

.results-sidebar {
  width: 450px;
  flex-shrink: 0;
  position: sticky;
  top: 20px;
}

.page-header {
  margin-bottom: 24px;
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
  text-align: left;
}

.page-title {
  margin-bottom: 16px !important;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  font-size: 2rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  gap: 12px;
}

.candidate-info {
  margin-top: 16px;
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border: 1px solid rgba(114, 46, 209, 0.2);
}

.info-text {
  color: rgba(255, 255, 255, 0.9);
  margin-left: 8px;
}

.cv-preview-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.cv-preview-card :deep(.ant-card-body) {
  padding: 32px;
}

.section-title {
  margin-bottom: 24px !important;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 1.5rem;
}

.cv-preview {
  min-height: 600px;
  background: rgba(255, 255, 255, 0.02);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.cv-placeholder {
  text-align: center;
  padding: 40px;
}

.cv-icon {
  font-size: 64px;
  color: rgba(114, 46, 209, 0.5);
  margin-bottom: 16px;
}

.cv-placeholder-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 1.2rem;
  margin-bottom: 8px;
}

.sidebar-card {
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.sidebar-card :deep(.ant-card-body) {
  padding: 24px;
}

.sidebar-header {
  margin-bottom: 16px;
}

.sidebar-title {
  margin-bottom: 16px !important;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 1.3rem;
}

.overall-score {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  background: rgba(114, 46, 209, 0.1);
  border-radius: 12px;
  margin-bottom: 16px;
}

.overall-label {
  margin-bottom: 12px;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.categories-container {
  max-height: calc(100vh - 400px);
  overflow-y: auto;
  padding-right: 8px;
}

.categories-container::-webkit-scrollbar {
  width: 6px;
}

.categories-container::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.05);
  border-radius: 3px;
}

.categories-container::-webkit-scrollbar-thumb {
  background: rgba(114, 46, 209, 0.5);
  border-radius: 3px;
}

.categories-container::-webkit-scrollbar-thumb:hover {
  background: rgba(114, 46, 209, 0.7);
}

.category-section {
  margin-bottom: 24px;
}

.category-title {
  margin-bottom: 16px !important;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 1.1rem;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(114, 46, 209, 0.2);
}

.category-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.category-item {
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(114, 46, 209, 0.15);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

.category-item:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(114, 46, 209, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(114, 46, 209, 0.2);
}

.item-content {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}

.item-name {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1rem;
  flex: 1;
}

.item-value {
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  line-height: 1.5;
}

.item-footer {
  display: flex;
  align-items: center;
  gap: 8px;
}

.authenticity-tag {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: 4px;
}

.loading-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
  color: rgba(255, 255, 255, 0.7);
}

/* Responsive */
@media (max-width: 1200px) {
  .results-container {
    flex-direction: column;
  }

  .results-sidebar {
    width: 100%;
    position: relative;
    top: 0;
  }

  .categories-container {
    max-height: none;
  }
}

@media (max-width: 768px) {
  .page-title {
    font-size: 1.5rem;
  }

  .candidate-info {
    flex-direction: column;
    align-items: flex-start;
  }

  .item-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
