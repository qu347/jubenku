<script setup lang="ts">
import { computed, onMounted, ref, watch, type Component } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as ElementIcons from '@element-plus/icons-vue'
import { Collection, Delete, Download, EditPen, Plus, Refresh, View } from '@element-plus/icons-vue'
import { getGenreModuleBySlug } from '../api/genreModules'
import { deleteMaterial, downloadMaterial, getMaterial, listMaterials, updateMaterial } from '../api/materials'
import { ApiError } from '../api/http'
import MaterialDetailDrawer from '../components/material/MaterialDetailDrawer.vue'
import MaterialFilterBar from '../components/material/MaterialFilterBar.vue'
import MaterialUploadDrawer from '../components/material/MaterialUploadDrawer.vue'
import { useGenreModulesStore } from '../stores/genreModules'
import type { GenreModule, GenreModuleDetail } from '../types/genreModule'
import type { Material, MaterialFilters, MaterialUpdatePayload } from '../types/material'
import { confirmDestructive } from '../utils/confirm'
import { formatDateTime } from '../utils/format'

const props = withDefaults(defineProps<{ libraryType?: 'material' | 'script' }>(), {
  libraryType: 'material',
})
const route = useRoute()
const genreStore = useGenreModulesStore()
const iconRegistry = ElementIcons as Record<string, Component>
const module = ref<GenreModuleDetail | null>(null)
const materials = ref<Material[]>([])
const loading = ref(false)
const contentLoading = ref(false)
const error = ref('')
const contentError = ref('')
const notFound = ref(false)
const uploadOpen = ref(false)
const detailOpen = ref(false)
const selectedMaterial = ref<Material | null>(null)
const detailMode = ref<'view' | 'edit'>('view')
const saving = ref(false)
const materialFilters = ref<MaterialFilters>({ sort: 'created_desc' })

const isInactive = computed(() => module.value?.status !== 'active')
const isScript = computed(() => props.libraryType === 'script')
const contentNoun = computed(() => isScript.value ? '剧本' : '剧情')
const modules = computed<GenreModule[]>(() => {
  if (genreStore.allModules.length) return genreStore.allModules
  if (genreStore.modules.length) return genreStore.modules
  return module.value ? [module.value] : []
})

function summaryOf(item: Material) {
  return item.description || item.legacy_summary || item.legacy_content || '暂无摘要'
}

async function fetchAllMaterials(moduleId: string) {
  const filters = {
    ...materialFilters.value,
    library_type: props.libraryType,
    genre_module_id: moduleId,
    material_type: undefined,
    source: undefined,
  }
  const first = await listMaterials({ ...filters, sort: filters.sort || 'created_desc', page: 1, page_size: 100 })
  if (first.pages <= 1) return first.items
  const rest = await Promise.all(Array.from({ length: first.pages - 1 }, (_, index) => listMaterials({
    ...filters, sort: filters.sort || 'created_desc', page: index + 2, page_size: 100,
  })))
  return [first.items, ...rest.map((page) => page.items)].flat()
}

async function loadMaterials(moduleId: string) {
  contentLoading.value = true
  contentError.value = ''
  try { materials.value = await fetchAllMaterials(moduleId) }
  catch (reason) { contentError.value = reason instanceof Error ? reason.message : `${contentNoun.value}列表加载失败` }
  finally { contentLoading.value = false }
}

async function loadModule() {
  const slug = String(route.params.slug || '')
  loading.value = true; error.value = ''; notFound.value = false; module.value = null; materials.value = []; materialFilters.value = { sort: 'created_desc' }
  try {
    const detail = await getGenreModuleBySlug(slug)
    module.value = detail
    await loadMaterials(detail.id)
  } catch (reason) {
    if (reason instanceof ApiError && reason.status === 404) notFound.value = true
    else error.value = reason instanceof Error ? reason.message : '题材模块加载失败'
  } finally { loading.value = false }
}

async function openDetail(item: Material, mode: 'view' | 'edit' = 'view') {
  try {
    selectedMaterial.value = await getMaterial(item.id)
    detailMode.value = mode
    detailOpen.value = true
  } catch (reason) { ElMessage.error(reason instanceof Error ? reason.message : `${contentNoun.value}详情加载失败`) }
}

async function saveMaterial(payload: MaterialUpdatePayload) {
  if (!selectedMaterial.value || !module.value) return
  saving.value = true
  try {
    await updateMaterial(selectedMaterial.value.id, payload)
    selectedMaterial.value = await getMaterial(selectedMaterial.value.id)
    await loadMaterials(module.value.id)
    detailMode.value = 'view'
    ElMessage.success(`${contentNoun.value}信息已更新`)
  } finally { saving.value = false }
}

