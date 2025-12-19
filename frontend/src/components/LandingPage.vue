<script setup lang="ts">
import { 
  Card, 
  Row, 
  Col, 
  Typography, 
  Button, 
  Space, 
  Steps
} from 'ant-design-vue'

import { useRouter } from 'vue-router'

const router = useRouter()
import {
  SearchOutlined,
  CheckCircleOutlined,
  BarChartOutlined,
  BulbOutlined,
  DashboardOutlined,
  RocketOutlined
} from '@ant-design/icons-vue'

const { Title, Paragraph } = Typography

const features = [
  {
    title: 'Skill Evidence Mapping',
    description: 'Map every skill in the CV to the evidence found on Github or LinkedIn',
    icon: SearchOutlined,
    gradient: 'linear-gradient(135deg, #722ed1 0%, #b37feb 100%)'
  },
  {
    title: 'Project Authenticity Score',
    description: 'Detects Copy-paste projects, Tutorial Clones or AI generated code',
    icon: CheckCircleOutlined,
    gradient: 'linear-gradient(135deg, #b37feb 0%, #722ed1 100%)'
  },
  {
    title: 'Skill Inflation Detection',
    description: 'LLM classifies claims as Beginner/Intermediate/Expert. Compares claim wording vs actual usage',
    icon: BarChartOutlined,
    gradient: 'linear-gradient(135deg, #722ed1 0%, #b37feb 100%)'
  },
  {
    title: 'Personalized Interview Questions',
    description: 'Generated based on CV claims, weak points. Each skill will have theoretical questions, practical scenarios, and debugging questions',
    icon: BulbOutlined,
    gradient: 'linear-gradient(135deg, #b37feb 0%, #722ed1 100%)'
  },
  {
    title: 'Candidate Comparison Dashboard',
    description: 'A dashboard showing the final score for the evaluation with skill confidence, evidence count, red flags, and interview readiness score',
    icon: DashboardOutlined,
    gradient: 'linear-gradient(135deg, #722ed1 0%, #b37feb 100%)'
  }
]

const userFlowSteps = [
  {
    title: 'Login',
    description: 'Employer logs into the platform'
  },
  {
    title: 'Upload CV',
    description: 'Upload candidate CV for evaluation'
  },
  {
    title: 'Processing',
    description: 'AI analyzes CV, GitHub, and LinkedIn data'
  },
  {
    title: 'Results',
    description: 'View comprehensive evaluation report'
  }
]
</script>

