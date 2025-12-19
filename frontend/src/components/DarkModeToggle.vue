<script setup lang="ts">
import { Button } from 'ant-design-vue'
import { useTheme } from '../composables/useTheme'

const { isDarkMode, toggleTheme } = useTheme()
</script>

<template>
  <div class="theme-toggle-wrapper">
    <div class="tech-background"></div>
    <Button
      type="text"
      @click="toggleTheme"
      class="theme-toggle"
    >
      {{ isDarkMode ? '☀️ Light' : '🌙 Dark' }}
    </Button>
  </div>
</template>

<style scoped>
.theme-toggle-wrapper {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
}

.tech-background {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 120px;
  height: 120px;
  background: radial-gradient(circle, rgba(114, 46, 209, 0.3) 0%, rgba(114, 46, 209, 0.1) 50%, transparent 100%);
  border-radius: 50%;
  filter: blur(20px);
  animation: pulse 3s ease-in-out infinite;
  pointer-events: none;
}

.tech-background::before {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80px;
  height: 80px;
  background: radial-gradient(circle, rgba(114, 46, 209, 0.4) 0%, transparent 70%);
  border-radius: 50%;
  filter: blur(15px);
  animation: pulse 2s ease-in-out infinite reverse;
}

.tech-background::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 60px;
  height: 60px;
  background: radial-gradient(circle, rgba(179, 127, 235, 0.5) 0%, transparent 60%);
  border-radius: 50%;
  filter: blur(10px);
  animation: pulse 1.5s ease-in-out infinite;
}

.theme-toggle {
  position: relative;
  z-index: 1;
  background: rgba(114, 46, 209, 0.1);
  backdrop-filter: blur(10px);
  border: 1px solid rgba(114, 46, 209, 0.3);
  color: #722ed1;
  font-weight: 600;
  transition: all 0.3s ease;
}

.theme-toggle:hover {
  background: rgba(114, 46, 209, 0.2);
  border-color: rgba(114, 46, 209, 0.5);
  transform: scale(1.05);
}

@keyframes pulse {
  0%, 100% {
    opacity: 0.6;
    transform: translate(-50%, -50%) scale(1);
  }
  50% {
    opacity: 1;
    transform: translate(-50%, -50%) scale(1.1);
  }
}

:global(.dark) .theme-toggle {
  background: rgba(114, 46, 209, 0.15);
  border-color: rgba(114, 46, 209, 0.4);
  color: #b37feb;
}

:global(.dark) .tech-background {
  background: radial-gradient(circle, rgba(179, 127, 235, 0.4) 0%, rgba(179, 127, 235, 0.15) 50%, transparent 100%);
}

:global(.dark) .tech-background::before {
  background: radial-gradient(circle, rgba(179, 127, 235, 0.5) 0%, transparent 70%);
}

:global(.dark) .tech-background::after {
  background: radial-gradient(circle, rgba(114, 46, 209, 0.6) 0%, transparent 60%);
}
</style>
