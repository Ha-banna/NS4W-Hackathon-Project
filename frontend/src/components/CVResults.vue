<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  Card,
  Button,
  Typography,
  Divider,
  Tag,
  Space,
  message
} from 'ant-design-vue'
import {
  ArrowLeftOutlined,
  FileTextOutlined,
  CheckCircleOutlined,
  CloseCircleOutlined,
  ExclamationCircleOutlined
} from '@ant-design/icons-vue'
import ScoreCircle from './ScoreCircle.vue'
import apiClient from '../api/axios'

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

interface InterviewQuestion {
  skill: string
  claimedLevel: string
  evidenceLevel: string
  overclaim: boolean
  rationale: string
  theoretical: string[]
  practical: string[]
  debugging: string[]
  focusAreas: string[]
}

interface CVData {
  id: string
  name: string
  email: string
  uploadedDate: string
  overallScore: number
  categories: Category[]
  interviewQuestions: InterviewQuestion[]
  pdfUrl: string
}

// Mock data - replace with API call
const cvData = ref<CVData | null>(null)
const loading = ref(true)

const transformAPIDataToCategories = (apiData: any): Category[] => {
  const categories: Category[] = []
  let itemId = 1

  // Skill Evidence Category
  if (apiData.skill_evidence?.skills) {
    const skillItems: CVItem[] = []
    const skills = apiData.skill_evidence.skills

    for (const [skillName, skillData] of Object.entries(skills)) {
      const skill = skillData as any
      if (skill.status === 'supported' && !skill.fake) {
        const confidence = Math.round((skill.confidence || 0) * 100)
        skillItems.push({
          id: String(itemId++),
          name: skillName,
          value: skill.evidence?.length
            ? `${skill.evidence.length} evidence(s) found`
            : 'No evidence',
          authenticityScore: confidence
        })
      }
    }

    if (skillItems.length > 0) {
      categories.push({
        name: 'Skill Evidence',
        items: skillItems
      })
    }
  }

  // Project Authenticity Category
  if (apiData.projects_authenticity?.repos) {
    const projectItems: CVItem[] = []
    const repos = apiData.projects_authenticity.repos

    for (const [repoName, repoData] of Object.entries(repos)) {
      const repo = repoData as any
      projectItems.push({
        id: String(itemId++),
        name: repoName.split('/').pop() || repoName,
        value: repo.description || 'No description',
        authenticityScore: Math.round(repo.authenticity_score || 0)
      })
    }

    if (projectItems.length > 0) {
      categories.push({
        name: 'Project Authenticity',
        items: projectItems
      })
    }
  }

  // Skill Inflation Category
  if (apiData.skill_inflation?.skills) {
    const inflationItems: CVItem[] = []
    const skills = apiData.skill_inflation.skills

    for (const [skillName, skillData] of Object.entries(skills)) {
      const skill = skillData as any
      if (skill.overclaim) {
        inflationItems.push({
          id: String(itemId++),
          name: skillName,
          value: `Claimed: ${skill.claimed_level || 'unknown'}, Observed: ${skill.observed_level || 'unknown'}`,
          authenticityScore: Math.max(0, 100 - (skill.severity || 0) * 20)
        })
      }
    }

    if (inflationItems.length > 0) {
      categories.push({
        name: 'Skill Inflation Detection',
        items: inflationItems
      })
    }
  }

  return categories
}

const transformInterviewQuestions = (apiData: any): InterviewQuestion[] => {
  const questions: InterviewQuestion[] = []
  
  if (apiData.interview_questions?.skills) {
    const skills = apiData.interview_questions.skills
    
    for (const [skillName, skillData] of Object.entries(skills)) {
      const skill = skillData as any
      questions.push({
        skill: skillName,
        claimedLevel: skill.claimed_level || 'unspecified',
        evidenceLevel: skill.evidence_level || 'none',
        overclaim: skill.overclaim || false,
        rationale: skill.rationale || '',
        theoretical: skill.theoretical || [],
        practical: skill.practical || [],
        debugging: skill.debugging || [],
        focusAreas: skill.focus_areas || []
      })
    }
  }
  
  return questions
}

