<script setup lang="ts">
import { Delete, Download, EditPen, View } from '@element-plus/icons-vue'
import type { Material } from '../../types/material'
import { formatDateTime } from '../../utils/format'

defineProps<{ items: Material[]; loading?: boolean }>()
const emit = defineEmits<{ view: [item: Material]; edit: [item: Material]; download: [item: Material]; delete: [item: Material] }>()

function size(value: number) {
  if (value < 1024) return `${value} B`
  if (value < 1024 ** 2) return `${(value / 1024).toFixed(1)} KB`
  return `${(value / 1024 ** 2).toFixed(1)} MB`
}
</script>

<template>
  <el-table :data="items" v-loading="loading" height="calc(100vh - 410px)" class="material-table">
    <el-table-column label="标题" min-width="230">
      <template #default="scope"><button class="title-cell" @click="emit('view', scope.row)"><b>{{ scope.row.title }}</b><span>{{ scope.row.has_attachment ? scope.row.original_filename : '旧素材记录 · 无附件' }}</span></button></template>
    </el-table-column>
    <el-table-column label="题材" min-width="110"><template #default="scope">{{ scope.row.genre_module?.name || '—' }}</template></el-table-column>
    <el-table-column prop="material_type" label="素材类型" min-width="110" />
    <el-table-column label="文件" width="100"><template #default="scope"><span class="file-pill" :class="{ empty: !scope.row.has_attachment }">{{ scope.row.has_attachment ? scope.row.file_extension.toUpperCase() : '无附件' }}</span></template></el-table-column>
    <el-table-column label="大小" width="95"><template #default="scope">{{ scope.row.has_attachment ? size(scope.row.file_size) : '—' }}</template></el-table-column>
    <el-table-column label="标签" min-width="160"><template #default="scope"><div class="tags"><span v-for="tag in scope.row.tags" :key="tag">{{ tag }}</span><i v-if="!scope.row.tags.length">—</i></div></template></el-table-column>
    <el-table-column prop="source" label="来源" min-width="120" show-overflow-tooltip />
    <el-table-column label="上传时间" width="160"><template #default="scope">{{ formatDateTime(scope.row.created_at) }}</template></el-table-column>
    <el-table-column label="操作" width="190" fixed="right">
      <template #default="scope"><el-button text :icon="View" @click="emit('view',scope.row)">查看</el-button><el-button v-if="scope.row.has_attachment" text :icon="Download" aria-label="下载附件" @click="emit('download',scope.row)" /><el-button v-else text :icon="Download" disabled title="该素材没有附件" aria-label="无附件，无法下载" /><el-button text :icon="EditPen" @click="emit('edit',scope.row)" /><el-button text type="danger" :icon="Delete" @click="emit('delete',scope.row)" /></template>
    </el-table-column>
  </el-table>
</template>

<style scoped>
.material-table{--el-table-bg-color:var(--panel);--el-table-tr-bg-color:var(--panel);--el-table-row-hover-bg-color:var(--panel-hover);--el-table-header-bg-color:var(--panel-raised);--el-table-border-color:var(--border-soft);--el-table-text-color:var(--text-secondary);--el-table-header-text-color:var(--text-muted)}.title-cell{display:grid;gap:4px;padding:0;border:0;background:none;color:var(--text);text-align:left;cursor:pointer}.title-cell span{color:var(--text-muted);font-size:9px}.file-pill{padding:3px 6px;border-radius:4px;background:var(--accent-soft);color:var(--accent);font-size:9px;font-weight:800}.file-pill.empty{background:var(--panel-raised);color:var(--text-muted)}.tags{display:flex;flex-wrap:wrap;gap:4px}.tags span{padding:2px 6px;border:1px solid var(--border);border-radius:99px;color:var(--text-muted);font-size:8px}.tags i{color:var(--text-muted);font-style:normal}
</style>
