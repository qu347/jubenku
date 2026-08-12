<script setup lang="ts">
import { CopyDocument, Delete, EditPen, MoreFilled, RefreshLeft, Star } from '@element-plus/icons-vue'
import { STATUS_LABELS, typeInfo } from '../config/materials'
import type { Material } from '../types'
import { formatRelative } from '../utils/format'

defineProps<{ materials: Material[] }>()
const emit = defineEmits<{
  open: [material: Material]
  edit: [material: Material]
  favorite: [material: Material]
  duplicate: [material: Material]
  remove: [material: Material]
  restore: [material: Material]
  permanent: [material: Material]
}>()
</script>

<template>
  <div class="table-wrap surface">
    <table>
      <caption class="sr-only">素材列表</caption>
      <thead><tr><th>素材</th><th>题材 / 标签</th><th>状态</th><th>所属项目</th><th>使用</th><th>最后修改</th><th></th></tr></thead>
      <tbody>
        <tr v-for="material in materials" :key="material.id" @click="emit('open', material)">
          <td><div class="material-cell"><span class="type-icon" :style="{ color: typeInfo(material.material_type).color }"><el-icon><component :is="typeInfo(material.material_type).icon" /></el-icon></span><div><strong>{{ material.title }}</strong><small>{{ typeInfo(material.material_type).label }} · {{ material.summary || '暂无概述' }}</small></div></div></td>
          <td><div class="tags"><span v-if="material.genre">{{ material.genre }}</span><span v-for="tag in material.tags.slice(0, 2)" :key="tag.id">#{{ tag.name }}</span></div></td>
          <td><span class="status"><i :class="material.status"></i>{{ STATUS_LABELS[material.status] }}</span></td>
          <td>{{ material.project?.name || '未归项目' }}</td>
          <td>{{ material.usage_count }} 次</td>
          <td>{{ formatRelative(material.updated_at) }}</td>
          <td @click.stop><div class="row-actions"><button :class="{ active: material.favorite }" @click="emit('favorite', material)"><el-icon><Star /></el-icon></button><el-dropdown trigger="click"><button><el-icon><MoreFilled /></el-icon></button><template #dropdown><el-dropdown-menu v-if="!material.deleted_at"><el-dropdown-item :icon="EditPen" @click="emit('edit', material)">编辑</el-dropdown-item><el-dropdown-item :icon="CopyDocument" @click="emit('duplicate', material)">复制</el-dropdown-item><el-dropdown-item :icon="Delete" divided @click="emit('remove', material)">移至回收站</el-dropdown-item></el-dropdown-menu><el-dropdown-menu v-else><el-dropdown-item :icon="RefreshLeft" @click="emit('restore', material)">恢复</el-dropdown-item><el-dropdown-item :icon="Delete" divided @click="emit('permanent', material)">永久删除</el-dropdown-item></el-dropdown-menu></template></el-dropdown></div></td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.table-wrap { overflow-x: auto; border-radius: 10px; } table { width: 100%; min-width: 900px; border-collapse: collapse; font-size: 12px; } th { padding: 12px 14px; background: var(--bg-soft); border-bottom: 1px solid var(--border); color: var(--text-muted); text-align: left; font-size: 10px; letter-spacing: .04em; } td { padding: 13px 14px; border-bottom: 1px solid var(--border-soft); color: var(--text-secondary); } tbody tr { cursor: pointer; } tbody tr:hover { background: var(--panel-raised); } tbody tr:last-child td { border-bottom: 0; }
.material-cell { min-width: 280px; display: flex; align-items: center; gap: 10px; }.type-icon { width: 30px; height: 30px; display: grid; place-items: center; border-radius: 7px; background: var(--panel-hover); }.material-cell strong { display: block; color: var(--text); font-size: 13px; }.material-cell small { display: block; max-width: 300px; margin-top: 4px; overflow: hidden; color: var(--text-muted); text-overflow: ellipsis; white-space: nowrap; }
.tags { display: flex; gap: 5px; }.tags span { padding: 3px 6px; border-radius: 4px; background: var(--panel-hover); color: var(--text-secondary); font-size: 9px; }.status { display: inline-flex; align-items: center; gap: 6px; }.status i { width: 5px; height: 5px; border-radius: 50%; background: #f59e0b; }.status i.completed { background: #34d399; }.status i.improving { background: #60a5fa; }.status i.archived { background: #94a3b8; }.row-actions { display: flex; }.row-actions button { width: 28px; height: 28px; display: grid; place-items: center; border: 0; border-radius: 6px; background: transparent; color: var(--text-muted); cursor: pointer; }.row-actions button:hover { background: var(--panel-hover); color: var(--text); }.row-actions button.active { color: var(--accent); }
</style>
