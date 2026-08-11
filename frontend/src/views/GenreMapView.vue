<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Download, Grid, List, Plus, Upload } from '@element-plus/icons-vue'
import GenreBubbleChart from '../components/genre-map/GenreBubbleChart.vue'
import GenreMetricTable from '../components/genre-map/GenreMetricTable.vue'
import GenreMetricFilterBar from '../components/genre-map/GenreMetricFilterBar.vue'
import GenreMetricEditorDrawer from '../components/genre-map/GenreMetricEditorDrawer.vue'
import GenreMetricImportDialog from '../components/genre-map/GenreMetricImportDialog.vue'
import GenreMetricDetailDrawer from '../components/genre-map/GenreMetricDetailDrawer.vue'
import { downloadGenreMetricTemplate, exportGenreMetrics } from '../api/genreMetrics'
import { useGenreMetricsStore } from '../stores/genreMetrics'
import { useGenreModulesStore } from '../stores/genreModules'
import type { GenreMetric, GenreMetricFilters, GenreMetricPayload } from '../types/genreMetric'
import { EDUCATION_SCORE, weightedMean } from '../utils/genreMap'
import { confirmDestructive } from '../utils/confirm'

const route=useRoute();const router=useRouter();const store=useGenreMetricsStore();const genreStore=useGenreModulesStore()
const view=ref<'chart'|'table'>((localStorage.getItem('genre-map-view') as 'chart'|'table')||'chart')
const editorOpen=ref(false);const importOpen=ref(false);const detailOpen=ref(false);const selected=ref<GenreMetric|null>(null);const editing=ref<GenreMetric|null>(null);const saving=ref(false)
const modules=computed(()=>genreStore.allModules.length?genreStore.allModules:genreStore.modules)
const genreCount=computed(()=>new Set(store.items.map(i=>i.genre_module_id)).size)
const averageAge=computed(()=>weightedMean(store.items,i=>i.average_age))
const averageEducation=computed(()=>weightedMean(store.items,i=>EDUCATION_SCORE[i.education_level]))
function string(value:unknown){return typeof value==='string'?value:undefined}
function filtersFromQuery():GenreMetricFilters{const core=string(route.query.is_core);return{genre_module_id:string(route.query.genre_module_id),platform:string(route.query.platform),channel:string(route.query.channel),period:string(route.query.period),age_group:string(route.query.age_group) as GenreMetricFilters['age_group'],education_level:string(route.query.education_level) as GenreMetricFilters['education_level'],trend:string(route.query.trend) as GenreMetricFilters['trend'],is_core:core===undefined?undefined:core==='true',heat_min:Number(string(route.query.heat_min)||0),heat_max:Number(string(route.query.heat_max)||100),page:Number(string(route.query.page)||1),page_size:100}}
function toQuery(filters:GenreMetricFilters){const query:Record<string,string>={};for(const[key,value]of Object.entries(filters)){if(value===undefined||value===''||value===null)continue;if(key==='page_size')continue;if(key==='page'&&value===1)continue;if(key==='heat_min'&&value===0)continue;if(key==='heat_max'&&value===100)continue;query[key]=String(value)}return query}
async function apply(filters:GenreMetricFilters){await router.push({query:toQuery(filters)})}
async function reset(){await router.push({query:{}})}
function setView(next:'chart'|'table'){view.value=next;localStorage.setItem('genre-map-view',next)}
function openCreate(){editing.value=null;editorOpen.value=true}
function openEdit(item:GenreMetric){detailOpen.value=false;editing.value=item;editorOpen.value=true}
function openDetail(item:GenreMetric){selected.value=item;detailOpen.value=true}
async function save(payload:GenreMetricPayload){saving.value=true;try{if(editing.value)await store.update(editing.value.id,payload);else await store.create(payload);editorOpen.value=false;ElMessage.success(editing.value?'定位数据已更新':'定位数据已新增')}finally{saving.value=false}}
async function remove(item:GenreMetric){const name=item.genre_module?.name||item.genre_name||'该题材';await confirmDestructive(`确定删除“${name}”这条 ${item.period} 定位数据？`,'二次确认');await store.remove(item.id);ElMessage.success('定位数据已删除')}
function saveBlob(blob:Blob,name:string){const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),0)}
async function template(format:'xlsx'|'csv'){try{saveBlob(await downloadGenreMetricTemplate(format),`题材定位数据导入模板.${format}`)}catch{ElMessage.error('模板下载失败')}}
async function exportData(format:'xlsx'|'csv'){try{const stamp=new Date().toISOString().slice(0,19).replaceAll('-','').replaceAll(':','').replace('T','');saveBlob(await exportGenreMetrics(store.filters,format),`题材定位数据_${stamp}.${format}`)}catch{ElMessage.error('导出失败，请稍后重试')}}
function viewMaterials(item:GenreMetric){void router.push({path:'/materials',query:{genre_module_id:item.genre_module_id}})}
watch(()=>route.query,async()=>{store.setFilters(filtersFromQuery());await store.fetchMetrics()},{immediate:true,deep:true})
onMounted(()=>genreStore.fetchAllModules())
</script>