<template>
  <div class="landing-page">
    <!-- Animated Background Elements -->
    <div class="animated-bg">
      <div class="bg-circle circle-1"></div>
      <div class="bg-circle circle-2"></div>
      <div class="bg-circle circle-3"></div>
    </div>

    <!-- Hero Section -->
    <section class="hero-section">
      <div class="hero-content">
        <div class="hero-badge">
          <RocketOutlined /> AI-Powered
        </div>
        <Title :level="1" class="hero-title">
          <span class="title-letter" style="--delay: 0s">B</span>
          <span class="title-letter" style="--delay: 0.1s">U</span>
          <span class="title-letter" style="--delay: 0.2s">S</span>
          <span class="title-letter" style="--delay: 0.3s">T</span>
          <span class="title-letter" style="--delay: 0.4s">E</span>
          <span class="title-letter" style="--delay: 0.5s">D</span>
        </Title>
        <Title :level="2" class="hero-subtitle">
          AI-Powered CV Evaluation Platform
        </Title>
        <Paragraph class="hero-description">
          Evaluate candidates intelligently with automated CV analysis, skill verification, 
          and authenticity detection powered by AI and LLM technology.
        </Paragraph>
        <Space size="large" class="hero-buttons">
          <Button type="primary" size="large" class="cta-primary" @click="router.push('/dashboard')">
            Get Started
          </Button>
          <Button size="large" class="cta-secondary" @click="router.push('/dashboard')">
            Login
          </Button>
        </Space>
      </div>
      <div class="hero-abstract">
        <svg class="abstract-svg" viewBox="0 0 600 600" xmlns="http://www.w3.org/2000/svg">
          <!-- Geometric shapes -->
          <polygon points="300,50 450,200 300,350 150,200" fill="rgba(114, 46, 209, 0.3)" stroke="#722ed1" stroke-width="2" class="shape-anim-1"/>
          <circle cx="150" cy="400" r="80" fill="rgba(179, 127, 235, 0.2)" stroke="#b37feb" stroke-width="2" class="shape-anim-2"/>
          <rect x="400" y="300" width="120" height="120" fill="rgba(114, 46, 209, 0.25)" stroke="#722ed1" stroke-width="2" transform="rotate(45 460 360)" class="shape-anim-3"/>
          <path d="M 100 200 L 200 100 L 300 200 L 200 300 Z" fill="rgba(179, 127, 235, 0.2)" stroke="#b37feb" stroke-width="2" class="shape-anim-4"/>
          <polygon points="450,450 550,350 550,550 450,550" fill="rgba(114, 46, 209, 0.3)" stroke="#722ed1" stroke-width="2" class="shape-anim-5"/>
          <!-- Connecting lines -->
          <line x1="300" y1="200" x2="150" y2="400" stroke="rgba(114, 46, 209, 0.4)" stroke-width="1" class="line-anim-1"/>
          <line x1="450" y1="200" x2="400" y2="300" stroke="rgba(179, 127, 235, 0.4)" stroke-width="1" class="line-anim-2"/>
          <line x1="200" y1="300" x2="450" y2="450" stroke="rgba(114, 46, 209, 0.3)" stroke-width="1" class="line-anim-3"/>
        </svg>
      </div>
    </section>

    <!-- User Flow Section -->
    <section class="section user-flow-section">
      <div class="section-container">
        <div class="section-header">
          <Title :level="2" class="section-title">How It Works</Title>
          <Paragraph class="section-description">
            The employer will login, the tool will allow him to upload a CV for possible employees. 
            The CV will then get processed and the employer will then get a result.
          </Paragraph>
        </div>
        <div class="flow-steps-wrapper">
          <Steps :items="userFlowSteps" class="flow-steps" />
        </div>
      </div>
    </section>

    <!-- Features Section -->
    <section class="section features-section">
      <div class="section-container">
        <div class="section-header">
          <Title :level="2" class="section-title">Main Features</Title>
          <Paragraph class="section-description">
            Comprehensive CV analysis powered by AI and machine learning
          </Paragraph>
        </div>
        <Row :gutter="[32, 32]" class="features-grid">
          <Col 
            v-for="(feature, index) in features" 
            :key="index"
            :xs="24" 
            :sm="12" 
            :md="8"
            :lg="8"
          >
            <Card 
              :hoverable="true" 
              class="feature-card"
              :style="{ '--gradient': feature.gradient }"
            >
              <div class="feature-icon-wrapper">
                <div class="feature-icon">
                  <component :is="feature.icon" />
                </div>
              </div>
              <Title :level="4" class="feature-title">{{ feature.title }}</Title>
              <Paragraph class="feature-description">{{ feature.description }}</Paragraph>
            </Card>
          </Col>
        </Row>
      </div>
    </section>

    <!-- CTA Section -->
    <section class="section cta-section">
      <div class="section-container">
        <Card class="cta-card">
          <div class="cta-content">
            <Title :level="2" class="cta-title">Ready to Transform Your Hiring Process?</Title>
            <Paragraph class="cta-description">
              Start evaluating candidates with AI-powered insights today
            </Paragraph>
            <Button type="primary" size="large" class="cta-button" @click="router.push('/dashboard')">
              Get Started Now
            </Button>
          </div>
        </Card>
      </div>
    </section>
  </div>
</template>

