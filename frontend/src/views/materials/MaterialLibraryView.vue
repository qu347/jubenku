<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Grid, List, Plus, Refresh } from '@element-plus/icons-vue'
import MaterialUploadDrawer from '../../components/material/MaterialUploadDrawer.vue'
import MaterialFilterBar from '../../components/material/MaterialFilterBar.vue'
import MaterialTable from '../../components/material/MaterialTable.vue'
import MaterialCardGrid from '../../components/material/MaterialCardGrid.vue'
import MaterialDetailDrawer from '../../components/material/MaterialDetailDrawer.vue'
import { downloadMaterial, getMaterial } from '../../api/materials'
import { useMaterialsStore } from '../../stores/materials'
import { useGenreModulesStore } from '../../stores/genreModules'
import type { Material, MaterialFilters, MaterialSort } from '../../types/material'
import { confirmDestructive } from '../../utils/confirm'

const props = withDefaults(defineProps<{ libraryType?: 'material' | 'script' }>(), { libraryType: 'material' })
const route=useRoute();const router=useRouter();const store=useMaterialsStore();const genreStore=useGenreModulesStore()
const uploadOpen=ref(false);const detailOpen=ref(false);const selected=ref<Material|null>(null);const detailMode=ref<'view'|'edit'>('view');const saving=ref(false)
const contentNoun=computed(()=>props.libraryType==='script'?'剧本':'素材')
const libraryTitle=computed(()=>props.libraryType==='script'?'剧本库':'素材库')
const viewStorageKey=computed(()=>`${props.libraryType}-library-view`)
const view=ref<'grid'|'table'>((localStorage.getItem(viewStorageKey.value) as 'grid'|'table')||'table')
const modules=computed(()=>genreStore.allModules.length?genreStore.allModules:genreStore.modules)
const activeChips=computed(()=>Object.entries(store.filters).filter(([key,value])=>!['page','page_size','sort','library_type'].includes(key)&&value!==undefined&&value!==''))
const sortOptions:[string,MaterialSort][]=[['最新上传','created_desc'],['最早上传','created_asc'],['最近更新','updated_desc'],['标题 A—Z','title_asc'],['文件从大到小','file_size_desc']]
function queryString(value: unknown){return typeof value==='string'?value:undefined}
function filtersFromQuery():MaterialFilters{return{library_type:props.libraryType,keyword:queryString(route.query.keyword),genre_module_id:queryString(route.query.genre_module_id),material_type:queryString(route.query.material_type),file_extension:queryString(route.query.file_extension),tags:queryString(route.query.tags),source:queryString(route.query.source),upload_platform:props.libraryType==='material'?queryString(route.query.upload_platform):undefined,uploaded_by:props.libraryType==='material'?queryString(route.query.uploaded_by):undefined,uploaded_from:queryString(route.query.uploaded_from),uploaded_to:queryString(route.query.uploaded_to),sort:(queryString(route.query.sort) as MaterialSort)||'created_desc',page:Number(queryString(route.query.page)||1),page_size:Number(queryString(route.query.page_size)||20)}}
function toQuery(filters:MaterialFilters){const query:Record<string,string>={};for(const [key,value] of Object.entries(filters)){if(value!==undefined&&value!==''&&value!==null){if(key==='library_type')continue;if(key==='page'&&value===1)continue;if(key==='page_size'&&value===20)continue;if(key==='sort'&&value==='created_desc')continue;query[key]=String(value)}}return query}
async function apply(filters:MaterialFilters){await router.push({query:toQuery(filters)})}
async function reset(){await router.push({query:{}})}
async function changePage(page:number){await apply({...store.filters,page})}
async function changeSort(value:MaterialSort){await apply({...store.filters,sort:value,page:1})}
function switchView(next:'grid'|'table'){view.value=next;localStorage.setItem(viewStorageKey.value,next)}
async function openDetail(item:Material,mode:'view'|'edit'='view'){selected.value=item;detailMode.value=mode;detailOpen.value=true;try{selected.value=await getMaterial(item.id)}catch{ElMessage.warning('完整正文暂时加载失败，仍可查看列表信息或下载原文件')}}
async function save(payload:Parameters<typeof store.update>[1]){if(!selected.value)return;saving.value=true;try{selected.value=await store.update(selected.value.id,payload);detailMode.value='view';ElMessage.success(`${contentNoun.value}信息已更新`)}finally{saving.value=false}}
async function remove(item:Material){const scope=item.has_attachment?'数据库记录与物理文件':'数据库记录（没有附件）';await confirmDestructive(`将永久删除“${item.title}”的${scope}，是否继续？`,`删除${contentNoun.value}`);await store.remove(item.id);if(selected.value?.id===item.id)detailOpen.value=false;ElMessage.success(item.has_attachment?`${contentNoun.value}与物理文件已删除`:`${contentNoun.value}记录已删除`)}
async function download(item:Material){if(!item.has_attachment){ElMessage.info(`该${contentNoun.value}没有可下载的附件`);return}try{const blob=await downloadMaterial(item.id);const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=item.original_filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),0)}catch{ElMessage.error('下载失败，请稍后重试')}}
function chipLabel(key:string,value:unknown){const labels:Record<string,string>={keyword:'关键词',genre_module_id:'题材',material_type:'素材类型',file_extension:'文件类型',tags:'标签',source:'来源',upload_platform:'上传平台',uploaded_by:'上传人',uploaded_from:'起始',uploaded_to:'截止'};const module=key==='genre_module_id'?modules.value.find(i=>i.id===value)?.name:value;return `${labels[key]||key}：${module}`}
async function removeChip(key:string){const next={...store.filters,[key]:undefined,page:1};await apply(next)}
watch([()=>route.path,()=>route.query],async()=>{store.setFilters(filtersFromQuery());await store.fetchMaterials()},{immediate:true,deep:true})
onMounted(()=>genreStore.fetchAllModules())
</script>

