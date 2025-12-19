<script setup lang="ts">
import { computed } from 'vue'
import { Progress } from 'ant-design-vue'

const props = withDefaults(defineProps<{
  score: number
  size?: number
}>(), {
  size: 80
})

const fontSize = computed(() => {
  if (props.size <= 60) return '12px'
  if (props.size <= 80) return '16px'
  return '20px'
})

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
      :size="size"
      :stroke-color="getScoreStrokeColor(score)"
      :format="() => ''"
    />
    <div class="score-text" :style="{ color: getScoreColor(score), fontSize: fontSize, lineHeight: `${size}px`, width: `${size}px` }">
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
  padding: 5px;
}

.score-text {
  position: absolute;
  font-weight: 700;
  text-align: center;
  pointer-events: none;
}
</style>
