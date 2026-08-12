<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { Download, EditPen } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import MaterialPreview from './MaterialPreview.vue'
import StandardTagSelector from './StandardTagSelector.vue'
import UploadPlatformSelect from './UploadPlatformSelect.vue'
import type { GenreModule } from '../../types/genreModule'
import type { Material, MaterialUpdatePayload } from '../../types/material'
import { formatDateTime } from '../../utils/format'
import { decodeStandardTags, readableTag, standardTagGroups } from '../../utils/materialTaxonomy'

const open = defineModel<boolean>({ required: true })
const props = withDefaults(defineProps<{ material: Material | null; modules: GenreModule[]; initialMode?: 'view' | 'edit'; saving?: boolean; libraryType?: 'material' | 'script' }>(), { libraryType: 'material' })
const emit = defineEmits<{ save: [payload: MaterialUpdatePayload]; download: [material: Material] }>()
const form = reactive({ title: '', genre_module_id: '', tags: [] as string[], description: '', uploaded_by: '', project_owner: '', upload_platform: '', platform_heat: null as number | null })
const mode = ref<'view' | 'edit'>('view')

watch([open, () => props.material, () => props.initialMode], () => {
  mode.value = props.initialMode || 'view'
  if (props.material) Object.assign(form, {
    title: props.material.title,
    genre_module_id: props.material.genre_module_id || '',
    tags: [...props.material.tags],
    description: props.material.description || props.material.legacy_summary || '',
    uploaded_by: props.material.uploaded_by || '',
    project_owner: props.material.project_owner || '',
    upload_platform: props.material.upload_platform || '',
    platform_heat: props.material.platform_heat,
  })
}, { immediate: true })

const groupedTags = computed(() => {
  const decoded = decodeStandardTags(props.material?.tags || [])
  return [
    ...standardTagGroups.map((group) => ({ key: group.key, label: group.label, values: decoded.selections[group.key] })),
    { key: 'custom', label: '自定义标签', values: decoded.passthrough },
  ].filter((group) => group.values.length)
})
const storyText = computed(() => props.material?.content_text || props.material?.legacy_content || '')
const fileExtension = computed(() => (props.material?.file_extension || '').toLowerCase().replace(/^\./, ''))
const textPreviewFallback = computed(() => Boolean(props.material?.has_attachment && !storyText.value && ['md', 'txt'].includes(fileExtension.value)))

function edit() { mode.value = 'edit' }
function save() {
  const title = form.title.trim()
  if (!title) return ElMessage.warning('标题不能为空')
  if (title.length > 100) return ElMessage.warning('标题不能超过 100 个字符')
  if (!form.genre_module_id) return ElMessage.warning('请选择题材')
  if (!form.description.trim()) return ElMessage.warning('请填写摘要')
  if (!form.uploaded_by.trim()) return ElMessage.warning('请填写上传人')
  if (!form.project_owner.trim()) return ElMessage.warning('请填写对接项目负责人')
  const selections = decodeStandardTags(form.tags).selections
  if (!selections.plot.length) return ElMessage.warning('请至少选择一个剧情标签')
  if (!selections.era.length) return ElMessage.warning('请选择一个时代背景')
  const payload: MaterialUpdatePayload = {
    title,
    genre_module_id: form.genre_module_id,
    material_type: '剧情',
    tags: form.tags,
    source: '',
    description: form.description.trim(),
    uploaded_by: form.uploaded_by.trim(),
    project_owner: form.project_owner.trim(),
  }
  if (props.libraryType === 'material') {
    const uploadPlatform = form.upload_platform.trim() || null
    const hasPlatform = uploadPlatform !== null
    const hasHeat = form.platform_heat !== null && form.platform_heat !== undefined
    if (hasPlatform !== hasHeat) return ElMessage.warning('请同时填写上传平台和平台热度，或同时清空')
    payload.upload_platform = uploadPlatform
    payload.platform_heat = hasHeat ? form.platform_heat : null
  }
  emit('save', payload)
}
function size(value: number) { return value < 1024 ** 2 ? `${(value / 1024).toFixed(1)} KB` : `${(value / 1024 ** 2).toFixed(1)} MB` }
</script>

