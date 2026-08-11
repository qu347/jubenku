<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import { Check, Clock } from '@element-plus/icons-vue'
import { materialApi } from '../api'
import { MATERIAL_TYPES, METADATA_FIELDS, SOURCE_LABELS, STATUS_LABELS } from '../config/materials'
import type { Material, MaterialPayload, Project, Tag } from '../types'

const props = defineProps<{
  modelValue: boolean
  material: Material | null
  projects: Project[]
  tags: Tag[]
}>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: [material: Material, autosave: boolean]
}>()

const formRef = ref<FormInstance>()
const saving = ref(false)
const dirty = ref(false)
const lastSavedAt = ref<Date | null>(null)
const rawMetadata = ref('{}')
let autosaveTimer: number | undefined

const emptyForm = (): MaterialPayload => ({
  title: '', material_type: 'character', genre_module_id: null, section_id: null, genre: '', summary: '', content: '', status: 'draft',
  project_id: null, cover_url: null, source_type: 'original', source_url: null, favorite: false,
  usage_count: 0, metadata: {}, tag_names: [], change_note: '保存素材',
})
const form = reactive<MaterialPayload>(emptyForm())
const dynamicFields = computed(() => METADATA_FIELDS[form.material_type] || [])
const isEditing = computed(() => Boolean(props.material))

const rules: FormRules<MaterialPayload> = {
  title: [{ required: true, message: '请输入素材标题', trigger: 'blur' }, { max: 100, message: '标题不能超过 100 个字符', trigger: 'blur' }],
  material_type: [{ required: true, message: '请选择素材类型', trigger: 'change' }],
}

function resetForm() {
  const next = props.material
    ? {
        title: props.material.title, material_type: props.material.material_type, genre: props.material.genre,
        genre_module_id: props.material.genre_module_id, section_id: props.material.section_id,
        summary: props.material.summary, content: props.material.content, status: props.material.status,
        project_id: props.material.project_id, cover_url: props.material.cover_url, source_type: props.material.source_type,
        source_url: props.material.source_url, favorite: props.material.favorite, usage_count: props.material.usage_count,
        metadata: JSON.parse(JSON.stringify(props.material.metadata || {})) as Record<string, unknown>, tag_names: props.material.tags.map((tag) => tag.name),
        change_note: '更新素材',
      }
    : emptyForm()
  Object.assign(form, next)
  rawMetadata.value = JSON.stringify(next.metadata, null, 2)
  dirty.value = false
  lastSavedAt.value = props.material ? new Date(props.material.updated_at) : null
  nextTick(() => formRef.value?.clearValidate())
}

watch(() => props.modelValue, (open) => { if (open) resetForm() })
watch(form, () => { if (props.modelValue) dirty.value = true }, { deep: true })
watch(rawMetadata, () => { if (props.modelValue && !dynamicFields.value.length) dirty.value = true })

function syncRawMetadata(): boolean {
  if (dynamicFields.value.length) return true
  try {
    const parsed = JSON.parse(rawMetadata.value || '{}')
    if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error()
    form.metadata = parsed as Record<string, unknown>
    return true
  } catch {
    ElMessage.error('扩展字段必须是有效的 JSON 对象')
    return false
  }
}

async function save(autosave = false) {
  if (saving.value || !dirty.value || !syncRawMetadata()) return
  if (!form.title.trim() || !form.material_type) {
    if (!autosave) await formRef.value?.validate()
    return
  }
  if (!autosave) {
    const valid = await formRef.value?.validate().catch(() => false)
    if (!valid) return
  }
  saving.value = true
  try {
    const payload = { ...form, title: form.title.trim(), change_note: autosave ? '自动保存草稿' : (form.change_note || '保存素材') }
    const response = props.material
      ? await materialApi.update(props.material.id, payload)
      : await materialApi.create(payload)
    dirty.value = false
    lastSavedAt.value = new Date()
    emit('saved', response.data.data, autosave)
    if (!autosave) {
      ElMessage.success(props.material ? '素材已保存，并创建历史版本' : '素材创建成功')
      emit('update:modelValue', false)
    }
  } finally {
    saving.value = false
  }
}

async function beforeClose(done: () => void) {
  if (!dirty.value) return done()
  try {
    await ElMessageBox.confirm('当前修改尚未保存，确定要离开吗？', '未保存的修改', {
      confirmButtonText: '放弃修改', cancelButtonText: '继续编辑', type: 'warning',
    })
    dirty.value = false
    done()
  } catch { /* 用户继续编辑 */ }
}

function handleBeforeUnload(event: BeforeUnloadEvent) {
  if (!props.modelValue || !dirty.value) return
  event.preventDefault()
  event.returnValue = ''
}

onMounted(() => {
  autosaveTimer = window.setInterval(() => {
    if (props.modelValue && isEditing.value && dirty.value) void save(true)
  }, 15_000)
  window.addEventListener('beforeunload', handleBeforeUnload)
})

onBeforeUnmount(() => {
  if (autosaveTimer) window.clearInterval(autosaveTimer)
  window.removeEventListener('beforeunload', handleBeforeUnload)
})
</script>

