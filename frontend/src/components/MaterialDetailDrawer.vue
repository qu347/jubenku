<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Clock, CopyDocument, Delete, EditPen, Link, RefreshLeft, Star } from '@element-plus/icons-vue'
import { materialApi } from '../api'
import { SOURCE_LABELS, STATUS_LABELS, typeInfo } from '../config/materials'
import type { Material, MaterialVersion } from '../types'
import { formatDateTime } from '../utils/format'

const props = defineProps<{ modelValue: boolean; material: Material | null }>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  edit: [material: Material]
  duplicate: [material: Material]
  favorite: [material: Material]
  remove: [material: Material]
  restored: [material: Material]
}>()

const versions = ref<MaterialVersion[]>([])
const versionsLoading = ref(false)
const renderedContent = computed(() => DOMPurify.sanitize(marked.parse(props.material?.content || '*暂无正文*', { async: false }) as string))
const metadataEntries = computed(() => Object.entries(props.material?.metadata || {}).filter(([, value]) => value !== '' && value !== null && value !== undefined))

watch(() => [props.modelValue, props.material?.id] as const, async ([open, id]) => {
  if (!open || !id) return
  versionsLoading.value = true
  try {
    versions.value = (await materialApi.versions(id)).data.data
  } finally {
    versionsLoading.value = false
  }
}, { immediate: true })

async function restoreVersion(version: MaterialVersion) {
  if (!props.material) return
  await ElMessageBox.confirm(`恢复版本 v${version.version_number}？当前内容会先生成一个新版本，可随时找回。`, '恢复历史版本', { type: 'warning' })
  const response = await materialApi.restoreVersion(props.material.id, version.id)
  ElMessage.success(`已恢复到 v${version.version_number}`)
  emit('restored', response.data.data)
}

function displayValue(value: unknown): string {
  if (typeof value === 'object') return JSON.stringify(value, null, 2)
  return String(value)
}
</script>

<template>
  <el-drawer :model-value="modelValue" size="min(680px, 100vw)" @update:model-value="emit('update:modelValue', $event)">
    <template #header>
      <div v-if="material" class="detail-heading">
        <span class="detail-type" :style="{ color: typeInfo(material.material_type).color }"><el-icon><component :is="typeInfo(material.material_type).icon" /></el-icon>{{ typeInfo(material.material_type).label }}</span>
        <span class="version-chip">v{{ material.version }}</span>
      </div>
    </template>

    <div v-if="material" class="detail-shell">
      <section class="hero">
        <div class="hero-top">
          <div><h1>{{ material.title }}</h1><p>{{ material.summary || '暂无一句话概述' }}</p></div>
          <button class="favorite" :class="{ active: material.favorite }" @click="emit('favorite', material)"><el-icon><Star /></el-icon></button>
        </div>
        <div class="chips"><span>{{ material.genre || '未分类题材' }}</span><span class="status">{{ STATUS_LABELS[material.status] }}</span><span v-for="tag in material.tags" :key="tag.id"># {{ tag.name }}</span></div>
      </section>

      <section class="meta-strip">
        <div><small>所属项目</small><b>{{ material.project?.name || '未归项目' }}</b></div>
        <div><small>素材来源</small><b>{{ SOURCE_LABELS[material.source_type] }}</b></div>
        <div><small>使用次数</small><b>{{ material.usage_count }} 次</b></div>
        <div><small>最后更新</small><b>{{ formatDateTime(material.updated_at) }}</b></div>
      </section>

      <section v-if="metadataEntries.length" class="detail-section">
        <h2>结构化设定</h2>
        <div class="metadata-grid">
          <div v-for="([key, value]) in metadataEntries" :key="key"><small>{{ key }}</small><pre>{{ displayValue(value) }}</pre></div>
        </div>
      </section>

      <section class="detail-section">
        <h2>完整内容</h2>
        <div class="markdown-body" v-html="renderedContent"></div>
        <a v-if="material.source_url" class="source-link" :href="material.source_url" target="_blank" rel="noreferrer"><el-icon><Link /></el-icon>打开外部来源</a>
      </section>

      <section class="detail-section versions">
        <h2>历史版本 <small>{{ versions.length }} 个快照</small></h2>
        <el-skeleton v-if="versionsLoading" :rows="3" animated />
        <div v-else class="version-list">
          <div v-for="version in versions" :key="version.id" class="version-item">
            <span class="version-node"><el-icon><Clock /></el-icon></span>
            <div><b>v{{ version.version_number }} · {{ version.change_note }}</b><small>{{ formatDateTime(version.created_at) }}</small></div>
            <el-button v-if="version.version_number !== material.version" text size="small" :icon="RefreshLeft" @click="restoreVersion(version)">恢复</el-button>
            <span v-else class="current">当前</span>
          </div>
        </div>
      </section>
    </div>

    <template #footer>
      <div v-if="material" class="detail-footer">
        <el-button :icon="Delete" @click="emit('remove', material)">删除</el-button>
        <div><el-button :icon="CopyDocument" @click="emit('duplicate', material)">复制</el-button><el-button type="primary" :icon="EditPen" @click="emit('edit', material)">编辑素材</el-button></div>
      </div>
    </template>
  </el-drawer>