<template>
  <el-drawer v-model="open" :title="mode === 'edit' ? `编辑${libraryType === 'script' ? '剧本' : '素材'}信息` : `${libraryType === 'script' ? '剧本' : '素材'}详情`" size="760px">
    <div v-if="material" class="detail-body">
      <template v-if="mode === 'view'">
        <div class="detail-heading"><span>{{ material.has_attachment ? material.file_extension.toUpperCase() : '正文' }}</span><div><h2>{{ material.title }}</h2><p>{{ material.description || material.legacy_summary || '暂无摘要' }}</p></div></div>
        <dl>
          <div><dt>上传人</dt><dd>{{ material.uploaded_by || '未填写' }}</dd></div>
          <div><dt>对接项目负责人</dt><dd>{{ material.project_owner || '未填写' }}</dd></div>
          <div><dt>上传时间</dt><dd>{{ formatDateTime(material.created_at) }}</dd></div>
          <div><dt>所属题材</dt><dd>{{ material.genre_module?.name || '—' }}</dd></div>
          <div><dt>{{ libraryType === 'script' ? '剧本类型' : '素材类型' }}</dt><dd>剧情</dd></div>
          <template v-if="libraryType === 'material'"><div><dt>上传平台</dt><dd>{{ material.upload_platform || '平台信息待补充' }}</dd></div><div><dt>平台热度</dt><dd>{{ material.platform_heat ?? '平台信息待补充' }}</dd></div></template>
          <div><dt>附件</dt><dd>{{ material.has_attachment ? `${material.original_filename} · ${size(material.file_size)}` : '旧记录，无附件' }}</dd></div>
        </dl>

        <section v-if="groupedTags.length" class="detail-section taxonomy-summary"><h3>标准素材标签</h3><div v-for="group in groupedTags" :key="group.key"><b>{{ group.label }}</b><span v-for="tag in group.values" :key="tag">{{ readableTag(tag) }}</span></div></section>
        <section class="story-section"><header><div><span>STORY CONTENT</span><h3>剧情正文</h3></div><el-button v-if="material.has_attachment" :icon="Download" @click="emit('download', material)">下载原文件</el-button></header><article v-if="storyText">{{ storyText }}</article><MaterialPreview v-else-if="textPreviewFallback" class="inline-preview" :material="material" @download="emit('download', material)" /><div v-else class="no-story"><b>当前格式暂不支持直接阅读</b><span>{{ material.has_attachment ? '请下载原文件查看完整剧情内容。MD、TXT、CSV 和 DOCX 可直接预览。' : '这条旧素材没有正文内容。' }}</span></div><p v-if="material.content_truncated" class="truncated">正文较长，此处展示前 50 万字节；请下载原文件阅读全文。</p></section>
        <MaterialPreview v-if="material.has_attachment && !storyText && !textPreviewFallback" :material="material" @download="emit('download', material)" />
      </template>

      <el-form v-else label-position="top">
        <el-form-item label="标题" required><el-input v-model="form.title" maxlength="100" show-word-limit /></el-form-item>
        <el-form-item label="摘要" required><el-input v-model="form.description" type="textarea" :rows="3" maxlength="20000" show-word-limit /></el-form-item>
        <div class="edit-grid"><el-form-item label="上传人" required><el-input v-model="form.uploaded_by" maxlength="100" /></el-form-item><el-form-item label="对接项目负责人" required><el-input v-model="form.project_owner" maxlength="100" /></el-form-item></div>
        <div v-if="libraryType === 'material'" class="edit-grid"><el-form-item label="上传平台"><UploadPlatformSelect v-model="form.upload_platform" select-test-id="edit-platform" /></el-form-item><el-form-item label="平台热度"><el-input-number v-model="form.platform_heat" :min="0" :max="100" :step="1" class="full" /></el-form-item></div>
        <el-form-item label="所属题材" required><el-select v-model="form.genre_module_id" filterable class="full"><el-option v-for="item in modules" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
        <div class="taxonomy-field"><div class="taxonomy-title"><b>标准素材标签</b><span>剧情和角色可多选，时代背景为单选；可补充自定义标签</span></div><StandardTagSelector v-model="form.tags" /></div>
        <div class="locked-file"><b>文件字段不可编辑</b><span>{{ material.has_attachment ? `${material.original_filename} · ${size(material.file_size)} · ${material.mime_type}` : '该旧素材记录没有附件' }}</span></div>
      </el-form>
    </div>
    <template #footer><el-button @click="open=false">关闭</el-button><template v-if="material"><el-button v-if="mode === 'view' && material.has_attachment" :icon="Download" @click="emit('download', material)">下载</el-button><el-button v-if="mode === 'view'" type="primary" :icon="EditPen" @click="edit">编辑信息</el-button><el-button v-else type="primary" :loading="saving" @click="save">保存修改</el-button></template></template>
  </el-drawer>