<template>
  <el-drawer
    :model-value="modelValue"
    :title="isEditing ? '编辑素材' : '新增素材'"
    size="min(720px, 100vw)"
    :before-close="beforeClose"
    @update:model-value="emit('update:modelValue', $event)"
  >
    <div class="form-shell">
      <div class="form-status">
        <span><el-icon><Clock /></el-icon>{{ isEditing ? '编辑时每 15 秒自动保存草稿' : '首次保存后启用自动保存' }}</span>
        <b v-if="lastSavedAt">上次保存 {{ lastSavedAt.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' }) }}</b>
        <b v-else-if="dirty">有未保存修改</b>
      </div>

      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" class="material-form">
        <section class="form-section">
          <h3>基础信息</h3>
          <div class="form-grid two">
            <el-form-item label="素材标题" prop="title" class="span-2"><el-input v-model="form.title" maxlength="100" show-word-limit placeholder="给这个创作火花一个准确的名字" /></el-form-item>
            <el-form-item label="素材类型" prop="material_type"><el-select v-model="form.material_type" class="w-full"><el-option v-for="item in MATERIAL_TYPES" :key="item.value" :label="item.label" :value="item.value" /></el-select></el-form-item>
            <el-form-item label="题材"><el-select v-model="form.genre" filterable allow-create default-first-option clearable class="w-full" placeholder="例如：悬疑"><el-option v-for="genre in ['悬疑','都市','古装','科幻','爱情','校园','犯罪','喜剧']" :key="genre" :label="genre" :value="genre" /></el-select></el-form-item>
            <el-form-item label="一句话概述" class="span-2"><el-input v-model="form.summary" type="textarea" :rows="2" maxlength="300" show-word-limit placeholder="用一个动作或困境概括它，而不是只写主题" /></el-form-item>
          </div>
        </section>

        <section class="form-section">
          <h3>创作内容 <small>支持 Markdown</small></h3>
          <el-form-item><el-input v-model="form.content" type="textarea" :rows="10" placeholder="## 核心设定\n\n在这里展开人物、场景或桥段……" /></el-form-item>
        </section>

        <section class="form-section">
          <h3>{{ dynamicFields.length ? '类型专属信息' : '扩展信息' }}</h3>
          <div v-if="dynamicFields.length" class="form-grid two">
            <el-form-item v-for="field in dynamicFields" :key="field.key" :label="field.label" :class="{ 'span-2': field.multiline }">
              <el-input :model-value="String(form.metadata[field.key] ?? '')" :type="field.multiline ? 'textarea' : 'text'" :rows="field.multiline ? 3 : undefined" @update:model-value="form.metadata[field.key] = $event" />
            </el-form-item>
          </div>
          <el-form-item v-else label="Metadata JSON"><el-input v-model="rawMetadata" type="textarea" :rows="7" spellcheck="false" /></el-form-item>
        </section>

        <section class="form-section">
          <h3>归档与来源</h3>
          <div class="form-grid two">
            <el-form-item label="标签"><el-select v-model="form.tag_names" multiple filterable allow-create default-first-option class="w-full" placeholder="选择或输入新标签"><el-option v-for="tag in tags" :key="tag.id" :label="tag.name" :value="tag.name" /></el-select></el-form-item>
            <el-form-item label="所属项目"><el-select v-model="form.project_id" clearable class="w-full"><el-option v-for="project in projects" :key="project.id" :label="project.name" :value="project.id" /></el-select></el-form-item>
            <el-form-item label="状态"><el-select v-model="form.status" class="w-full"><el-option v-for="(label, value) in STATUS_LABELS" :key="value" :label="label" :value="value" /></el-select></el-form-item>
            <el-form-item label="来源类型"><el-select v-model="form.source_type" class="w-full"><el-option v-for="(label, value) in SOURCE_LABELS" :key="value" :label="label" :value="value" /></el-select></el-form-item>
            <el-form-item label="来源链接"><el-input v-model="form.source_url" placeholder="https://" /></el-form-item>
            <el-form-item label="封面链接"><el-input v-model="form.cover_url" placeholder="https://" /></el-form-item>
            <el-form-item v-if="isEditing" label="本次修改说明" class="span-2"><el-input v-model="form.change_note" maxlength="200" placeholder="例如：补充人物动机与关系" /></el-form-item>
          </div>
        </section>
      </el-form>
    </div>

    <template #footer>
      <div class="drawer-footer">
        <span>{{ dirty ? '● 有未保存修改' : '✓ 内容已保存' }}</span>
        <div><el-button @click="beforeClose(() => emit('update:modelValue', false))">取消</el-button><el-button type="primary" :icon="Check" :loading="saving" @click="save(false)">保存素材</el-button></div>
      </div>
    </template>
  </el-drawer>
</template>

<style scoped>
.form-shell { min-height: 100%; padding: 0 24px 100px; }.form-status { height: 40px; display: flex; align-items: center; justify-content: space-between; margin: 0 -24px 20px; padding: 0 24px; background: var(--bg-soft); border-bottom: 1px solid var(--border-soft); color: var(--text-muted); font-size: 10px; }.form-status span { display: flex; align-items: center; gap: 6px; }.form-status b { color: var(--text-secondary); font-weight: 550; }
.form-section { padding: 4px 0 20px; }.form-section + .form-section { padding-top: 20px; border-top: 1px solid var(--border-soft); }.form-section h3 { margin: 0 0 16px; color: var(--text); font-size: 13px; }.form-section h3 small { margin-left: 6px; color: var(--text-muted); font-size: 9px; font-weight: 500; }.form-grid { display: grid; gap: 0 14px; }.form-grid.two { grid-template-columns: 1fr 1fr; }.span-2 { grid-column: span 2; }.w-full { width: 100%; }.drawer-footer { width: 100%; display: flex; align-items: center; justify-content: space-between; }.drawer-footer > span { color: var(--text-muted); font-size: 10px; }.drawer-footer > div { display: flex; gap: 8px; }
@media (max-width: 600px) { .form-grid.two { grid-template-columns: 1fr; }.span-2 { grid-column: span 1; } }
</style>
