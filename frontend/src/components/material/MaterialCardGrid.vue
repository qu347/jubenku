<script setup lang="ts">
import { Delete, Download, EditPen, View } from '@element-plus/icons-vue'
import type { Material } from '../../types/material'
import { formatDateTime } from '../../utils/format'
defineProps<{ items: Material[]; loading?: boolean }>()
const emit = defineEmits<{ view: [item: Material]; edit: [item: Material]; download: [item: Material]; delete: [item: Material] }>()
function size(value:number){return value<1024**2?`${(value/1024).toFixed(1)} KB`:`${(value/1024**2).toFixed(1)} MB`}
</script>

<template>
  <div v-loading="loading" class="card-grid">
    <article v-for="item in items" :key="item.id" class="material-card" @dblclick="emit('view',item)">
      <header><span class="ext" :class="{ empty: !item.has_attachment }">{{ item.has_attachment ? item.file_extension.toUpperCase() : '无附件' }}</span><small>{{ item.has_attachment ? size(item.file_size) : '旧记录' }}</small></header>
      <div class="card-body"><b>{{ item.title }}</b><p>{{ item.description || item.legacy_summary || item.legacy_content || '暂无素材说明' }}</p><div class="meta"><span>{{ item.genre_module?.name || '未分类题材' }}</span><span>{{ item.material_type }}</span></div><div class="tags"><i v-for="tag in item.tags.slice(0,3)" :key="tag">{{ tag }}</i><em v-if="item.tags.length>3">+{{ item.tags.length-3 }}</em></div></div>
      <footer><time>{{ formatDateTime(item.created_at) }}</time><div><el-button text :icon="View" @click="emit('view',item)"/><el-button v-if="item.has_attachment" text :icon="Download" aria-label="下载附件" @click="emit('download',item)"/><el-button v-else text :icon="Download" disabled title="该素材没有附件" aria-label="无附件，无法下载"/><el-button text :icon="EditPen" @click="emit('edit',item)"/><el-button text type="danger" :icon="Delete" @click="emit('delete',item)"/></div></footer>
    </article>
  </div>
</template>

<style scoped>
.card-grid{display:grid;grid-template-columns:repeat(4,minmax(210px,1fr));gap:12px;min-height:300px}.material-card{display:flex;min-height:240px;flex-direction:column;border:1px solid var(--border-soft);border-radius:10px;background:var(--panel);overflow:hidden;transition:.2s}.material-card:hover{border-color:color-mix(in srgb,var(--accent) 45%,var(--border));transform:translateY(-2px);box-shadow:var(--shadow)}.material-card header{height:70px;display:flex;align-items:flex-start;justify-content:space-between;padding:14px;background:linear-gradient(135deg,var(--panel-raised),var(--panel))}.ext{display:grid;place-items:center;width:48px;height:38px;border-radius:7px;background:var(--accent-soft);color:var(--accent);font-size:11px;font-weight:900}.ext.empty{width:56px;background:var(--panel-hover);color:var(--text-muted);font-size:9px}.material-card header small{color:var(--text-muted)}.card-body{flex:1;padding:14px}.card-body b{font-size:13px}.card-body p{height:32px;margin:8px 0;color:var(--text-muted);font-size:10px;line-height:1.6;overflow:hidden}.meta{display:flex;gap:7px;color:var(--text-secondary);font-size:9px}.meta span+span:before{content:'·';margin-right:7px;color:var(--border)}.tags{display:flex;gap:4px;margin-top:10px}.tags i,.tags em{padding:2px 5px;border:1px solid var(--border);border-radius:99px;color:var(--text-muted);font-size:8px;font-style:normal}.material-card footer{display:flex;align-items:center;justify-content:space-between;padding:7px 9px;border-top:1px solid var(--border-soft)}.material-card time{color:var(--text-muted);font-size:8px}.material-card footer :deep(.el-button){margin-left:0;padding:5px}@media(max-width:1250px){.card-grid{grid-template-columns:repeat(3,1fr)}}@media(max-width:900px){.card-grid{grid-template-columns:repeat(2,1fr)}}
</style>