const loadCVData = async () => {
  const cvId = route.params.id as string
  loading.value = true

  try {
    // Fetch all CVs and find the one matching the ID
    const response = await apiClient.get(`/dashboard/cv-result/${cvId}`)
    const cv = response.data;
    console.log(cv)
    if (!cv) {
      message.error('CV not found')
      router.push('/dashboard')
      return
    }

    const candidate = cv.cv?.candidate || {}
    const overallScore = Math.round(cv.projects_authenticity?.overall_authenticity_score || 0)
    const cvIdStr = String(cv._id)
    
    // Build PDF URL
    const baseURL = import.meta.env.VITE_BACKEND_URL || 'http://127.0.0.1:8000'
    const pdfUrl = `${baseURL}/dashboard/cv-pdf/${cvIdStr}`

    cvData.value = {
      id: cvIdStr,
      name: candidate.full_name || 'Unknown',
      email: candidate.contact?.email || '',
      uploadedDate: cv.cv?.meta?.last_updated || new Date().toISOString().split('T')[0],
      overallScore: overallScore,
      categories: transformAPIDataToCategories(cv),
      interviewQuestions: transformInterviewQuestions(cv),
      pdfUrl: pdfUrl
    }
  } catch (error: any) {
    console.error('Error fetching CV data:', error)
    message.error('Failed to load CV data. Please try again later.')
    router.push('/dashboard')
  } finally {
    loading.value = false
  }
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
          <Button type="text" size="large" class="back-button" @click="router.push('/dashboard')">
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
            <iframe 
              v-if="cvData.pdfUrl"
              :src="cvData.pdfUrl" 
              class="pdf-viewer"
              type="application/pdf"
            ></iframe>
            <div v-else class="cv-placeholder">
              <FileTextOutlined class="cv-icon" />
              <Paragraph class="cv-placeholder-text">
                CV Document Not Available
              </Paragraph>
            </div>
          </div>
        </Card>

        <!-- Interview Questions Card -->
        <Card v-if="cvData.interviewQuestions && cvData.interviewQuestions.length > 0" class="interview-questions-card">
          <Title :level="4" class="section-title">Recommended Interview Questions</Title>
          <div class="interview-questions-container">
            <div 
              v-for="(questionSet, index) in cvData.interviewQuestions" 
              :key="index"
              class="question-set"
            >
              <div class="question-set-header">
                <Title :level="5" class="skill-title">{{ questionSet.skill }}</Title>
                <div class="skill-metadata">
                  <Space size="small" wrap>
                    <Tag :color="questionSet.overclaim ? 'red' : 'green'">
                      {{ questionSet.overclaim ? 'Overclaim Detected' : 'Authentic' }}
                    </Tag>
                    <Tag>Claimed: {{ questionSet.claimedLevel }}</Tag>
                    <Tag>Evidence: {{ questionSet.evidenceLevel }}</Tag>
                  </Space>
                </div>
                <Text v-if="questionSet.rationale" type="secondary" class="rationale-text">
                  {{ questionSet.rationale }}
                </Text>
              </div>

              <div class="questions-content">
                <div v-if="questionSet.theoretical && questionSet.theoretical.length > 0" class="question-category">
                  <Title :level="5" class="category-title">
                    <CheckCircleOutlined /> Theoretical Questions
                  </Title>
                  <ul class="question-list">
                    <li v-for="(question, qIndex) in questionSet.theoretical" :key="qIndex" class="question-item">
                      {{ question }}
                    </li>
                  </ul>
                </div>

                <div v-if="questionSet.practical && questionSet.practical.length > 0" class="question-category">
                  <Title :level="5" class="category-title">
                    <CheckCircleOutlined /> Practical Questions
                  </Title>
                  <ul class="question-list">
                    <li v-for="(question, qIndex) in questionSet.practical" :key="qIndex" class="question-item">
                      {{ question }}
                    </li>
                  </ul>
                </div>

                <div v-if="questionSet.debugging && questionSet.debugging.length > 0" class="question-category">
                  <Title :level="5" class="category-title">
                    <CheckCircleOutlined /> Debugging Questions
                  </Title>
                  <ul class="question-list">
                    <li v-for="(question, qIndex) in questionSet.debugging" :key="qIndex" class="question-item">
                      {{ question }}
                    </li>
                  </ul>
                </div>

                <div v-if="questionSet.focusAreas && questionSet.focusAreas.length > 0" class="question-category">
                  <Title :level="5" class="category-title">
                    <ExclamationCircleOutlined /> Focus Areas
                  </Title>
                  <div class="focus-areas">
                    <Tag 
                      v-for="(area, aIndex) in questionSet.focusAreas" 
                      :key="aIndex"
                      color="purple"
                      class="focus-area-tag"
                    >
                      {{ area }}
                    </Tag>
                  </div>
                </div>
              </div>

              <Divider v-if="index < cvData.interviewQuestions.length - 1" />
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
            <div v-for="(category, categoryIndex) in cvData.categories" :key="categoryIndex" class="category-section">
              <Title :level="5" class="category-title">
                {{ category.name }}
              </Title>

              <div class="category-items">
                <div v-for="item in category.items" :key="item.id" class="category-item">
                  <div class="item-content">
                    <div class="item-header">
                      <Text strong class="item-name">{{ item.name }}</Text>
                      <ScoreCircle :score="item.authenticityScore" :size="60" />
                    </div>
                    <Text class="item-value">{{ item.value }}</Text>
                    <div class="item-footer">
                      <Tag :color="getScoreColor(item.authenticityScore)" class="authenticity-tag">
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
  overflow: hidden;
}

.pdf-viewer {
  width: 100%;
  height: 800px;
  border: none;
  background: rgba(255, 255, 255, 0.95);
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

.interview-questions-card {
  margin-top: 24px;
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 16px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
}

.interview-questions-card :deep(.ant-card-body) {
  padding: 32px;
}

.interview-questions-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.question-set {
  padding: 20px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(114, 46, 209, 0.15);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.question-set:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(114, 46, 209, 0.3);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(114, 46, 209, 0.2);
}

.question-set-header {
  margin-bottom: 20px;
}

.skill-title {
  margin-bottom: 12px !important;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 1.2rem;
}

.skill-metadata {
  margin-bottom: 12px;
}

.rationale-text {
  display: block;
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 0.9rem;
  font-style: italic;
  line-height: 1.5;
}

.questions-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.question-category {
  padding: 16px;
  background: rgba(255, 255, 255, 0.02);
  border-radius: 8px;
  border-left: 3px solid rgba(114, 46, 209, 0.5);
}

.category-title {
  margin-bottom: 12px !important;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 600;
  font-size: 1rem;
  display: flex;
  align-items: center;
  gap: 8px;
}

.question-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.question-item {
  padding: 12px 16px;
  margin-bottom: 8px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 6px;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.6;
  position: relative;
  padding-left: 32px;
  transition: all 0.2s ease;
}

.question-item::before {
  content: "•";
  position: absolute;
  left: 16px;
  color: #b37feb;
  font-weight: bold;
  font-size: 1.2rem;
}

.question-item:hover {
  background: rgba(255, 255, 255, 0.08);
  transform: translateX(4px);
}

.focus-areas {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.focus-area-tag {
  margin: 0;
  padding: 4px 12px;
  font-size: 0.85rem;
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