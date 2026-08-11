<script setup lang="ts">
import { Calendar, Clock, Collection, Star } from '@element-plus/icons-vue'
import type { FilterOptions } from '../types'

defineProps<{ options: FilterOptions | null; loading?: boolean }>()

const cards = [
  { key: 'total', label: '素材总数', icon: Collection, tone: '#60a5fa' },
  { key: 'week_new', label: '本周新增', icon: Calendar, tone: '#34d399' },
  { key: 'favorite', label: '收藏素材', icon: Star, tone: '#f59e0b' },
  { key: 'recently_modified', label: '最近修改', icon: Clock, tone: '#a78bfa' },
] as const
</script>

<template>
  <div class="stats-strip">
    <div v-for="card in cards" :key="card.key" class="stat-card surface">
      <span class="stat-icon" :style="{ color: card.tone, background: `color-mix(in srgb, ${card.tone} 13%, transparent)` }"><el-icon><component :is="card.icon" /></el-icon></span>
      <div>
        <span class="stat-value">{{ loading ? '—' : (options?.stats[card.key] ?? 0) }}</span>
        <span class="stat-label">{{ card.label }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.stats-strip { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 12px; }
.stat-card { min-height: 82px; display: flex; align-items: center; gap: 13px; padding: 16px; border-radius: 10px; }
.stat-icon { width: 38px; height: 38px; display: grid; place-items: center; border-radius: 9px; font-size: 18px; }
.stat-value { display: block; color: var(--text); font-size: 22px; font-weight: 750; line-height: 1.1; font-variant-numeric: tabular-nums; }
.stat-label { display: block; margin-top: 5px; color: var(--text-muted); font-size: 11px; }
@media (max-width: 760px) { .stats-strip { grid-template-columns: repeat(2, 1fr); } .stat-card { min-height: 68px; padding: 12px; } }
</style>

