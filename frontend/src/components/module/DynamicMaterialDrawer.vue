<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { CopyDocument, Delete, EditPen, Star } from '@element-plus/icons-vue'
import { genreModuleApi, materialApi } from '../../api'
import { STATUS_LABELS } from '../../config/materials'
import { useGenresStore } from '../../stores/genres'
import type { Material, MaterialPayload, ModuleSection } from '../../types'
import { formatDateTime } from '../../utils/format'

const props = defineProps<{
  modelValue: boolean
  mode: 'view' | 'edit' | 'create'
  material?: Material | null
  initialGenreId?: string | null
  initialSectionId?: string | null
}>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  'update:mode': [value: 'view' | 'edit' | 'create']
  changed: [material?: Material]
}>()

const genreStore = useGenresStore()
const sections = ref<ModuleSection[]>([])
const saving = ref(false)
const dirty = ref(false)
const form = reactive<MaterialPayload>({
  title: '', material_type: 'custom', genre_module_id: null, section_id: null, genre: '', summary: '', content: '',
  status: 'draft', project_id: null, cover_url: null, source_type: 'original', source_url: null,
  favorite: false, usage_count: 0, metadata: {}, tag_names: [], change_note: '保存素材',
})
const activeSection = computed(() => sections.value.find((item) => item.id === form.section_id) || null)
const isView = computed(() => props.mode === 'view')
const title = computed(() => props.mode === 'create' ? '新增模块素材' : props.mode === 'edit' ? '编辑模块素材' : '素材详情')

async function loadSections(moduleId: string | null) {
  sections.value = moduleId ? (await genreModuleApi.sections(moduleId)).data.data : []
  if (form.section_id && !sections.value.some((item) => item.id === form.section_id)) form.section_id = sections.value[0]?.id || null
}

function hydrate() {
  if (props.material) {
    Object.assign(form, {
      title: props.material.title, material_type: props.material.material_type || 'custom',
      genre_module_id: props.material.genre_module_id, section_id: props.material.section_id,
      genre: props.material.genre || props.material.genre_module?.name || '', summary: props.material.summary,
      content: props.material.content, status: props.material.status, project_id: props.material.project_id,
      cover_url: props.material.cover_url, source_type: props.material.source_type, source_url: props.material.source_url,
      favorite: props.material.favorite, usage_count: props.material.usage_count,
      metadata: JSON.parse(JSON.stringify(props.material.metadata || {})) as Record<string, unknown>,
      tag_names: props.material.tags.map((tag) => tag.name), change_note: '更新模块素材',
    })
  } else {
    Object.assign(form, {
      title: '', material_type: 'custom', genre_module_id: props.initialGenreId || genreStore.activeModules[0]?.id || null,
      section_id: props.initialSectionId || null, genre: '', summary: '', content: '', status: 'draft',
      project_id: null, cover_url: null, source_type: 'original', source_url: null, favorite: false,
      usage_count: 0, metadata: {}, tag_names: [], change_note: '创建模块素材',
    })
  }
  dirty.value = false
  void loadSections(form.genre_module_id)
}

watch(() => props.modelValue, (open) => { if (open) hydrate() })
watch(() => form.genre_module_id, (id, old) => { if (props.modelValue && id !== old) void loadSections(id) })
watch(form, () => { if (props.modelValue && !isView.value) dirty.value = true }, { deep: true })

async function save() {
  if (!form.title.trim()) return ElMessage.warning('请输入素材标题')
  if (!form.genre_module_id) return ElMessage.warning('请选择题材模块')
  if (!form.section_id) return ElMessage.warning('请选择功能板块')
  const module = genreStore.modules.find((item) => item.id === form.genre_module_id)
  saving.value = true
  try {
    const payload = { ...form, title: form.title.trim(), genre: module?.name || form.genre, material_type: activeSection.value?.section_key || 'custom' }
    const response = props.material
      ? await materialApi.update(props.material.id, payload)
      : await materialApi.create(payload)
    dirty.value = false
    ElMessage.success(props.material ? '素材已更新并生成版本快照' : '素材已创建并写入数据库')
    emit('changed', response.data.data); emit('update:modelValue', false)
  } finally { saving.value = false }
}

