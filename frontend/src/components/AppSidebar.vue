<script setup lang="ts">
import { Clock, CollectionTag, Delete, Folder, Star } from '@element-plus/icons-vue'
import { MATERIAL_TYPES } from '../config/materials'
import type { FilterOptions, Filters } from '../types'

const props = defineProps<{ filters: Filters; options: FilterOptions | null }>()
const emit = defineEmits<{ select: [section: { type?: string; favorite?: boolean; recent?: boolean; deleted?: 'active' | 'only' }] ; manage: [] }>()

function activeType(type: string) {
  return props.filters.deleted === 'active' && props.filters.favorite === null && !props.filters.recent && props.filters.type.length === 1 && props.filters.type[0] === type
}

function isAll() {
  return props.filters.deleted === 'active' && props.filters.favorite === null && !props.filters.recent && props.filters.type.length === 0
}
</script>

<template>
  <aside class="sidebar desktop-only">
    <div class="nav-section">
      <div class="nav-label">素材空间</div>
      <button class="nav-item" :class="{ active: isAll() }" @click="emit('select', { deleted: 'active' })">
        <span class="nav-icon"><el-icon><Folder /></el-icon></span><span>全部素材</span><b>{{ options?.stats.total ?? 0 }}</b>
      </button>
      <button
        v-for="item in MATERIAL_TYPES"
        :key="item.value"
        class="nav-item"
        :class="{ active: activeType(item.value) }"
        @click="emit('select', { type: item.value, deleted: 'active' })"
      >
        <span class="nav-icon" :style="{ color: item.color }"><el-icon><component :is="item.icon" /></el-icon></span>
        <span>{{ item.label }}</span><b>{{ options?.material_types[item.value] ?? 0 }}</b>
      </button>
    </div>

    <div class="nav-section utilities">
      <div class="nav-label">快捷访问</div>
      <button class="nav-item" :class="{ active: filters.favorite === true }" @click="emit('select', { favorite: true, deleted: 'active' })">
        <span class="nav-icon amber"><el-icon><Star /></el-icon></span><span>我的收藏</span><b>{{ options?.special_counts.favorite ?? 0 }}</b>
      </button>
      <button class="nav-item" :class="{ active: filters.recent === true }" @click="emit('select', { recent: true, deleted: 'active' })">
        <span class="nav-icon"><el-icon><Clock /></el-icon></span><span>最近使用</span><b>{{ options?.special_counts.recent ?? 0 }}</b>
      </button>
      <button class="nav-item" :class="{ active: filters.deleted === 'only' }" @click="emit('select', { deleted: 'only' })">
        <span class="nav-icon"><el-icon><Delete /></el-icon></span><span>回收站</span><b>{{ options?.special_counts.trash ?? 0 }}</b>
      </button>
      <button class="nav-item manage" @click="emit('manage')">
        <span class="nav-icon"><el-icon><CollectionTag /></el-icon></span><span>项目与标签</span>
      </button>
    </div>

    <div class="sidebar-note">
      <span class="note-kicker">创作提示</span>
      <p>先收藏值得发展的火花，再把它们放进项目中持续打磨。</p>
    </div>
  </aside>
</template>

<style scoped>
.sidebar { width: 244px; height: calc(100vh - 68px); position: sticky; top: 68px; flex: 0 0 244px; overflow-y: auto; padding: 20px 14px; background: var(--bg-soft); border-right: 1px solid var(--border-soft); }
.nav-section + .nav-section { margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--border-soft); }
.nav-label { margin: 0 10px 8px; color: var(--text-muted); font-size: 10px; font-weight: 800; letter-spacing: .12em; text-transform: uppercase; }
.nav-item { width: 100%; min-height: 38px; display: grid; grid-template-columns: 25px 1fr auto; align-items: center; gap: 8px; padding: 7px 10px; border: 0; border-radius: 8px; background: transparent; color: var(--text-secondary); text-align: left; font-size: 13px; cursor: pointer; }
.nav-item:hover { background: var(--panel); color: var(--text); }
.nav-item.active { background: var(--accent-soft); color: var(--text); box-shadow: inset 2px 0 0 var(--accent); }
.nav-item b { min-width: 22px; color: var(--text-muted); font-size: 10px; font-weight: 650; text-align: right; }
.nav-icon { display: grid; place-items: center; color: var(--text-muted); font-size: 15px; }
.nav-icon.amber { color: var(--accent); }
.nav-item.manage { margin-top: 5px; }
.sidebar-note { margin: 28px 4px 10px; padding: 14px; border: 1px solid var(--border-soft); border-radius: 10px; background: linear-gradient(145deg, var(--panel), var(--bg-soft)); }
.note-kicker { color: var(--accent); font-size: 10px; font-weight: 800; letter-spacing: .08em; }
.sidebar-note p { margin: 8px 0 0; color: var(--text-muted); font-size: 11px; line-height: 1.65; }
</style>