<template>
  <div class="page-shell">
    <header class="page-heading"><div><span class="eyebrow">{{ libraryType === 'script' ? 'SCRIPT EDITORIAL LIBRARY' : 'ENTERPRISE ASSET LIBRARY' }}</span><h1>{{ libraryTitle }} <em>{{ store.total.toLocaleString() }}</em></h1><p>{{ libraryType === 'script' ? '保存剧本编辑参考素材后完成的剧本，集中查阅与管理成稿。' : '上传、筛选与维护供剧本编辑查阅的创作参考素材。' }}</p></div><div class="heading-actions"><el-button :icon="Refresh" :loading="store.loading" @click="store.fetchMaterials">刷新</el-button><el-button type="primary" :icon="Plus" @click="uploadOpen=true">{{ libraryType === 'script' ? '上传剧本' : '上传素材' }}</el-button></div></header>
    <MaterialFilterBar :model-value="store.filters" :modules="modules" :library-type="libraryType" @apply="apply" @reset="reset" />
    <div v-if="activeChips.length" class="filter-chips"><span>已选条件</span><button v-for="([key,value]) in activeChips" :key="key" @click="removeChip(key)">{{ chipLabel(key,value) }} ×</button></div>
    <section class="list-panel surface">
      <header><div><b>{{ contentNoun }}文件</b><span>{{ store.total }} 条记录</span></div><div class="list-tools"><el-select :model-value="store.filters.sort" style="width:130px" @change="changeSort"><el-option v-for="([label,value]) in sortOptions" :key="value" :label="label" :value="value" /></el-select><div class="view-switch"><button :class="{active:view==='table'}" title="表格视图" @click="switchView('table')"><el-icon><List/></el-icon></button><button :class="{active:view==='grid'}" title="卡片视图" @click="switchView('grid')"><el-icon><Grid/></el-icon></button></div></div></header>
      <div v-if="store.error" class="state-box error"><b>{{ contentNoun }}列表加载失败</b><span>{{ store.error }}</span><el-button :icon="Refresh" @click="store.fetchMaterials">重新加载</el-button></div>
      <div v-else-if="!store.loading&&!store.items.length" class="state-box"><div class="empty-mark">空</div><b>{{ activeChips.length?`没有符合条件的${contentNoun}`:`${libraryTitle}还是空的` }}</b><span>{{ activeChips.length?'尝试清空部分筛选条件。':(libraryType === 'script' ? '上传剧本编辑完成的第一个剧本文件。' : '上传第一个文件，建立团队共享素材资产。') }}</span><el-button v-if="activeChips.length" @click="reset">清空筛选</el-button><el-button v-else type="primary" @click="uploadOpen=true">{{ libraryType === 'script' ? '上传剧本' : '上传素材' }}</el-button></div>
      <template v-else><MaterialTable v-if="view==='table'" :items="store.items" :loading="store.loading" :content-noun="contentNoun" :library-type="libraryType" @view="openDetail" @edit="item=>openDetail(item,'edit')" @download="download" @delete="remove"/><MaterialCardGrid v-else :items="store.items" :loading="store.loading" :content-noun="contentNoun" :library-type="libraryType" @view="openDetail" @edit="item=>openDetail(item,'edit')" @download="download" @delete="remove"/></template>
      <footer v-if="store.total"><span>第 {{ store.filters.page }} / {{ Math.max(store.pages,1) }} 页</span><el-pagination background layout="prev,pager,next" :current-page="store.filters.page" :page-size="store.filters.page_size" :total="store.total" @current-change="changePage" /></footer>
    </section>
    <MaterialUploadDrawer v-model="uploadOpen" :modules="modules" :library-type="libraryType" />
    <MaterialDetailDrawer v-model="detailOpen" :material="selected" :modules="modules" :initial-mode="detailMode" :saving="saving" :library-type="libraryType" @save="save" @download="download" />
  </div>