<template>
  <div class="page-shell"><header class="page-heading"><div><span class="eyebrow">AUDIENCE POSITIONING</span><h1>年龄—学历题材定位图</h1><p>用真实定位数据观察受众年龄、学历层级与用户占比分布。</p></div><div class="heading-actions"><el-dropdown trigger="click" @command="template"><el-button :icon="Download">下载模板</el-button><template #dropdown><el-dropdown-menu><el-dropdown-item command="xlsx">Excel 模板</el-dropdown-item><el-dropdown-item command="csv">CSV 模板</el-dropdown-item></el-dropdown-menu></template></el-dropdown><el-button :icon="Upload" @click="importOpen=true">导入数据</el-button><el-dropdown trigger="click" @command="exportData"><el-button :icon="Download">导出当前结果</el-button><template #dropdown><el-dropdown-menu><el-dropdown-item command="xlsx">导出 Excel</el-dropdown-item><el-dropdown-item command="csv">导出 CSV</el-dropdown-item></el-dropdown-menu></template></el-dropdown><el-button type="primary" :icon="Plus" @click="openCreate">新增数据</el-button></div></header>
    <section class="summary"><div><small>筛选结果</small><b>{{ store.total }}</b><span>条定位记录</span></div><div><small>覆盖题材</small><b>{{ genreCount }}</b><span>个模块</span></div><div><small>加权平均年龄</small><b>{{ averageAge.toFixed(1) }}</b><span>按用户占比计算</span></div><div><small>加权学历位置</small><b>{{ averageEducation.toFixed(2) }}</b><span>1 低 · 2 中 · 3 高</span></div></section>
    <GenreMetricFilterBar :model-value="store.filters" :modules="modules" @apply="apply" @reset="reset" />
    <section class="map-panel surface"><header><div><h2>定位数据全景</h2><p>点击气泡查看完整定位数据，并可直接进入对应题材素材库。</p></div><div class="view-switch"><button :class="{active:view==='chart'}" @click="setView('chart')"><el-icon><Grid/></el-icon>图表</button><button :class="{active:view==='table'}" @click="setView('table')"><el-icon><List/></el-icon>表格</button></div></header><GenreBubbleChart v-if="view==='chart'" :items="store.items" :loading="store.loading" :error="store.error" @select="openDetail" @retry="store.fetchMetrics"/><GenreMetricTable v-else :items="store.items" :loading="store.loading" @view="openDetail" @edit="openEdit" @delete="remove"/></section>
    <GenreMetricEditorDrawer v-model="editorOpen" :metric="editing" :modules="modules" :saving="saving" @save="save"/><GenreMetricImportDialog v-model="importOpen" @complete="store.fetchMetrics"/><GenreMetricDetailDrawer v-model="detailOpen" :metric="selected" @edit="openEdit" @materials="viewMaterials"/>
  </div>
</template>

<style scoped>
.page-shell{max-width:1600px;margin:0 auto;padding:28px 30px 50px}.page-heading{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:18px}.eyebrow{color:var(--accent);font-size:8px;font-weight:800;letter-spacing:.18em}.page-heading h1{margin:5px 0 4px;font-family:"Songti SC",serif;font-size:27px}.page-heading p{margin:0;color:var(--text-muted);font-size:11px}.heading-actions{display:flex;gap:8px}.summary{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-bottom:12px}.summary>div{padding:14px 16px;border:1px solid var(--border-soft);border-radius:9px;background:var(--panel)}.summary small,.summary span{color:var(--text-muted);font-size:8px}.summary b{display:inline-block;margin:0 8px 0 14px;font-size:21px}.map-panel{margin-top:12px;border-radius:10px;overflow:hidden}.map-panel>header{min-height:62px;display:flex;align-items:center;justify-content:space-between;padding:11px 15px;border-bottom:1px solid var(--border-soft)}.map-panel h2{margin:0;font-size:12px}.map-panel header p{margin:5px 0 0;color:var(--text-muted);font-size:8px}.view-switch{display:flex;padding:3px;border:1px solid var(--border);border-radius:7px;background:var(--bg-soft)}.view-switch button{display:flex;align-items:center;gap:5px;padding:6px 9px;border:0;border-radius:5px;background:transparent;color:var(--text-muted);font-size:9px;cursor:pointer}.view-switch button.active{background:var(--panel-hover);color:var(--accent)}@media(max-width:1250px){.page-heading{align-items:flex-start}.heading-actions{flex-wrap:wrap;justify-content:flex-end}.summary{grid-template-columns:repeat(2,1fr)}}
</style>