<style scoped>
.landing-page {
  width: 100%;
  min-height: 100vh;
  background: transparent;
  position: relative;
  overflow-x: hidden;
  font-family: 'Space Grotesk', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
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

/* Hero Section */
.hero-section {
  padding: 120px 20px 80px;
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: center;
  gap: 80px;
  flex-wrap: wrap;
  position: relative;
  z-index: 1;
}

.hero-content {
  flex: 1;
  min-width: 300px;
  animation: fadeInUp 0.8s ease-out;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 20px;
  background: rgba(114, 46, 209, 0.1);
  border: 1px solid rgba(114, 46, 209, 0.3);
  border-radius: 50px;
  color: #722ed1;
  font-weight: 600;
  font-size: 0.9rem;
  margin-bottom: 24px;
  backdrop-filter: blur(10px);
}

.hero-title {
  font-size: 6rem;
  font-weight: 900;
  margin-bottom: 16px;
  line-height: 1.1;
  letter-spacing: -2px;
  display: flex;
  align-items: center;
  gap: 4px;
  position: relative;
}

.title-letter {
  display: inline-block;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 50%, #722ed1 100%);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: 
    letterFloat 3s ease-in-out infinite var(--delay),
    gradientShift 4s ease infinite var(--delay),
    letterGlow 2s ease-in-out infinite var(--delay);
  position: relative;
  filter: drop-shadow(0 0 10px rgba(114, 46, 209, 0.5));
  transition: transform 0.3s ease;
}

.title-letter:hover {
  transform: translateY(-10px) scale(1.1);
  filter: drop-shadow(0 0 20px rgba(114, 46, 209, 0.8));
}

@keyframes letterFloat {
  0%, 100% {
    transform: translateY(0) rotate(0deg);
  }
  50% {
    transform: translateY(-8px) rotate(2deg);
  }
}

@keyframes gradientShift {
  0%, 100% {
    background-position: 0% 50%;
  }
  50% {
    background-position: 100% 50%;
  }
}

@keyframes letterGlow {
  0%, 100% {
    filter: drop-shadow(0 0 10px rgba(114, 46, 209, 0.5));
    opacity: 1;
  }
  50% {
    filter: drop-shadow(0 0 20px rgba(179, 127, 235, 0.8));
    opacity: 0.9;
  }
}

.hero-subtitle {
  font-size: 1.75rem;
  font-weight: 600;
  margin-bottom: 24px;
  color: #722ed1;
  letter-spacing: -0.5px;
}

.hero-description {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.7);
  margin-bottom: 40px;
  line-height: 1.8;
  max-width: 600px;
}

.hero-buttons {
  margin-top: 32px;
}

.cta-primary {
  height: 56px;
  padding: 0 40px;
  font-size: 1.1rem;
  font-weight: 600;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  border: none;
  box-shadow: 0 8px 24px rgba(114, 46, 209, 0.4);
  transition: all 0.3s ease;
}

.cta-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(114, 46, 209, 0.5);
}

.cta-secondary {
  height: 56px;
  padding: 0 40px;
  font-size: 1.1rem;
  font-weight: 600;
  background: transparent;
  border: 2px solid #722ed1;
  color: #722ed1;
  transition: all 0.3s ease;
}

.cta-secondary:hover {
  background: rgba(114, 46, 209, 0.1);
  transform: translateY(-2px);
}

/* Hero Abstract Design */
.hero-abstract {
  flex: 1;
  min-width: 300px;
  position: relative;
  height: 500px;
  animation: fadeInRight 0.8s ease-out;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.abstract-svg {
  width: 100%;
  height: 100%;
  max-width: 600px;
  max-height: 600px;
  filter: drop-shadow(0 0 20px rgba(114, 46, 209, 0.3));
}

.shape-anim-1 {
  animation: shapeFloat1 8s ease-in-out infinite;
  transform-origin: center;
}

.shape-anim-2 {
  animation: shapeFloat2 10s ease-in-out infinite;
  transform-origin: center;
}

.shape-anim-3 {
  animation: shapeFloat3 12s ease-in-out infinite;
  transform-origin: center;
}

.shape-anim-4 {
  animation: shapeFloat4 9s ease-in-out infinite;
  transform-origin: center;
}

.shape-anim-5 {
  animation: shapeFloat5 11s ease-in-out infinite;
  transform-origin: center;
}

.line-anim-1 {
  animation: linePulse 3s ease-in-out infinite;
  stroke-dasharray: 5, 5;
}

.line-anim-2 {
  animation: linePulse 3s ease-in-out infinite 1s;
  stroke-dasharray: 5, 5;
}

.line-anim-3 {
  animation: linePulse 3s ease-in-out infinite 2s;
  stroke-dasharray: 5, 5;
}

@keyframes shapeFloat1 {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 0.3;
  }
  50% {
    transform: translate(20px, -30px) rotate(180deg);
    opacity: 0.5;
  }
}

@keyframes shapeFloat2 {
  0%, 100% {
    transform: translate(0, 0) scale(1);
    opacity: 0.2;
  }
  50% {
    transform: translate(-15px, 25px) scale(1.2);
    opacity: 0.4;
  }
}

@keyframes shapeFloat3 {
  0%, 100% {
    transform: rotate(45deg) translate(0, 0);
    opacity: 0.25;
  }
  50% {
    transform: rotate(225deg) translate(30px, 20px);
    opacity: 0.45;
  }
}

@keyframes shapeFloat4 {
  0%, 100% {
    transform: translate(0, 0) rotate(0deg);
    opacity: 0.2;
  }
  50% {
    transform: translate(25px, 15px) rotate(90deg);
    opacity: 0.4;
  }
}

