<script setup lang="ts">
import { Progress } from 'ant-design-vue'

const props = defineProps<{
  score: number
}>()

const getScoreColor = (score: number) => {
  if (score >= 85) return '#52c41a'
  if (score >= 70) return '#faad14'
  return '#ff4d4f'
}

const getScoreStrokeColor = (score: number) => {
  if (score >= 85) return ['#52c41a', '#73d13d']
  if (score >= 70) return ['#faad14', '#ffc53d']
  return ['#ff4d4f', '#ff7875']
}
</script>

<template>
  <div class="score-circle-wrapper">
    <Progress
      type="circle"
      :percent="score"
      :size="80"
      :stroke-color="getScoreStrokeColor(score)"
      :format="() => ''"
    />
    <div class="score-text" :style="{ color: getScoreColor(score) }">
      {{ score }}
    </div>
  </div>
</template>

<style scoped>
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
</style>
