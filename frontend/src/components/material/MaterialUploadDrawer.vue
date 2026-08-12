<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Close, DocumentAdd, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useMaterialsStore } from '../../stores/materials'
import type { GenreModule } from '../../types/genreModule'
import type { MaterialUploadFileResult } from '../../types/material'
import StandardTagSelector from './StandardTagSelector.vue'
import UploadPlatformSelect from './UploadPlatformSelect.vue'
import { decodeStandardTags } from '../../utils/materialTaxonomy'

const open = defineModel<boolean>({ required: true })
const props = withDefaults(defineProps<{
  modules: GenreModule[]
  initialGenreId?: string
  initialMaterialType?: string
  libraryType?: 'material' | 'script'
}>(), { initialGenreId: '', initialMaterialType: '', libraryType: 'material' })
const emit = defineEmits<{ complete: [] }>()
const store = useMaterialsStore()
const input = ref<HTMLInputElement>()
const files = ref<File[]>([])
const genreId = ref('')
const title = ref('')
const summary = ref('')
const uploadedBy = ref('')
const projectOwner = ref('')
const uploadPlatform = ref('')
const platformHeat = ref<number | undefined>()
const tags = ref<string[]>([])
const validationMessages = ref<string[]>([])
const uploading = ref(false)
const progress = ref(0)
const results = ref<MaterialUploadFileResult[]>([])
const totalSize = computed(() => files.value.reduce((sum, file) => sum + file.size, 0))
const singleFile = computed(() => files.value.length === 1)
const contentNoun = computed(() => props.libraryType === 'script' ? '剧本' : '素材')

watch([open, () => props.initialGenreId], ([value]) => {
  if (!value) return
  genreId.value = props.initialGenreId || genreId.value || props.modules[0]?.id || ''
}, { immediate: true })

watch(files, (value) => {
  if (value.length === 1 && !title.value.trim()) title.value = value[0].name.replace(/\.[^.]+$/, '')
  if (value.length !== 1) title.value = ''
}, { deep: true })

watch(() => props.libraryType, (value) => {
  if (value === 'script') {
    uploadPlatform.value = ''
    platformHeat.value = undefined
  }
})

function formatSize(value: number) { return value < 1024 ** 2 ? `${(value / 1024).toFixed(1)} KB` : `${(value / 1024 ** 2).toFixed(1)} MB` }
function addFiles(next: FileList | File[]) {
  const existing = new Set(files.value.map((file) => `${file.name}-${file.size}-${file.lastModified}`))
  files.value.push(...Array.from(next).filter((file) => !existing.has(`${file.name}-${file.size}-${file.lastModified}`)))
  results.value = []
}
function onChoose(event: Event) { const target = event.target as HTMLInputElement; if (target.files) addFiles(target.files); target.value = '' }
function onDrop(event: DragEvent) { if (event.dataTransfer?.files) addFiles(event.dataTransfer.files) }
function remove(index: number) { files.value.splice(index, 1) }

async function submit() {
  validationMessages.value = []
  if (!files.value.length) return ElMessage.warning('请先选择至少一个文件')
  if (!genreId.value) return ElMessage.warning('请选择题材')
  if (singleFile.value && !title.value.trim()) return ElMessage.warning('请填写标题')
  if (title.value.trim().length > 100) return ElMessage.warning('标题不能超过 100 个字符')
  if (!summary.value.trim()) return ElMessage.warning('请填写摘要')
  if (summary.value.trim().length > 20_000) return ElMessage.warning('摘要不能超过 20000 个字符')
  if (!uploadedBy.value.trim()) return ElMessage.warning('请填写上传人')
  if (!projectOwner.value.trim()) return ElMessage.warning('请填写对接项目负责人')
  const selections = decodeStandardTags(tags.value).selections
  if (!selections.plot.length) return ElMessage.warning('请至少选择一个剧情标签')
  if (!selections.era.length) return ElMessage.warning('请选择一个时代背景')
  if (props.libraryType === 'material') {
    const errors: string[] = []
    if (!uploadPlatform.value.trim()) errors.push('请选择或输入上传平台')
    if (platformHeat.value === undefined || platformHeat.value === null || platformHeat.value < 0 || platformHeat.value > 100) errors.push('请填写 0 到 100 的平台热度')
    if (errors.length) {
      validationMessages.value = errors
      errors.forEach((message) => ElMessage.warning(message))
      return
    }
  }
  uploading.value = true; progress.value = 0; results.value = []
  try {
    const payload = {
      files: files.value,
      genre_module_id: genreId.value,
      material_type: '剧情',
      title: singleFile.value ? title.value.trim() : '',
      tags: tags.value,
      source: '',
      description: summary.value.trim(),
      uploaded_by: uploadedBy.value.trim(),
      project_owner: projectOwner.value.trim(),
    }
    const result = await store.upload(props.libraryType === 'material'
      ? { ...payload, library_type: 'material', upload_platform: uploadPlatform.value.trim(), platform_heat: platformHeat.value! }
      : { ...payload, library_type: 'script' }, (value) => progress.value = value)
    results.value = result.results
    if (result.failure_count) ElMessage.warning(`成功 ${result.success_count} 个，失败 ${result.failure_count} 个，请查看逐文件结果`)
    else ElMessage.success(`已上传 ${result.success_count} 个${contentNoun.value}文件`)
    if (result.success_count) {
      files.value = []; title.value = ''; summary.value = ''; tags.value = []; uploadPlatform.value = ''; platformHeat.value = undefined
      emit('complete')
    }
  } finally { uploading.value = false }
}
</script>