</template>

<style scoped>
.detail-heading { display: flex; align-items: center; gap: 9px; }.detail-type { display: inline-flex; align-items: center; gap: 7px; font-size: 12px; font-weight: 750; }.version-chip { padding: 2px 6px; border-radius: 4px; background: var(--panel-raised); color: var(--text-muted); font-size: 9px; }.detail-shell { padding: 28px 28px 110px; }.hero { padding-bottom: 23px; border-bottom: 1px solid var(--border-soft); }.hero-top { display: flex; align-items: flex-start; gap: 20px; }.hero-top > div { flex: 1; }.hero h1 { margin: 0; font-family: "Songti SC", serif; font-size: 27px; line-height: 1.35; }.hero p { margin: 10px 0 0; color: var(--text-secondary); font-size: 13px; line-height: 1.7; }.favorite { width: 36px; height: 36px; flex: 0 0 auto; display: grid; place-items: center; border: 1px solid var(--border); border-radius: 8px; background: var(--panel-raised); color: var(--text-muted); cursor: pointer; }.favorite.active { color: var(--accent); }.chips { display: flex; flex-wrap: wrap; gap: 6px; margin-top: 17px; }.chips span { padding: 4px 8px; border-radius: 5px; background: var(--panel-raised); color: var(--text-secondary); font-size: 10px; }.chips .status { background: var(--accent-soft); color: var(--accent); }
.meta-strip { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1px; margin: 20px 0; overflow: hidden; border: 1px solid var(--border-soft); border-radius: 8px; background: var(--border-soft); }.meta-strip > div { min-width: 0; padding: 12px; background: var(--panel-raised); }.meta-strip small, .metadata-grid small { display: block; color: var(--text-muted); font-size: 9px; }.meta-strip b { display: block; margin-top: 5px; overflow: hidden; color: var(--text-secondary); font-size: 10px; font-weight: 600; text-overflow: ellipsis; white-space: nowrap; }
.detail-section { padding: 23px 0; border-top: 1px solid var(--border-soft); }.detail-section h2 { margin: 0 0 16px; font-size: 13px; }.detail-section h2 small { margin-left: 6px; color: var(--text-muted); font-size: 9px; font-weight: 500; }.metadata-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; }.metadata-grid > div { min-width: 0; padding: 11px; border-radius: 7px; background: var(--panel-raised); }.metadata-grid pre { margin: 5px 0 0; overflow: auto; color: var(--text-secondary); font: 11px/1.55 inherit; white-space: pre-wrap; }.source-link { display: inline-flex; align-items: center; gap: 5px; margin-top: 15px; color: var(--accent); font-size: 11px; text-decoration: none; }
.version-list { display: grid; }.version-item { display: grid; grid-template-columns: 28px 1fr auto; align-items: center; gap: 9px; padding: 10px 0; }.version-node { width: 26px; height: 26px; display: grid; place-items: center; border-radius: 50%; background: var(--panel-raised); color: var(--text-muted); }.version-item b { display: block; color: var(--text-secondary); font-size: 10px; }.version-item small { display: block; margin-top: 3px; color: var(--text-muted); font-size: 9px; }.current { color: #34d399; font-size: 9px; }.detail-footer { width: 100%; display: flex; justify-content: space-between; }.detail-footer > div { display: flex; gap: 8px; }
@media (max-width: 600px) { .detail-shell { padding: 22px 18px 100px; }.meta-strip { grid-template-columns: 1fr 1fr; }.metadata-grid { grid-template-columns: 1fr; } }
</style>