@keyframes shapeFloat5 {
  0%, 100% {
    transform: translate(0, 0);
    opacity: 0.3;
  }
  50% {
    transform: translate(-20px, -25px);
    opacity: 0.5;
  }
}

@keyframes linePulse {
  0%, 100% {
    opacity: 0.3;
    stroke-dashoffset: 0;
  }
  50% {
    opacity: 0.6;
    stroke-dashoffset: 10;
  }
}

/* Section Styles */
.section {
  padding: 100px 20px;
  position: relative;
  z-index: 1;
}

.section-container {
  max-width: 1200px;
  margin: 0 auto;
}

.section-header {
  text-align: center;
  margin-bottom: 64px;
}

.section-title {
  font-size: 3rem;
  font-weight: 800;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  letter-spacing: -1px;
}

.section-description {
  font-size: 1.2rem;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 auto;
  max-width: 700px;
  line-height: 1.8;
}

/* User Flow */
.user-flow-section {
  background: transparent;
}

.flow-steps-wrapper {
  max-width: 900px;
  margin: 0 auto;
  padding: 40px;
  background: rgba(114, 46, 209, 0.05);
  border-radius: 20px;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.1);
}

.flow-steps {
  width: 100%;
}

/* Features */
.features-grid {
  margin-top: 48px;
}

.feature-card {
  height: 100%;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: rgba(255, 255, 255, 0.02);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.2);
  border-radius: 16px;
  overflow: hidden;
  position: relative;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4px;
  background: var(--gradient);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.4s ease;
}

.feature-card:hover {
  transform: translateY(-12px);
  box-shadow: 0 20px 40px rgba(114, 46, 209, 0.3);
  border-color: rgba(114, 46, 209, 0.4);
}

.feature-card:hover::before {
  transform: scaleX(1);
}

.feature-icon-wrapper {
  display: flex;
  justify-content: center;
  margin-bottom: 24px;
}

.feature-icon {
  font-size: 3rem;
  width: 100px;
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--gradient);
  border-radius: 20px;
  box-shadow: 0 8px 24px rgba(114, 46, 209, 0.3);
  transition: transform 0.4s ease;
  color: white;
}

.feature-card:hover .feature-icon {
  transform: scale(1.1) rotate(5deg);
}

.feature-title {
  text-align: center;
  margin-bottom: 16px;
  font-weight: 700;
  color: rgba(255, 255, 255, 0.9);
  letter-spacing: -0.3px;
}

.feature-description {
  text-align: center;
  color: rgba(255, 255, 255, 0.6);
  margin-bottom: 0;
  line-height: 1.7;
}

/* CTA Section */
.cta-section {
  padding: 120px 20px;
}

.cta-card {
  text-align: center;
  background: linear-gradient(135deg, #722ed1 0%, #b37feb 100%);
  border: none;
  border-radius: 24px;
  overflow: hidden;
  position: relative;
  box-shadow: 0 20px 60px rgba(114, 46, 209, 0.4);
}

.cta-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23ffffff' fill-opacity='0.05'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E");
  opacity: 0.3;
}

.cta-card :deep(.ant-card-body) {
  padding: 80px 40px;
  position: relative;
  z-index: 1;
}

.cta-content {
  position: relative;
  z-index: 2;
}

.cta-title {
  color: white;
  margin-bottom: 20px;
  font-size: 2.5rem;
  font-weight: 800;
  letter-spacing: -0.5px;
}

.cta-description {
  color: rgba(255, 255, 255, 0.9);
  font-size: 1.2rem;
  margin-bottom: 40px;
}

.cta-button {
  height: 56px;
  padding: 0 50px;
  font-size: 1.1rem;
  font-weight: 600;
  background: white;
  color: #722ed1;
  border: none;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.cta-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.3);
  background: #f0f0f0;
}

/* Animations */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes fadeInRight {
  from {
    opacity: 0;
    transform: translateX(30px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* Text colors for dark mode */
.hero-description,
.section-description,
.feature-description {
  color: rgba(255, 255, 255, 0.7);
}

.hero-subtitle {
  color: #b37feb;
}

/* Responsive */
@media (max-width: 768px) {
  .hero-title {
    font-size: 3.5rem;
  }
  
  .hero-section {
    flex-direction: column;
    padding: 60px 20px;
    gap: 40px;
  }
  
  .section {
    padding: 60px 20px;
  }
  
  .section-title {
    font-size: 2rem;
  }

  .hero-abstract {
    height: 400px;
  }

  .flow-steps-wrapper {
    padding: 20px;
  }
}
</style>
