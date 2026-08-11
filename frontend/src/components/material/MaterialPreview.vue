<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { Document, Download } from '@element-plus/icons-vue'
import { downloadMaterial } from '../../api/materials'
import type { Material } from '../../types/material'

const props=defineProps<{ material: Material }>()
const emit=defineEmits<{ download: [] }>()
const url=ref('')
const textContent=ref('')
const loading=ref(false)
const error=ref('')
const previewable=['jpg','jpeg','png','pdf','txt','md']
const extension=computed(()=>props.material.file_extension.toLowerCase().replace(/^\./,''))
function cleanup(){if(url.value)URL.revokeObjectURL(url.value);url.value='';textContent.value=''}
async function load(){cleanup();error.value='';if(!props.material.has_attachment||!previewable.includes(extension.value))return;loading.value=true;try{const blob=await downloadMaterial(props.material.id);if(['txt','md'].includes(extension.value))textContent.value=await blob.text();else url.value=URL.createObjectURL(blob)}catch(reason){error.value=reason instanceof Error?reason.message:'预览加载失败'}finally{loading.value=false}}
watch(()=>props.material.id,load,{immediate:true});onBeforeUnmount(cleanup)
</script>

<template>
  <div v-loading="loading" class="preview-shell">
    <div v-if="!material.has_attachment" class="preview-state"><el-icon><Document/></el-icon><b>该素材没有附件</b><span>这是升级前保留的素材记录，可继续查看、编辑元数据或安全删除。</span></div>
    <div v-else-if="error" class="preview-state"><el-icon><Document/></el-icon><b>无法加载预览</b><span>{{ error }}</span><el-button :icon="Download" @click="emit('download')">下载原文件</el-button></div>
    <img v-else-if="url && ['jpg','jpeg','png'].includes(extension)" :src="url" :alt="material.title">
    <iframe v-else-if="url && extension==='pdf'" :src="url" title="PDF 预览" />
    <pre v-else-if="textContent">{{ textContent }}</pre>
    <div v-else-if="!loading" class="preview-state"><el-icon><Document/></el-icon><b>{{ material.original_filename }}</b><span>此格式暂不提供在线预览，可下载后使用本地应用查看。</span><el-button :icon="Download" @click="emit('download')">下载原文件</el-button></div>
  </div>
</template>

<style scoped>
.preview-shell{min-height:310px;display:grid;place-items:center;border:1px solid var(--border-soft);border-radius:9px;background:#080c16;overflow:hidden}.preview-shell img{max-width:100%;max-height:520px;object-fit:contain}.preview-shell iframe{width:100%;height:520px;border:0}.preview-shell pre{width:100%;max-height:520px;margin:0;padding:20px;color:#d6deeb;font:11px/1.8 ui-monospace,monospace;white-space:pre-wrap;overflow:auto}.preview-state{display:grid;justify-items:center;gap:9px;padding:35px;text-align:center}.preview-state .el-icon{font-size:38px;color:var(--accent)}.preview-state b{font-size:12px}.preview-state span{max-width:360px;color:var(--text-muted);font-size:9px;line-height:1.6}
</style>
