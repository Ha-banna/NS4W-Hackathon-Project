<script setup lang="ts">
import { computed } from 'vue'
import { ConfigProvider, theme } from 'ant-design-vue'
import LandingPage from './components/LandingPage.vue'

// Always use dark theme with purple primary color
const themeConfig = computed(() => ({
  algorithm: theme.darkAlgorithm,
  token: {
    colorPrimary: '#722ed1',
  },
}))
</script>

<template>
  <ConfigProvider :theme="themeConfig">
    <div class="app-wrapper">
      <LandingPage />
    </div>
  </ConfigProvider>
</template>

<style scoped>
.app-wrapper {
  width: 100%;
  min-height: 100vh;
  position: relative;
}
</style>