async function removeMaterial(item: Material) {
  const scope = item.has_attachment ? '数据库记录与物理文件' : '数据库记录（该素材没有附件）'
  await confirmDestructive(`将永久删除“${item.title}”的${scope}，是否继续？`, `删除${contentNoun.value}`)
  await deleteMaterial(item.id)
  if (selectedMaterial.value?.id === item.id) detailOpen.value = false
  if (module.value) await loadMaterials(module.value.id)
  ElMessage.success(`${contentNoun.value}已删除`)
}

async function download(item: Material) {
  if (!item.has_attachment) return ElMessage.info('该素材没有可下载的附件')
  try {
    const blob = await downloadMaterial(item.id)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url; link.download = item.original_filename; link.click()
    setTimeout(() => URL.revokeObjectURL(url), 0)
  } catch { ElMessage.error('下载失败，请稍后重试') }
}

async function handleUploadComplete() { if (module.value) await loadMaterials(module.value.id) }
async function applyMaterialFilters(filters: MaterialFilters) {
  materialFilters.value = { ...filters, genre_module_id: undefined, material_type: undefined, source: undefined, page: 1, page_size: 100 }
  if (module.value) await loadMaterials(module.value.id)
}
async function resetMaterialFilters() {
  materialFilters.value = { sort: 'created_desc' }
  if (module.value) await loadMaterials(module.value.id)
}

watch([() => route.params.slug, () => props.libraryType], () => void loadModule(), { immediate: true })
onMounted(() => void genreStore.fetchAllModules())
</script>

<template>
  <div class="genre-page">
    <div v-if="loading" class="page-state loading-state"><div class="hero-skeleton"></div><div class="content-skeleton"></div></div>
    <section v-else-if="notFound" class="page-state message-state"><strong>404</strong><h1>题材不存在</h1><p>该题材可能已被删除，或当前地址不正确。</p><RouterLink :to="isScript ? '/scripts' : '/materials'">返回{{ isScript ? '剧本库' : '素材库' }}</RouterLink></section>
    <section v-else-if="error" class="page-state message-state error-state"><el-icon><Collection /></el-icon><h1>题材加载失败</h1><p>{{ error }}</p><el-button :icon="Refresh" @click="loadModule">重新加载</el-button></section>

    <template v-else-if="module">
      <div v-if="isInactive" class="inactive-banner">该题材已停用，仅可通过直接地址访问。</div>
      <header class="genre-hero" :style="{ '--genre-color': module.theme_color }">
        <div class="hero-identity"><span class="module-icon"><el-icon><component :is="iconRegistry[module.icon] || Collection" /></el-icon></span><div><small>{{ isScript ? 'SCRIPT GENRE LIBRARY' : 'MATERIAL GENRE LIBRARY' }}</small><h1>{{ module.name }}</h1><p>{{ module.description || (isScript ? '题材剧本统一归档与检索。' : '题材剧情素材统一归档与检索。') }}</p></div></div>
        <div class="hero-count"><small>{{ isScript ? '剧本标题' : '剧情标题' }}</small><b>{{ materials.length }}</b><span>条已归档内容</span></div>
      </header>

      <main class="module-body">
        <section class="title-module surface">
          <header><div class="module-title"><span><el-icon><Collection /></el-icon></span><div><small>ONLY MODULE</small><h2>标题</h2><p>{{ isScript ? '按标题管理已完成剧本，点击标题查看剧本正文。' : '按标题管理剧情素材，点击标题查看完整剧情。' }}</p></div></div><div class="section-actions"><el-button :icon="Refresh" :loading="contentLoading" @click="loadMaterials(module.id)">刷新</el-button><el-button type="primary" :icon="Plus" @click="uploadOpen = true">添加{{ contentNoun }}</el-button></div></header>

          <MaterialFilterBar class="genre-filter" :model-value="materialFilters" :modules="modules" hide-genre @apply="applyMaterialFilters" @reset="resetMaterialFilters" />

          <div v-if="contentError" class="content-state error-state"><b>{{ contentNoun }}列表加载失败</b><span>{{ contentError }}</span><el-button :icon="Refresh" @click="loadMaterials(module.id)">重新加载</el-button></div>
          <div v-else-if="contentLoading" class="table-loading"><i v-for="item in 5" :key="item"></i></div>
          <div v-else-if="!materials.length" class="content-state"><el-icon><Collection /></el-icon><b>还没有{{ contentNoun }}</b><span>点击右上角“添加{{ contentNoun }}”，上传第一份{{ contentNoun }}文件。</span><el-button type="primary" :icon="Plus" @click="uploadOpen = true">添加{{ contentNoun }}</el-button></div>
          <div v-else class="story-table-wrap">
            <table class="story-table"><thead><tr><th>标题</th><th>摘要</th><th>上传人</th><th>对接项目负责人</th><th>时间</th><th>操作</th></tr></thead><tbody>
              <tr v-for="item in materials" :key="item.id"><td><button class="story-title" @click="openDetail(item)"><span>{{ item.title }}</span><small>{{ item.has_attachment ? item.original_filename : '旧素材记录' }}</small></button></td><td><p class="summary-cell">{{ summaryOf(item) }}</p></td><td><span class="person-cell">{{ item.uploaded_by || '未填写' }}</span></td><td><span class="person-cell owner">{{ item.project_owner || '未填写' }}</span></td><td><time>{{ formatDateTime(item.created_at) }}</time></td><td><div class="row-actions"><el-button text :icon="View" aria-label="查看剧情" @click="openDetail(item)" /><el-button text :icon="EditPen" aria-label="编辑剧情" @click="openDetail(item, 'edit')" /><el-button v-if="item.has_attachment" text :icon="Download" aria-label="下载附件" @click="download(item)" /><el-button text type="danger" :icon="Delete" aria-label="删除剧情" @click="removeMaterial(item)" /></div></td></tr>
            </tbody></table>
          </div>
        </section>
      </main>

      <MaterialUploadDrawer v-model="uploadOpen" :modules="modules" :initial-genre-id="module.id" initial-material-type="剧情" :library-type="props.libraryType" @complete="handleUploadComplete" />
      <MaterialDetailDrawer v-model="detailOpen" :material="selectedMaterial" :modules="modules" :initial-mode="detailMode" :saving="saving" :library-type="props.libraryType" @save="saveMaterial" @download="download" />
    </template>
  </div>
