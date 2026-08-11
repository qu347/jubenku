<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import type { GenreModule } from '../../types/genreModule'
import type { MaterialFilters } from '../../types/material'

const props = defineProps<{ modelValue: MaterialFilters; modules: GenreModule[] }>()
const emit = defineEmits<{ apply: [filters: MaterialFilters]; reset: [] }>()
const draft = reactive<MaterialFilters>({})
watch(() => props.modelValue, (value) => Object.assign(draft, value), { immediate: true, deep: true })

const materialTypes = ['人物设定', '剧情桥段', '场景参考', '世界观', '对白素材', '研究资料', '其他']
const fileTypes = ['pdf', 'docx', 'xlsx', 'csv', 'txt', 'md', 'jpg', 'jpeg', 'png']
function submit() { emit('apply', { ...draft, page: 1 }) }
</script>

<template>
  <section class="filter-panel surface" aria-label="素材筛选">
    <div class="filter-grid">
      <el-input v-model="draft.keyword" clearable placeholder="搜索标题、文件名、说明或来源" :prefix-icon="Search" @keyup.enter="submit" />
      <el-select v-model="draft.genre_module_id" clearable filterable placeholder="全部题材">
        <el-option v-for="item in modules" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="draft.material_type" clearable allow-create filterable placeholder="素材类型">
        <el-option v-for="item in materialTypes" :key="item" :label="item" :value="item" />
      </el-select>
      <el-select v-model="draft.file_extension" clearable placeholder="文件类型">
        <el-option v-for="item in fileTypes" :key="item" :label="item.toUpperCase()" :value="item" />
      </el-select>
      <el-input v-model="draft.tags" clearable placeholder="标签（多个用逗号分隔）" />
      <el-input v-model="draft.source" clearable placeholder="内容来源" />
      <el-date-picker v-model="draft.uploaded_from" type="date" value-format="YYYY-MM-DD" placeholder="上传开始日期" />
      <el-date-picker v-model="draft.uploaded_to" type="date" value-format="YYYY-MM-DD" placeholder="上传结束日期" />
    </div>
    <div class="filter-actions">
      <span>不同条件按 AND 匹配，多标签匹配任意一项</span>
      <el-button :icon="Refresh" @click="emit('reset')">清空筛选</el-button>
      <el-button type="primary" :icon="Search" @click="submit">应用筛选</el-button>
    </div>
  </section>
</template>

<style scoped>
.filter-panel{padding:14px;border-radius:10px}.filter-grid{display:grid;grid-template-columns:2fr repeat(5,minmax(120px,1fr)) 150px 150px;gap:8px}.filter-actions{display:flex;align-items:center;justify-content:flex-end;gap:8px;margin-top:10px}.filter-actions span{margin-right:auto;color:var(--text-muted);font-size:9px}@media(max-width:1320px){.filter-grid{grid-template-columns:repeat(4,1fr)}.filter-grid>:first-child{grid-column:span 2}}@media(max-width:800px){.filter-grid{grid-template-columns:1fr 1fr}.filter-grid>:first-child{grid-column:1/-1}}
</style>
