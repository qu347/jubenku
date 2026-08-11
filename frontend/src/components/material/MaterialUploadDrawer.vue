<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { Close, DocumentAdd, UploadFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useMaterialsStore } from '../../stores/materials'
import type { GenreModule } from '../../types/genreModule'
import type { MaterialUploadFileResult } from '../../types/material'

const open = defineModel<boolean>({ required: true })
const props = defineProps<{ modules: GenreModule[] }>()
const emit = defineEmits<{ complete: [] }>()
const store = useMaterialsStore()
const input = ref<HTMLInputElement>()
const files = ref<File[]>([])
const genreId = ref('')
const materialType = ref('研究资料')
const tags = ref('')
const source = ref('')
const description = ref('')
const uploading = ref(false)
const progress = ref(0)
const results = ref<MaterialUploadFileResult[]>([])
const totalSize = computed(() => files.value.reduce((sum, file) => sum + file.size, 0))

watch(open, (value) => { if (value && !genreId.value) genreId.value = props.modules[0]?.id || '' }, { immediate: true })
function formatSize(value:number){return value<1024**2?`${(value/1024).toFixed(1)} KB`:`${(value/1024**2).toFixed(1)} MB`}
function addFiles(next: FileList | File[]) {
  const existing = new Set(files.value.map((file) => `${file.name}-${file.size}-${file.lastModified}`))
  files.value.push(...Array.from(next).filter((file) => !existing.has(`${file.name}-${file.size}-${file.lastModified}`)))
  results.value = []
}
function onChoose(event: Event) { const target=event.target as HTMLInputElement;if(target.files)addFiles(target.files);target.value='' }
function onDrop(event: DragEvent) { if(event.dataTransfer?.files)addFiles(event.dataTransfer.files) }
function remove(index:number){files.value.splice(index,1)}
async function submit() {
  if (!files.value.length) return ElMessage.warning('请先选择至少一个文件')
  if (!genreId.value) return ElMessage.warning('请选择公共题材')
  if (!materialType.value.trim()) return ElMessage.warning('请填写素材类型')
  if (materialType.value.trim().length > 30) return ElMessage.warning('素材类型不能超过 30 个字符')
  const parsedTags = tags.value.split(/[,，]/).map((item) => item.trim()).filter(Boolean)
  if (parsedTags.length > 30 || parsedTags.some((tag) => tag.length > 50)) return ElMessage.warning('最多 30 个标签，单个标签不超过 50 个字符')
  if (source.value.trim().length > 200) return ElMessage.warning('来源不能超过 200 个字符')
  if (description.value.trim().length > 20000) return ElMessage.warning('说明不能超过 20000 个字符')
  uploading.value=true;progress.value=0;results.value=[]
  try {
    const result=await store.upload({ files:files.value, genre_module_id:genreId.value, material_type:materialType.value.trim(), tags:parsedTags, source:source.value.trim(), description:description.value.trim() },(value)=>progress.value=value)
    results.value=result.results
    if(result.failure_count) ElMessage.warning(`成功 ${result.success_count} 个，失败 ${result.failure_count} 个，请查看逐文件结果`)
    else ElMessage.success(`已上传 ${result.success_count} 个文件`)
    if(result.success_count){files.value=[];emit('complete')}
  } finally { uploading.value=false }
}
</script>