async function toggleFavorite() {
  if (!props.material) return
  const result = await materialApi.favorite(props.material.id)
  ElMessage.success(result.data.data.favorite ? '已收藏' : '已取消收藏')
  emit('changed', result.data.data)
}

async function duplicate() {
  if (!props.material) return
  const result = await materialApi.duplicate(props.material.id)
  ElMessage.success('副本已创建')
  emit('changed', result.data.data); emit('update:modelValue', false)
}

async function remove() {
  if (!props.material) return
  await ElMessageBox.confirm(`将“${props.material.title}”移入回收站？`, '删除素材', { type: 'warning' })
  await materialApi.remove(props.material.id); ElMessage.success('素材已移入回收站')
  emit('changed'); emit('update:modelValue', false)
}

async function beforeClose(done: () => void) {
  if (!dirty.value || isView.value) return done()
  try {
    await ElMessageBox.confirm('当前修改尚未保存，确定放弃吗？', '未保存的修改', { type: 'warning', confirmButtonText: '放弃修改' })
    dirty.value = false; done()
  } catch { /* 继续编辑 */ }
}
</script>

<template>
  <el-drawer :model-value="modelValue" :title="title" size="min(700px, 100vw)" :before-close="beforeClose" @update:model-value="emit('update:modelValue', $event)">
    <div v-if="isView && material" class="dynamic-detail">
      <div class="detail-kicker"><span :style="{ color: material.genre_module?.theme_color }">{{ material.genre_module?.name || '未归题材' }}</span><i>·</i><span>{{ material.section?.section_name || '未归板块' }}</span></div>
      <h1>{{ material.title }}</h1><p class="summary">{{ material.summary || '暂无概述' }}</p>
      <div class="detail-tags"><span>{{ STATUS_LABELS[material.status] }}</span><span v-for="tag in material.tags" :key="tag.id"># {{ tag.name }}</span></div>
      <section v-if="Object.keys(material.metadata).length"><h3>自定义字段</h3><div class="metadata-list"><div v-for="(value,key) in material.metadata" :key="key"><small>{{ key }}</small><b>{{ Array.isArray(value) ? value.join('、') : String(value) }}</b></div></div></section>
      <section><h3>完整内容</h3><div class="content">{{ material.content || '暂无正文' }}</div></section>
      <div class="detail-meta">创建于 {{ formatDateTime(material.created_at) }} · 更新于 {{ formatDateTime(material.updated_at) }} · 使用 {{ material.usage_count }} 次</div>
    </div>
    <div v-else class="dynamic-form">
      <section><h3>归属位置</h3><div class="form-grid"><el-form-item label="题材模块"><el-select v-model="form.genre_module_id" class="w-full"><el-option v-for="module in genreStore.activeModules" :key="module.id" :label="module.name" :value="module.id" /></el-select></el-form-item><el-form-item label="功能板块"><el-select v-model="form.section_id" class="w-full"><el-option v-for="section in sections" :key="section.id" :label="section.section_name" :value="section.id" /></el-select></el-form-item></div></section>
      <section><h3>公共字段</h3><el-form-item label="标题" required><el-input v-model="form.title" maxlength="100" show-word-limit /></el-form-item><el-form-item label="一句话概述"><el-input v-model="form.summary" type="textarea" :rows="2" maxlength="300" /></el-form-item><div class="form-grid"><el-form-item label="状态"><el-select v-model="form.status" class="w-full"><el-option v-for="(label,value) in STATUS_LABELS" :key="value" :label="label" :value="value" /></el-select></el-form-item><el-form-item label="标签"><el-select v-model="form.tag_names" multiple filterable allow-create class="w-full" /></el-form-item></div><el-form-item label="正文（Markdown）"><el-input v-model="form.content" type="textarea" :rows="8" /></el-form-item></section>
      <section v-if="activeSection?.field_schema.length"><h3>{{ activeSection.section_name }} · 自定义字段</h3><div class="form-grid"><el-form-item v-for="field in activeSection.field_schema" :key="field.key" :label="field.label" :required="field.required" :class="{ wide: ['textarea','markdown'].includes(field.type) }"><el-input v-if="['text','url','image','relation'].includes(field.type)" :model-value="String(form.metadata[field.key] || '')" :placeholder="field.placeholder" @update:model-value="form.metadata[field.key] = $event" /><el-input v-else-if="['textarea','markdown'].includes(field.type)" :model-value="String(form.metadata[field.key] || '')" type="textarea" :rows="4" @update:model-value="form.metadata[field.key] = $event" /><el-input-number v-else-if="field.type === 'number'" :model-value="Number(form.metadata[field.key] || 0)" class="w-full" @update:model-value="form.metadata[field.key] = $event" /><el-date-picker v-else-if="field.type === 'date'" :model-value="form.metadata[field.key] as string" value-format="YYYY-MM-DD" class="w-full" @update:model-value="form.metadata[field.key] = $event" /><el-select v-else :model-value="form.metadata[field.key]" :multiple="['multiselect','tags'].includes(field.type)" :filterable="field.type === 'tags'" :allow-create="field.type === 'tags'" class="w-full" @update:model-value="form.metadata[field.key] = $event"><el-option v-for="option in field.options" :key="option" :label="option" :value="option" /></el-select></el-form-item></div></section>
    </div>
    <template #footer><div class="drawer-actions"><template v-if="isView && material"><el-button :icon="Delete" @click="remove">删除</el-button><div><el-button :icon="Star" @click="toggleFavorite">{{ material.favorite ? '取消收藏' : '收藏' }}</el-button><el-button :icon="CopyDocument" @click="duplicate">复制</el-button><el-button type="primary" :icon="EditPen" @click="emit('update:mode','edit')">编辑</el-button></div></template><template v-else><span>{{ dirty ? '● 有未保存修改' : '' }}</span><div><el-button @click="beforeClose(() => emit('update:modelValue',false))">取消</el-button><el-button type="primary" :loading="saving" @click="save">保存素材</el-button></div></template></div></template>
  </el-drawer>