<template>
  <el-drawer v-model="open" :title="libraryType === 'script' ? '添加剧本' : '添加剧情素材'" size="680px" :close-on-click-modal="!uploading">
    <div class="drawer-body">
      <div class="upload-lead"><el-icon><DocumentAdd /></el-icon><div><b>{{ libraryType === 'script' ? '上传剧本并建立剧本条目' : '上传文件并建立剧情素材条目' }}</b><span>{{ libraryType === 'script' ? '剧本库用于保存编辑观看素材后完成的剧本，上传后可直接阅读正文。' : '素材上传后可供剧本编辑查阅，并会出现在所属题材的标题列表中。' }}</span></div></div>
      <button class="drop-zone" type="button" @click="input?.click()" @dragover.prevent @drop.prevent="onDrop">
        <el-icon><UploadFilled /></el-icon><b>拖拽文件到此处，或点击选择</b><span>推荐 MD / TXT / DOCX，可直接阅读剧情正文；其他格式可下载查看</span>
      </button>
      <input ref="input" hidden type="file" multiple accept=".pdf,.docx,.xlsx,.csv,.txt,.md,.jpg,.jpeg,.png" @change="onChoose">

      <div v-if="files.length" class="pending-list">
        <header><b>待上传 {{ files.length }} 个</b><span>共 {{ formatSize(totalSize) }}</span></header>
        <div v-for="(file,index) in files" :key="`${file.name}-${file.lastModified}`"><span class="file-ext">{{ file.name.split('.').pop()?.toUpperCase() }}</span><p><b>{{ file.name }}</b><small>{{ formatSize(file.size) }}</small></p><el-button text :icon="Close" :disabled="uploading" @click="remove(index)" /></div>
      </div>

      <el-form label-position="top" class="metadata-form">
        <div class="form-grid">
          <el-form-item label="题材" required><el-select v-model="genreId" filterable class="full"><el-option v-for="item in modules" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item>
          <el-form-item :label="libraryType === 'script' ? '剧本类型' : '素材类型'"><el-input model-value="剧情" disabled /></el-form-item>
        </div>
        <div v-if="libraryType === 'material'" class="form-grid">
          <el-form-item label="上传平台" required><UploadPlatformSelect v-model="uploadPlatform" select-test-id="upload-platform" /></el-form-item>
          <el-form-item label="平台热度" required><el-input-number v-model="platformHeat" data-test="platform-heat" :min="0" :max="100" :step="1" class="full" placeholder="0 到 100" /></el-form-item>
        </div>
        <el-form-item label="标题" :required="singleFile"><el-input v-model="title" data-testid="story-title-input" :disabled="!singleFile" maxlength="100" show-word-limit :placeholder="singleFile ? '输入列表中显示的标题' : '批量上传时自动使用文件名作为标题'" /></el-form-item>
        <el-form-item label="摘要" required><el-input v-model="summary" data-testid="story-summary-input" type="textarea" :rows="3" maxlength="20000" show-word-limit placeholder="用一两句话概括剧情钩子、冲突和看点" /></el-form-item>
        <div class="form-grid"><el-form-item label="上传人" required><el-input v-model="uploadedBy" data-testid="uploaded-by-input" maxlength="100" placeholder="例如：张三" /></el-form-item><el-form-item label="对接项目负责人" required><el-input v-model="projectOwner" data-testid="project-owner-input" maxlength="100" placeholder="例如：李制片" /></el-form-item></div>
        <div class="taxonomy-field"><div class="taxonomy-title"><b>标准剧情标签</b><span>剧情和角色可多选，时代背景为单选；可补充自定义标签</span></div><StandardTagSelector v-model="tags" /></div>
      </el-form>

      <div v-if="validationMessages.length" class="validation-messages" role="alert"><span v-for="message in validationMessages" :key="message">{{ message }}</span></div>

      <div v-if="uploading || progress" class="progress"><span><b>上传进度</b><em>{{ progress }}%</em></span><el-progress :percentage="progress" :stroke-width="7" :show-text="false" /></div>
      <div v-if="results.length" class="upload-results"><h3>逐文件处理结果</h3><div v-for="item in results" :key="item.filename" :class="item.success ? 'ok' : 'failed'"><i></i><span><b>{{ item.filename }}</b><small>{{ item.success ? '上传成功' : (item.error || item.message || '上传失败') }}</small></span></div></div>
    </div>
    <template #footer><el-button :disabled="uploading" @click="open=false">关闭</el-button><el-button data-test="submit-upload" type="primary" :loading="uploading" :disabled="!files.length" @click="submit">上传 {{ files.length || '' }} 个文件</el-button></template>
  </el-drawer>