</template>

<style scoped>
.page-shell{max-width:1600px;margin:0 auto;padding:30px 32px 52px}.page-heading{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:20px}.eyebrow{color:var(--accent);font-size:11px;font-weight:800;letter-spacing:.16em}.page-heading h1{margin:6px 0 5px;font-family:"Songti SC",serif;font-size:30px}.page-heading h1 em{margin-left:8px;color:var(--text-muted);font:500 14px Inter,sans-serif}.page-heading p{margin:0;color:var(--text-muted);font-size:14px}.heading-actions{display:flex;gap:8px}.filter-chips{display:flex;align-items:center;gap:7px;min-height:42px;padding:9px 2px;color:var(--text-muted);font-size:12px}.filter-chips button{padding:5px 9px;border:1px solid color-mix(in srgb,var(--accent) 32%,var(--border));border-radius:99px;background:var(--accent-soft);color:var(--text-secondary);font-size:11px;cursor:pointer}.list-panel{margin-top:12px;border-radius:10px;overflow:hidden}.list-panel>header{min-height:62px;display:flex;align-items:center;justify-content:space-between;padding:12px 16px;border-bottom:1px solid var(--border-soft)}.list-panel>header b{font-size:15px}.list-panel>header span{margin-left:9px;color:var(--text-muted);font-size:12px}.list-tools{display:flex;gap:8px}.view-switch{display:flex;padding:3px;border:1px solid var(--border);border-radius:7px;background:var(--bg-soft)}.view-switch button{width:31px;border:0;border-radius:5px;background:transparent;color:var(--text-muted);cursor:pointer}.view-switch button.active{background:var(--panel-hover);color:var(--accent)}.list-panel :deep(.card-grid){padding:14px}.list-panel>footer{min-height:60px;display:flex;align-items:center;justify-content:space-between;padding:10px 16px;border-top:1px solid var(--border-soft)}.list-panel>footer>span{color:var(--text-muted);font-size:12px}.state-box{min-height:340px;display:grid;justify-items:center;align-content:center;gap:10px;padding:30px}.state-box b{font-size:16px}.state-box span{color:var(--text-muted);font-size:13px}.state-box.error b{color:var(--danger)}.empty-mark{width:52px;height:52px;display:grid;place-items:center;border:1px dashed var(--border);border-radius:50%;color:var(--text-muted);font-size:13px}@media(max-width:800px){.page-shell{padding:20px 16px}.page-heading{align-items:flex-start;gap:12px}.heading-actions{flex-shrink:0}}
</style>