</template>

<style scoped>
.dynamic-detail,.dynamic-form { padding: 26px 28px 110px; }.detail-kicker { display:flex;gap:7px;color:var(--text-muted);font-size:11px;font-weight:700; }.dynamic-detail h1 { margin:12px 0 8px;font-family:"Songti SC",serif;font-size:28px; }.summary { color:var(--text-secondary);line-height:1.7; }.detail-tags { display:flex;flex-wrap:wrap;gap:6px;margin:16px 0 24px; }.detail-tags span { padding:4px 8px;border-radius:5px;background:var(--panel-raised);color:var(--text-secondary);font-size:10px; }.dynamic-detail section,.dynamic-form section { padding:20px 0;border-top:1px solid var(--border-soft); }.dynamic-detail h3,.dynamic-form h3 { margin:0 0 15px;font-size:13px; }.metadata-list { display:grid;grid-template-columns:1fr 1fr;gap:8px; }.metadata-list div { padding:11px;border-radius:7px;background:var(--panel-raised); }.metadata-list small,.metadata-list b { display:block; }.metadata-list small { color:var(--text-muted);font-size:9px; }.metadata-list b { margin-top:5px;color:var(--text-secondary);font-size:11px;white-space:pre-wrap; }.content { color:var(--text-secondary);font-size:13px;line-height:1.8;white-space:pre-wrap; }.detail-meta { margin-top:20px;color:var(--text-muted);font-size:9px; }.form-grid { display:grid;grid-template-columns:1fr 1fr;gap:0 12px; }.form-grid .wide { grid-column:1/-1; }.w-full { width:100%; }.drawer-actions { width:100%;display:flex;align-items:center;justify-content:space-between; }.drawer-actions>span { color:var(--text-muted);font-size:9px; }.drawer-actions>div { display:flex;gap:8px; }
</style>
