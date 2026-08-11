<script setup lang="ts">
import { CircleClose, DocumentAdd, RefreshRight, Search } from '@element-plus/icons-vue'

defineProps<{ kind: 'empty' | 'search' | 'error'; message?: string }>()
const emit = defineEmits<{ add: []; clear: []; retry: [] }>()
</script>

<template>
  <div class="library-state surface">
    <span class="state-icon"><el-icon><CircleClose v-if="kind === 'error'" /><Search v-else-if="kind === 'search'" /><DocumentAdd v-else /></el-icon></span>
    <h3>{{ kind === 'error' ? '暂时无法加载素材' : kind === 'search' ? '没有找到匹配的素材' : '素材库还是空的' }}</h3>
    <p>{{ message || (kind === 'search' ? '换个关键词或减少筛选条件试试。' : '保存第一个灵感，让它成为故事的起点。') }}</p>
    <el-button v-if="kind === 'error'" :icon="RefreshRight" @click="emit('retry')">重新加载</el-button>
    <el-button v-else-if="kind === 'search'" @click="emit('clear')">清空筛选</el-button>
    <el-button v-else type="primary" :icon="DocumentAdd" @click="emit('add')">新增素材</el-button>
  </div>
</template>

<style scoped>
.library-state { min-height: 320px; display: grid; place-content: center; justify-items: center; padding: 40px; border-radius: 10px; text-align: center; }.state-icon { width: 54px; height: 54px; display: grid; place-items: center; border-radius: 14px; background: var(--panel-raised); color: var(--accent); font-size: 25px; }.library-state h3 { margin: 18px 0 8px; font-family: "Songti SC", serif; font-size: 18px; }.library-state p { margin: 0 0 20px; color: var(--text-muted); font-size: 12px; }
</style>
