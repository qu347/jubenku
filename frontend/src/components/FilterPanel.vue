<script setup lang="ts">
import { computed, ref } from 'vue'
import { ArrowDown, ArrowUp, Close, Filter } from '@element-plus/icons-vue'
import { MATERIAL_TYPES, SOURCE_LABELS, STATUS_LABELS } from '../config/materials'
import type { FilterOptions, Filters } from '../types'

const props = defineProps<{ filters: Filters; options: FilterOptions | null }>()
const emit = defineEmits<{ clear: [] }>()
const expanded = ref(false)
const activeCount = computed(() =>
  props.filters.type.length + props.filters.genre.length + props.filters.status.length + props.filters.tags.length +
  props.filters.project_id.length + props.filters.source_type.length + (props.filters.favorite !== null ? 1 : 0) +
  (props.filters.used !== null ? 1 : 0) + (props.filters.created_range ? 1 : 0) + (props.filters.updated_range ? 1 : 0),
)
</script>

<template>
  <section class="filter-panel surface">
    <div class="filter-heading">
      <div class="filter-title"><el-icon><Filter /></el-icon><span>组合筛选</span><em v-if="activeCount">{{ activeCount }}</em></div>
      <div class="filter-heading-actions">
        <button v-if="activeCount" class="clear-button" @click="emit('clear')"><el-icon><Close /></el-icon> 清空筛选</button>
        <button class="expand-button" @click="expanded = !expanded">{{ expanded ? '收起' : '更多条件' }}<el-icon><ArrowUp v-if="expanded" /><ArrowDown v-else /></el-icon></button>
      </div>
    </div>
    <div class="filter-grid">
      <el-select v-model="filters.type" multiple collapse-tags clearable placeholder="素材类型">
        <el-option v-for="item in MATERIAL_TYPES" :key="item.value" :label="item.label" :value="item.value" />
      </el-select>
      <el-select v-model="filters.genre" multiple collapse-tags clearable filterable allow-create placeholder="题材">
        <el-option v-for="(_, genre) in options?.genres" :key="genre" :label="genre" :value="genre" />
      </el-select>
      <el-select v-model="filters.status" multiple collapse-tags clearable placeholder="状态">
        <el-option v-for="(label, value) in STATUS_LABELS" :key="value" :label="label" :value="value" />
      </el-select>
      <el-select v-model="filters.tags" multiple collapse-tags clearable filterable placeholder="标签">
        <el-option v-for="tag in options?.tags" :key="tag.id" :label="tag.name" :value="tag.name" />
      </el-select>
      <template v-if="expanded">
        <el-select v-model="filters.project_id" multiple collapse-tags clearable placeholder="所属项目">
          <el-option v-for="project in options?.projects" :key="project.id" :label="project.name" :value="project.id" />
        </el-select>
        <el-select v-model="filters.source_type" multiple collapse-tags clearable placeholder="来源">
          <el-option v-for="source in options?.source_types" :key="source" :label="SOURCE_LABELS[source]" :value="source" />
        </el-select>
        <el-select v-model="filters.favorite" clearable placeholder="是否收藏">
          <el-option label="仅收藏" :value="true" /><el-option label="未收藏" :value="false" />
        </el-select>
        <el-select v-model="filters.used" clearable placeholder="是否使用过">
          <el-option label="已使用" :value="true" /><el-option label="未使用" :value="false" />
        </el-select>
        <el-date-picker v-model="filters.created_range" type="daterange" range-separator="至" start-placeholder="创建起始" end-placeholder="创建结束" value-format="YYYY-MM-DD" />
        <el-date-picker v-model="filters.updated_range" type="daterange" range-separator="至" start-placeholder="修改起始" end-placeholder="修改结束" value-format="YYYY-MM-DD" />
        <div class="tag-mode">
          <span>多标签：</span>
          <el-radio-group v-model="filters.tag_mode" size="small"><el-radio-button value="any">任一</el-radio-button><el-radio-button value="all">全部</el-radio-button></el-radio-group>
        </div>
      </template>
    </div>
  </section>
</template>

<style scoped>
.filter-panel { border-radius: 10px; padding: 14px; }
.filter-heading { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }
.filter-title, .filter-heading-actions, .clear-button, .expand-button { display: flex; align-items: center; }
.filter-title { gap: 8px; color: var(--text-secondary); font-size: 12px; font-weight: 700; }
.filter-title em { min-width: 18px; height: 18px; display: grid; place-items: center; border-radius: 9px; background: var(--accent); color: #17110a; font-size: 10px; font-style: normal; }
.filter-heading-actions { gap: 16px; }
.clear-button, .expand-button { gap: 4px; border: 0; background: transparent; color: var(--text-muted); font-size: 11px; cursor: pointer; }
.clear-button:hover { color: var(--danger); }.expand-button:hover { color: var(--text); }
.filter-grid { display: grid; grid-template-columns: repeat(4, minmax(140px, 1fr)); gap: 10px; }
.tag-mode { display: flex; align-items: center; gap: 8px; color: var(--text-muted); font-size: 11px; }
@media (max-width: 1200px) { .filter-grid { grid-template-columns: repeat(3, 1fr); } }
@media (max-width: 760px) { .filter-grid { grid-template-columns: 1fr 1fr; } }
@media (max-width: 520px) { .filter-grid { grid-template-columns: 1fr; } }
</style>