</template>

<style scoped>
.detail-body{padding:22px 26px 42px}.detail-heading{display:flex;align-items:flex-start;gap:14px;margin-bottom:20px}.detail-heading>span{display:grid;place-items:center;width:58px;height:50px;flex:0 0 auto;border-radius:9px;background:var(--accent-soft);color:var(--accent);font-size:12px;font-weight:900}.detail-heading h2{margin:0;font-family:"Songti SC",serif;font-size:24px}.detail-heading p{margin:7px 0 0;color:var(--text-muted);font-size:14px;line-height:1.65}dl{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin:16px 0 22px;background:var(--border-soft);border:1px solid var(--border-soft);border-radius:9px;overflow:hidden}dl div{padding:14px;background:var(--panel-raised)}dt{color:var(--text-muted);font-size:11px}dd{margin:6px 0 0;color:var(--text-secondary);font-size:13px;line-height:1.5;word-break:break-word}.detail-section{padding:17px 0;border-top:1px solid var(--border-soft)}.detail-section h3{margin:0 0 11px;font-size:14px}.taxonomy-summary>div{display:flex;align-items:center;gap:7px;flex-wrap:wrap;margin-top:9px}.taxonomy-summary b{width:72px;color:var(--text-muted);font-size:11px}.taxonomy-summary span{padding:5px 9px;border:1px solid var(--border);border-radius:999px;color:var(--text-secondary);font-size:12px}.story-section{margin-top:18px;border:1px solid var(--border-soft);border-radius:11px;background:var(--panel-raised);overflow:hidden}.story-section>header{display:flex;align-items:center;justify-content:space-between;padding:16px 18px;border-bottom:1px solid var(--border-soft)}.story-section header span{color:var(--accent);font-size:10px;font-weight:800;letter-spacing:.14em}.story-section h3{margin:4px 0 0;font-size:16px}.story-section article{padding:24px;color:var(--text-secondary);font-size:15px;line-height:1.9;white-space:pre-wrap;word-break:break-word}.story-section :deep(.inline-preview){border:0;border-radius:0}.story-section :deep(.inline-preview pre){font-size:14px;line-height:1.9}.no-story{display:grid;justify-items:center;gap:8px;padding:48px 22px;color:var(--text-muted);text-align:center}.no-story b{color:var(--text);font-size:15px}.no-story span{font-size:13px}.truncated{margin:0;padding:10px 17px;background:var(--accent-soft);color:var(--accent);font-size:12px}.edit-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.full{width:100%}.taxonomy-field{margin:8px 0 18px;padding:16px;border:1px solid var(--border-soft);border-radius:10px;background:var(--panel-raised)}.taxonomy-title{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}.taxonomy-title b{font-size:14px}.taxonomy-title span{color:var(--text-muted);font-size:12px}.locked-file{display:grid;gap:5px;padding:13px;border:1px solid var(--border-soft);border-radius:8px;background:var(--panel-raised)}.locked-file b{font-size:13px}.locked-file span{color:var(--text-muted);font-size:12px}@media(max-width:680px){dl,.edit-grid{grid-template-columns:1fr}.taxonomy-title{align-items:flex-start;gap:4px;flex-direction:column}}
</style>
