<script setup lang="ts">
import { CopyDocument, Delete, EditPen, MoreFilled, RefreshLeft, Star, View } from '@element-plus/icons-vue'
import { STATUS_LABELS, typeInfo } from '../config/materials'
import type { Material } from '../types'
import { formatRelative } from '../utils/format'

const props = defineProps<{ material: Material }>()
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
  <article class="material-card" tabindex="0" @click="emit('open', material)" @keydown.enter="emit('open', material)">
    <div class="card-accent" :style="{ background: typeInfo(material.material_type).color }"></div>
    <header class="card-header">
      <span class="type-badge" :style="{ color: typeInfo(material.material_type).color, background: `color-mix(in srgb, ${typeInfo(material.material_type).color} 12%, transparent)` }">
        <el-icon><component :is="typeInfo(material.material_type).icon" /></el-icon>{{ typeInfo(material.material_type).label }}
      </span>
      <div class="card-actions" @click.stop>
        <button class="star-button" :class="{ active: material.favorite }" :aria-label="material.favorite ? '取消收藏' : '收藏'" @click="emit('favorite', material)">
          <el-icon><Star /></el-icon>
        </button>
        <el-dropdown trigger="click">
          <button class="more-button" aria-label="更多操作"><el-icon><MoreFilled /></el-icon></button>
          <template #dropdown>
            <el-dropdown-menu v-if="!material.deleted_at">
              <el-dropdown-item :icon="View" @click="emit('open', material)">查看详情</el-dropdown-item>
              <el-dropdown-item :icon="EditPen" @click="emit('edit', material)">编辑素材</el-dropdown-item>
              <el-dropdown-item :icon="CopyDocument" @click="emit('duplicate', material)">创建副本</el-dropdown-item>
              <el-dropdown-item :icon="Delete" divided @click="emit('remove', material)">移入回收站</el-dropdown-item>
            </el-dropdown-menu>
            <el-dropdown-menu v-else>
              <el-dropdown-item :icon="RefreshLeft" @click="emit('restore', material)">恢复素材</el-dropdown-item>
              <el-dropdown-item :icon="Delete" divided @click="emit('permanent', material)">永久删除</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </header>

    <h3>{{ material.title }}</h3>
    <p class="summary truncate-2">{{ material.summary || '还没有填写一句话概述。' }}</p>

    <div class="tag-row">
      <span v-if="material.genre" class="genre-tag">{{ material.genre }}</span>
      <span v-for="tag in material.tags.slice(0, 2)" :key="tag.id" class="tag"># {{ tag.name }}</span>
      <span v-if="material.tags.length > 2" class="tag more">+{{ material.tags.length - 2 }}</span>
    </div>

    <div v-if="material.metadata.characters || material.metadata.name" class="relation-line">
      <span>{{ material.metadata.characters ? '出场' : '角色' }}</span>
      <b>{{ String(material.metadata.characters || material.metadata.name) }}</b>
    </div>

    <footer>
      <div class="status-wrap">
        <span class="status-dot" :class="material.status"></span>
        <span>{{ STATUS_LABELS[material.status] }}</span>
      </div>
      <span class="project-name">{{ material.project?.name || '未归项目' }}</span>
      <span class="updated">{{ formatRelative(material.updated_at) }}</span>
      <span class="usage">用过 {{ material.usage_count }} 次</span>
    </footer>
  </article>
</template>

<style scoped>
.material-card { position: relative; min-width: 0; min-height: 260px; display: flex; flex-direction: column; padding: 17px; overflow: hidden; background: var(--panel); border: 1px solid var(--border-soft); border-radius: 10px; outline: none; cursor: pointer; transition: transform .18s ease, border-color .18s ease, background .18s ease, box-shadow .18s ease; }
.material-card:hover, .material-card:focus-visible { transform: translateY(-2px); border-color: var(--border); background: var(--panel-raised); box-shadow: 0 14px 35px rgba(0, 0, 0, .16); }
.card-accent { position: absolute; top: 0; left: 0; width: 3px; height: 100%; opacity: .8; }
.card-header, .card-actions, footer, .status-wrap { display: flex; align-items: center; }
.card-header { justify-content: space-between; }
.type-badge { height: 25px; display: inline-flex; align-items: center; gap: 6px; padding: 0 8px; border-radius: 6px; font-size: 10px; font-weight: 700; letter-spacing: .03em; }
.card-actions { gap: 2px; }
.star-button, .more-button { width: 28px; height: 28px; display: grid; place-items: center; border: 0; border-radius: 6px; background: transparent; color: var(--text-muted); cursor: pointer; }
.star-button:hover, .more-button:hover { background: var(--panel-hover); color: var(--text); }
.star-button.active { color: var(--accent); }
h3 { margin: 16px 0 8px; color: var(--text); font-family: "Songti SC", "STSong", serif; font-size: 17px; line-height: 1.35; font-weight: 700; letter-spacing: .015em; }
.summary { min-height: 42px; margin: 0 0 13px; color: var(--text-secondary); font-size: 12px; line-height: 1.75; }
.tag-row { min-height: 25px; display: flex; align-items: center; gap: 5px; overflow: hidden; }
.genre-tag, .tag { flex: 0 0 auto; padding: 3px 7px; border-radius: 5px; font-size: 9px; font-weight: 650; }
.genre-tag { background: rgba(59, 130, 246, .12); color: #7db3ff; }.tag { background: rgba(139, 92, 246, .1); color: #b7a0ee; }.tag.more { background: var(--panel-hover); color: var(--text-muted); }
.relation-line { margin-top: 12px; display: flex; gap: 7px; color: var(--text-muted); font-size: 10px; }.relation-line b { overflow: hidden; color: var(--text-secondary); font-weight: 550; text-overflow: ellipsis; white-space: nowrap; }
footer { flex-wrap: wrap; gap: 7px 10px; margin-top: auto; padding-top: 15px; border-top: 1px solid var(--border-soft); color: var(--text-muted); font-size: 9px; }
.status-wrap { gap: 5px; }.status-dot { width: 5px; height: 5px; border-radius: 50%; background: #64748b; }.status-dot.completed { background: #34d399; }.status-dot.improving { background: #60a5fa; }.status-dot.archived { background: #94a3b8; }.status-dot.draft { background: #f59e0b; }
.project-name { max-width: 90px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }.updated { margin-left: auto; }.usage { width: 100%; }
</style>

