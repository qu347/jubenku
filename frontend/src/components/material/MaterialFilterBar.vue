<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import StandardTagSelector from './StandardTagSelector.vue'
import type { GenreModule } from '../../types/genreModule'
import type { MaterialFilters } from '../../types/material'
import { useUploadPlatformsStore } from '../../stores/uploadPlatforms'

const props = withDefaults(defineProps<{ modelValue: MaterialFilters; modules: GenreModule[]; hideGenre?: boolean; libraryType?: 'material' | 'script' }>(), { hideGenre: false, libraryType: 'material' })
const emit = defineEmits<{ apply: [filters: MaterialFilters]; reset: [] }>()
const uploadPlatforms = useUploadPlatformsStore()
const draft = reactive<MaterialFilters>({})
const emptyFilters: MaterialFilters = { keyword: undefined, genre_module_id: undefined, material_type: undefined, file_extension: undefined, tags: undefined, source: undefined, upload_platform: undefined, uploaded_from: undefined, uploaded_to: undefined, sort: 'created_desc', page: 1, page_size: 20 }
watch(() => props.modelValue, (value) => Object.assign(draft, emptyFilters, value), { immediate: true, deep: true })
onMounted(() => {
  if (props.libraryType === 'material') void uploadPlatforms.fetchPlatforms().catch(() => undefined)
})

const fileTypes = ['pdf', 'docx', 'xlsx', 'csv', 'txt', 'md', 'jpg', 'jpeg', 'png']
const filterTags = computed<string[]>({
  get: () => (draft.tags || '').split(/[,，]/).map((tag) => tag.trim()).filter(Boolean),
  set: (tags) => { draft.tags = tags.join(',') || undefined },
})
const selectedTagCount = computed(() => filterTags.value.length)
const taxonomyOpen = ref(true)
function submit() { emit('apply', { ...draft, material_type: undefined, source: undefined, upload_platform: props.libraryType === 'material' ? draft.upload_platform : undefined, page: 1 }) }
function syncTaxonomyOpen(event: Event) { taxonomyOpen.value = (event.currentTarget as HTMLDetailsElement).open }
</script>

<template>
  <section class="filter-panel surface" aria-label="素材筛选">
    <div class="filter-grid" :class="{ 'genre-locked': hideGenre }">
      <el-input v-model="draft.keyword" clearable placeholder="搜索标题、文件名、说明或来源" :prefix-icon="Search" @keyup.enter="submit" />
      <el-select v-if="!hideGenre" v-model="draft.genre_module_id" clearable filterable placeholder="全部题材">
        <el-option v-for="item in modules" :key="item.id" :label="item.name" :value="item.id" />
      </el-select>
      <el-select v-model="draft.file_extension" clearable placeholder="文件类型">
        <el-option v-for="item in fileTypes" :key="item" :label="item.toUpperCase()" :value="item" />
      </el-select>
      <el-select v-if="libraryType === 'material'" v-model="draft.upload_platform" data-test="filter-platform" clearable filterable default-first-option placeholder="上传平台">
        <el-option v-for="item in uploadPlatforms.platforms" :key="item" :label="item" :value="item" />
      </el-select>
      <el-date-picker v-model="draft.uploaded_from" type="date" value-format="YYYY-MM-DD" placeholder="上传开始日期" />
      <el-date-picker v-model="draft.uploaded_to" type="date" value-format="YYYY-MM-DD" placeholder="上传结束日期" />
    </div>
    <details class="taxonomy-filter" :open="taxonomyOpen" @toggle="syncTaxonomyOpen">
      <summary><span><b>标准素材标签</b><em>剧情、情绪、时代背景、角色设定和自定义标签</em></span><i>{{ selectedTagCount ? `已选 ${selectedTagCount} 项` : '展开选择' }}</i></summary>
      <div class="taxonomy-body"><StandardTagSelector v-model="filterTags" /></div>
    </details>
    <div class="filter-actions">
      <el-button :icon="Refresh" @click="emit('reset')">清空筛选</el-button>
      <el-button type="primary" :icon="Search" @click="submit">应用筛选</el-button>
    </div>
  </section>
</template>

<style scoped>
.filter-panel{padding:16px;border-radius:10px;overflow:hidden}.filter-grid{display:grid;grid-template-columns:minmax(260px,2fr) repeat(4,minmax(155px,1fr));gap:10px}.filter-grid>:deep(.el-date-editor.el-input),.filter-grid>:deep(.el-date-editor.el-input__wrapper){width:100%;min-width:0}.taxonomy-filter{margin-top:12px;border:1px solid var(--border-soft);border-radius:9px;background:color-mix(in srgb,var(--panel-raised) 58%,transparent);overflow:hidden}.taxonomy-filter summary{min-height:52px;display:flex;align-items:center;justify-content:space-between;gap:16px;padding:10px 14px;list-style:none;cursor:pointer}.taxonomy-filter summary::-webkit-details-marker{display:none}.taxonomy-filter summary span{display:grid;gap:3px}.taxonomy-filter summary b{font-size:14px}.taxonomy-filter summary em{color:var(--text-muted);font-size:11px;font-style:normal}.taxonomy-filter summary i{flex:0 0 auto;color:var(--accent);font-size:12px;font-style:normal}.taxonomy-filter summary i::after{content:'⌄';margin-left:7px}.taxonomy-filter[open] summary i::after{content:'⌃'}.taxonomy-body{padding:17px;border-top:1px solid var(--border-soft)}.filter-actions{display:flex;align-items:center;justify-content:flex-end;flex-wrap:wrap;gap:9px;margin-top:12px}.filter-actions span{margin-right:auto;color:var(--text-muted);font-size:12px;line-height:1.5}.filter-actions :deep(.el-button){flex:0 0 auto}@media(max-width:1180px){.filter-grid{grid-template-columns:repeat(3,minmax(0,1fr))}.filter-grid>:first-child{grid-column:span 2}}@media(max-width:760px){.filter-grid{grid-template-columns:1fr 1fr}.filter-grid>:first-child{grid-column:1/-1}}@media(max-width:520px){.filter-grid{grid-template-columns:1fr}.filter-grid>:first-child{grid-column:auto}.filter-actions{align-items:stretch;flex-direction:column}.filter-actions span{margin:0}.filter-actions :deep(.el-button){width:100%;margin:0}.taxonomy-filter summary{align-items:flex-start;flex-direction:column;gap:6px}}
.filter-grid.genre-locked{grid-template-columns:minmax(260px,2fr) repeat(3,minmax(155px,1fr))}
@media(max-width:1180px){.filter-grid.genre-locked{grid-template-columns:repeat(3,minmax(0,1fr))}}
@media(max-width:760px){.filter-grid.genre-locked{grid-template-columns:1fr 1fr}}
@media(max-width:520px){.filter-grid.genre-locked{grid-template-columns:1fr}}
</style>