</template>

<style scoped>
.drawer-body{padding:20px 24px 36px}.upload-lead{display:flex;gap:12px;padding:14px;border:1px solid var(--border-soft);border-radius:10px;background:var(--panel-raised);color:var(--accent)}.upload-lead :deep(svg){font-size:22px}.upload-lead b,.upload-lead span{display:block}.upload-lead b{color:var(--text);font-size:12px}.upload-lead span{margin-top:4px;color:var(--text-muted);font-size:9px;line-height:1.6}.drop-zone{width:100%;height:132px;display:grid;place-items:center;align-content:center;gap:8px;margin:14px 0;padding:18px;border:1px dashed #52617a;border-radius:10px;background:color-mix(in srgb,var(--panel-raised) 65%,transparent);color:var(--text);cursor:pointer}.drop-zone:hover{border-color:var(--accent);background:var(--accent-soft)}.drop-zone .el-icon{font-size:30px;color:var(--accent)}.drop-zone b{font-size:12px}.drop-zone span{color:var(--text-muted);font-size:8px}.pending-list{margin-bottom:16px;border:1px solid var(--border-soft);border-radius:8px;overflow:hidden}.pending-list header,.pending-list>div{display:flex;align-items:center;gap:10px;padding:9px 11px;border-bottom:1px solid var(--border-soft)}.pending-list header{justify-content:space-between;background:var(--panel-raised);font-size:9px}.pending-list header span{color:var(--text-muted)}.pending-list>div:last-child{border-bottom:0}.file-ext{width:38px;color:var(--accent);font-size:8px;font-weight:800}.pending-list p{flex:1;margin:0;min-width:0}.pending-list p b,.pending-list p small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pending-list p b{font-size:10px}.pending-list p small{margin-top:3px;color:var(--text-muted);font-size:8px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px}.full{width:100%}.taxonomy-field{margin-top:4px;padding:15px;border:1px solid var(--border-soft);border-radius:10px;background:color-mix(in srgb,var(--panel-raised) 70%,transparent)}.taxonomy-title{display:flex;align-items:center;justify-content:space-between;margin-bottom:16px}.taxonomy-title b{font-size:11px}.taxonomy-title span{color:var(--text-muted);font-size:8px}.validation-messages{display:grid;gap:4px;margin-top:12px;padding:10px 12px;border:1px solid color-mix(in srgb,var(--danger) 50%,var(--border));border-radius:8px;background:color-mix(in srgb,var(--danger) 10%,transparent);color:var(--danger);font-size:11px}.progress{margin-top:14px;padding:12px;border:1px solid var(--border-soft);border-radius:8px}.progress>span{display:flex;justify-content:space-between;margin-bottom:7px;font-size:9px}.progress em{color:var(--accent);font-style:normal}.upload-results{margin-top:12px}.upload-results h3{font-size:10px}.upload-results>div{display:flex;gap:8px;padding:7px;border-bottom:1px solid var(--border-soft)}.upload-results i{width:7px;height:7px;margin-top:4px;border-radius:50%}.upload-results .ok i{background:#34d399}.upload-results .failed i{background:var(--danger)}.upload-results span b,.upload-results span small{display:block;font-size:9px}.upload-results span small{margin-top:3px;color:var(--text-muted)}@media(max-width:650px){.form-grid{grid-template-columns:1fr}.taxonomy-title{align-items:flex-start;gap:4px;flex-direction:column}}
</style>