</template>

<style scoped>
.genre-page{min-height:100%}.inactive-banner{padding:9px 30px;background:rgba(245,158,11,.1);border-bottom:1px solid rgba(245,158,11,.2);color:#fbbf24;font-size:12px}.genre-hero{position:relative;display:flex;align-items:center;justify-content:space-between;gap:28px;padding:30px 36px;background:linear-gradient(120deg,color-mix(in srgb,var(--genre-color) 10%,var(--panel)),var(--bg-soft));border-bottom:1px solid var(--border-soft);overflow:hidden}.genre-hero:after{content:"";position:absolute;right:-90px;top:-210px;width:420px;height:420px;border:1px solid color-mix(in srgb,var(--genre-color) 35%,transparent);border-radius:50%;opacity:.35}.hero-identity{position:relative;z-index:1;display:flex;align-items:center;gap:16px;min-width:0}.module-icon{width:54px;height:54px;display:grid;place-items:center;flex:0 0 auto;border-radius:12px;background:var(--genre-color);color:#fff;font-size:23px}.hero-identity small{color:var(--genre-color);font-size:10px;font-weight:800;letter-spacing:.15em}.hero-identity h1{margin:6px 0 4px;font-family:"Songti SC",serif;font-size:28px}.hero-identity p{max-width:620px;margin:0;color:var(--text-secondary);font-size:13px;line-height:1.7}.hero-count{position:relative;z-index:1;min-width:135px;padding:12px 16px;border:1px solid color-mix(in srgb,var(--genre-color) 24%,var(--border-soft));border-radius:10px;background:color-mix(in srgb,var(--panel) 88%,transparent)}.hero-count small,.hero-count span{display:block;color:var(--text-muted);font-size:11px}.hero-count b{display:block;margin:4px 0;font-size:24px}.module-body{padding:24px 30px 50px}.title-module{border-radius:11px;overflow:hidden}.title-module>header{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:17px 19px;border-bottom:1px solid var(--border-soft)}.module-title{display:flex;align-items:center;gap:12px}.module-title>span{width:40px;height:40px;display:grid;place-items:center;border-radius:9px;background:var(--accent-soft);color:var(--accent)}.module-title small{color:var(--accent);font-size:10px;font-weight:800;letter-spacing:.14em}.module-title h2{margin:3px 0 0;font-size:18px}.module-title p{margin:4px 0 0;color:var(--text-muted);font-size:12px}.section-actions{display:flex;gap:8px}.story-table-wrap{max-width:100%;overflow-x:hidden}.story-table{width:100%;border-collapse:separate;border-spacing:0;table-layout:fixed}.story-table th{padding:12px 12px;background:var(--panel-raised);color:var(--text-muted);font-size:11px;font-weight:700;text-align:left}.story-table th:nth-child(1){width:19%}.story-table th:nth-child(2){width:auto}.story-table th:nth-child(3){width:11%}.story-table th:nth-child(4){width:14%}.story-table th:nth-child(5){width:13%}.story-table th:nth-child(6){width:132px}.story-table td{padding:14px 12px;border-top:1px solid var(--border-soft);vertical-align:middle}.story-table th:last-child,.story-table td:last-child{position:sticky;right:0;z-index:2}.story-table th:last-child{z-index:3;background:var(--panel-raised)}.story-table td:last-child{background:var(--panel)}.story-table tbody tr:hover td{background:var(--panel-hover)}.story-title{display:grid;gap:5px;max-width:100%;padding:0;border:0;background:none;text-align:left;cursor:pointer}.story-title span{overflow:hidden;color:var(--text);font-size:14px;font-weight:750;text-overflow:ellipsis;white-space:nowrap}.story-title:hover span{color:var(--accent)}.story-title small{overflow:hidden;color:var(--text-muted);font-size:11px;text-overflow:ellipsis;white-space:nowrap}.summary-cell{display:-webkit-box;overflow:hidden;margin:0;color:var(--text-secondary);font-size:12px;line-height:1.55;-webkit-box-orient:vertical;-webkit-line-clamp:2}.person-cell{display:inline-flex;max-width:100%;overflow:hidden;padding:4px 8px;border-radius:999px;background:var(--panel-raised);color:var(--text-secondary);font-size:11px;text-overflow:ellipsis;white-space:nowrap}.person-cell.owner{background:var(--accent-soft);color:var(--accent)}time{color:var(--text-muted);font-size:11px}.row-actions{display:flex;align-items:center;gap:2px;white-space:nowrap}.row-actions :deep(.el-button){width:30px;height:30px;margin:0;padding:6px}.table-loading{display:grid;gap:1px}.table-loading i{height:58px;background:linear-gradient(90deg,var(--panel),var(--panel-raised),var(--panel));background-size:200% 100%;animation:loading 1.2s infinite}.content-state{min-height:300px;display:grid;place-content:center;justify-items:center;gap:8px;padding:45px 20px;text-align:center;color:var(--text-muted)}.content-state>.el-icon{font-size:32px;color:var(--accent)}.content-state b{color:var(--text);font-size:15px}.content-state span{font-size:13px}.page-state{min-height:calc(100vh - 64px)}.loading-state{padding:32px}.hero-skeleton,.content-skeleton{border-radius:10px;background:linear-gradient(90deg,var(--panel),var(--panel-raised),var(--panel));background-size:200% 100%;animation:loading 1.2s infinite}.hero-skeleton{height:165px}.content-skeleton{height:420px;margin-top:22px}.message-state{display:grid;place-content:center;justify-items:center;color:var(--text-muted);text-align:center}.message-state strong{color:var(--accent);font:700 52px monospace}.message-state>.el-icon{font-size:34px;color:var(--danger)}.message-state h1{margin:12px 0 5px;color:var(--text);font-size:20px}.message-state p{margin:0 0 16px;font-size:13px}.message-state a{padding:9px 14px;border-radius:8px;background:var(--accent);color:#17110a;text-decoration:none;font-size:12px;font-weight:700}@keyframes loading{to{background-position:-200% 0}}@media(max-width:900px){.genre-hero{align-items:flex-start;flex-direction:column}.hero-count{width:100%}.module-body{padding:18px 10px 35px}.title-module>header{align-items:flex-start;flex-direction:column}.section-actions{width:100%;justify-content:flex-end}.story-table th,.story-table td{padding-left:7px;padding-right:7px}.story-table th:nth-child(1){width:18%}.story-table th:nth-child(3){width:10%}.story-table th:nth-child(4){width:13%}.story-table th:nth-child(5){width:12%}.story-table th:nth-child(6){width:128px}.story-title span{font-size:12px}.summary-cell,.person-cell,time{font-size:10px}}
.genre-filter{margin:14px}
@media(max-width:900px){.genre-filter{margin:10px}}
</style>