<template>
  <el-drawer v-model="open" title="上传企业素材" size="560px" :close-on-click-modal="!uploading">
    <div class="drawer-body">
      <div class="upload-lead"><el-icon><DocumentAdd/></el-icon><div><b>一个文件对应一条素材记录</b><span>可批量拖入文件，并统一设置题材、类型和标签。</span></div></div>
      <button class="drop-zone" type="button" @click="input?.click()" @dragover.prevent @drop.prevent="onDrop">
        <el-icon><UploadFilled /></el-icon><b>拖拽文件到此处，或点击选择</b><span>PDF / DOCX / XLSX / CSV / TXT / MD / JPG / PNG · 单文件最大 100MB</span>
      </button>
      <input ref="input" hidden type="file" multiple accept=".pdf,.docx,.xlsx,.csv,.txt,.md,.jpg,.jpeg,.png" @change="onChoose">
      <div v-if="files.length" class="pending-list"><header><b>待上传 {{ files.length }} 个</b><span>共 {{ formatSize(totalSize) }}</span></header><div v-for="(file,index) in files" :key="`${file.name}-${file.lastModified}`"><span class="file-ext">{{ file.name.split('.').pop()?.toUpperCase() }}</span><p><b>{{ file.name }}</b><small>{{ formatSize(file.size) }}</small></p><el-button text :icon="Close" :disabled="uploading" @click="remove(index)" /></div></div>
      <el-form label-position="top" class="metadata-form">
        <div class="form-grid"><el-form-item label="公共题材" required><el-select v-model="genreId" filterable class="full"><el-option v-for="item in modules" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item><el-form-item label="素材类型" required><el-select v-model="materialType" allow-create filterable class="full"><el-option v-for="item in ['人物设定','剧情桥段','场景参考','世界观','对白素材','研究资料','其他']" :key="item" :label="item" :value="item" /></el-select></el-form-item></div>
        <el-form-item label="公共标签"><el-input v-model="tags" placeholder="多个标签使用逗号分隔" /></el-form-item>
        <el-form-item label="公共来源"><el-input v-model="source" placeholder="例如：品牌档案、研究报告、内部采编" /></el-form-item>
        <el-form-item label="公共说明"><el-input v-model="description" type="textarea" :rows="3" placeholder="说明这批文件的用途与背景" /></el-form-item>
      </el-form>
      <div v-if="uploading || progress" class="progress"><span><b>上传进度</b><em>{{ progress }}%</em></span><el-progress :percentage="progress" :stroke-width="7" :show-text="false" /></div>
      <div v-if="results.length" class="upload-results"><h3>逐文件处理结果</h3><div v-for="item in results" :key="item.filename" :class="item.success?'ok':'failed'"><i></i><span><b>{{ item.filename }}</b><small>{{ item.success ? '上传成功' : (item.error || item.message || '上传失败') }}</small></span></div></div>
    </div>
    <template #footer><el-button :disabled="uploading" @click="open=false">关闭</el-button><el-button type="primary" :loading="uploading" :disabled="!files.length" @click="submit">上传 {{ files.length || '' }} 个文件</el-button></template>
  </el-drawer>
</template>

<style scoped>
.drawer-body{padding:20px 24px 30px}.upload-lead{display:flex;gap:12px;padding:13px;border:1px solid var(--border-soft);border-radius:9px;background:var(--panel-raised);color:var(--accent)}.upload-lead :deep(svg){font-size:22px}.upload-lead b,.upload-lead span{display:block}.upload-lead b{color:var(--text);font-size:11px}.upload-lead span{margin-top:4px;color:var(--text-muted);font-size:9px}.drop-zone{width:100%;height:145px;display:grid;place-items:center;align-content:center;gap:8px;margin:14px 0;padding:18px;border:1px dashed #52617a;border-radius:10px;background:color-mix(in srgb,var(--panel-raised) 65%,transparent);color:var(--text);cursor:pointer}.drop-zone:hover{border-color:var(--accent);background:var(--accent-soft)}.drop-zone .el-icon{font-size:30px;color:var(--accent)}.drop-zone b{font-size:12px}.drop-zone span{color:var(--text-muted);font-size:8px}.pending-list{margin-bottom:16px;border:1px solid var(--border-soft);border-radius:8px;overflow:hidden}.pending-list header,.pending-list>div{display:flex;align-items:center;gap:10px;padding:9px 11px;border-bottom:1px solid var(--border-soft)}.pending-list header{justify-content:space-between;background:var(--panel-raised);font-size:9px}.pending-list header span{color:var(--text-muted)}.pending-list>div:last-child{border-bottom:0}.file-ext{width:38px;color:var(--accent);font-size:8px;font-weight:800}.pending-list p{flex:1;margin:0;min-width:0}.pending-list p b,.pending-list p small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.pending-list p b{font-size:10px}.pending-list p small{margin-top:3px;color:var(--text-muted);font-size:8px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.full{width:100%}.progress{padding:12px;border:1px solid var(--border-soft);border-radius:8px}.progress>span{display:flex;justify-content:space-between;margin-bottom:7px;font-size:9px}.progress em{color:var(--accent);font-style:normal}.upload-results{margin-top:12px}.upload-results h3{font-size:10px}.upload-results>div{display:flex;gap:8px;padding:7px;border-bottom:1px solid var(--border-soft)}.upload-results i{width:7px;height:7px;margin-top:4px;border-radius:50%}.upload-results .ok i{background:#34d399}.upload-results .failed i{background:var(--danger)}.upload-results span b,.upload-results span small{display:block;font-size:9px}.upload-results span small{margin-top:3px;color:var(--text-muted)}
</style>
