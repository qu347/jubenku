<script setup lang="ts">
import { computed, ref } from 'vue'
import { Download, Moon, Plus, Search, Sunny, Upload } from '@element-plus/icons-vue'

const props = defineProps<{ modelValue: string; importing?: boolean }>()
const emit = defineEmits<{
  'update:modelValue': [value: string]
  add: []
  import: [file: File]
  export: []
}>()

const fileInput = ref<HTMLInputElement>()
const theme = ref(localStorage.getItem('script-library-theme') || 'dark')
const isDark = computed(() => theme.value === 'dark')

function toggleTheme() {
  theme.value = isDark.value ? 'light' : 'dark'
  document.documentElement.dataset.theme = theme.value
  localStorage.setItem('script-library-theme', theme.value)
}

function chooseFile() {
  fileInput.value?.click()
}

function handleFile(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) emit('import', file)
  target.value = ''
}
</script>

<template>
  <header class="app-header">
    <div class="brand-block">
      <div class="brand-mark"><span>剧</span></div>
      <div>
        <div class="brand-name">剧本素材库</div>
        <div class="brand-caption desktop-only">STORY ELEMENTS</div>
      </div>
    </div>

    <div class="global-search">
      <el-icon><Search /></el-icon>
      <input
        :value="props.modelValue"
        placeholder="搜索标题、正文、标签、人物或项目…"
        aria-label="全局搜索"
        @input="emit('update:modelValue', ($event.target as HTMLInputElement).value)"
      />
      <kbd class="desktop-only">⌘ K</kbd>
    </div>

    <div class="header-actions">
      <input ref="fileInput" type="file" accept="application/json,.json" hidden @change="handleFile" />
      <el-button class="desktop-only" :icon="Upload" :loading="importing" @click="chooseFile">导入</el-button>
      <el-button class="desktop-only" :icon="Download" @click="emit('export')">导出</el-button>
      <el-tooltip :content="isDark ? '切换浅色主题' : '切换深色主题'">
        <button class="icon-button" aria-label="切换主题" @click="toggleTheme">
          <el-icon><Moon v-if="isDark" /><Sunny v-else /></el-icon>
        </button>
      </el-tooltip>
      <el-button type="primary" :icon="Plus" @click="emit('add')"><span class="desktop-only">新增素材</span><span class="mobile-add">新增</span></el-button>
      <div class="avatar" title="本地创作者">创</div>
    </div>
  </header>
</template>

<style scoped>
.app-header { height: 68px; position: sticky; top: 0; z-index: 20; display: grid; grid-template-columns: 244px minmax(260px, 650px) 1fr; align-items: center; gap: 24px; padding: 0 24px; background: color-mix(in srgb, var(--bg-soft) 92%, transparent); border-bottom: 1px solid var(--border-soft); backdrop-filter: blur(14px); }
.brand-block { display: flex; align-items: center; gap: 11px; }
.brand-mark { width: 34px; height: 34px; display: grid; place-items: center; border-radius: 9px; background: var(--accent); color: #17110a; font-family: "Songti SC", serif; font-size: 18px; font-weight: 900; box-shadow: inset 0 0 0 1px rgba(255,255,255,.25); }
.brand-name { font-size: 16px; font-weight: 750; letter-spacing: .02em; }
.brand-caption { margin-top: 2px; color: var(--text-muted); font-size: 8px; font-weight: 700; letter-spacing: .22em; }
.global-search { height: 38px; display: flex; align-items: center; gap: 10px; padding: 0 12px; background: var(--panel); border: 1px solid var(--border); border-radius: 9px; color: var(--text-muted); transition: border-color .2s, box-shadow .2s; }
.global-search:focus-within { border-color: color-mix(in srgb, var(--accent) 70%, var(--border)); box-shadow: 0 0 0 3px var(--accent-soft); }
.global-search input { flex: 1; min-width: 0; border: 0; outline: 0; background: transparent; color: var(--text); font-size: 13px; }
.global-search input::placeholder { color: var(--text-muted); }
kbd { padding: 2px 6px; border: 1px solid var(--border); border-radius: 5px; background: var(--panel-raised); color: var(--text-muted); font: 10px/1.5 monospace; }
.header-actions { display: flex; align-items: center; justify-content: flex-end; gap: 8px; }
.icon-button { width: 36px; height: 36px; display: grid; place-items: center; border: 1px solid var(--border); border-radius: 8px; background: var(--panel); color: var(--text-secondary); cursor: pointer; }
.icon-button:hover { background: var(--panel-hover); color: var(--text); }
.avatar { width: 34px; height: 34px; display: grid; place-items: center; border-radius: 50%; background: linear-gradient(135deg, #475569, #1e293b); border: 1px solid #5a6780; color: white; font-size: 12px; font-weight: 700; }
.mobile-add { display: none; }
@media (max-width: 1100px) { .app-header { grid-template-columns: 210px minmax(220px, 1fr) auto; padding: 0 18px; gap: 16px; } }
@media (max-width: 760px) { .app-header { height: auto; min-height: 64px; grid-template-columns: 1fr auto; padding: 12px 14px; } .global-search { grid-column: 1 / -1; grid-row: 2; width: 100%; } .avatar { display: none; } .mobile-add { display: inline; } }
</style>

