<script setup lang="ts">
import { reactive, watch } from 'vue'
import { Refresh, Search } from '@element-plus/icons-vue'
import type { GenreMetricFilters } from '../../types/genreMetric'
import type { GenreModule } from '../../types/genreModule'
const props=defineProps<{modelValue:GenreMetricFilters;modules:GenreModule[]}>()
const emit=defineEmits<{apply:[filters:GenreMetricFilters];reset:[]}>()
const draft=reactive<GenreMetricFilters>({})
watch(()=>props.modelValue,value=>Object.assign(draft,value),{immediate:true,deep:true})
function apply(){emit('apply',{...draft,page:1})}
</script>

<template>
  <section class="metric-filter surface">
    <div class="filter-grid"><el-select v-model="draft.genre_module_id" clearable filterable placeholder="全部题材"><el-option v-for="item in modules" :key="item.id" :label="item.name" :value="item.id" /></el-select><el-input v-model="draft.platform" clearable placeholder="数据平台" @keyup.enter="apply"/><el-input v-model="draft.channel" clearable placeholder="频道" @keyup.enter="apply"/><el-input v-model="draft.period" clearable placeholder="数据周期" @keyup.enter="apply"/><el-select v-model="draft.age_group" clearable placeholder="年龄层级"><el-option label="少年（12—22）" value="youth"/><el-option label="中年（23—50）" value="middle"/><el-option label="老年（51+）" value="senior"/></el-select><el-select v-model="draft.education_level" clearable placeholder="学历层级"><el-option label="低学历" value="low"/><el-option label="中学历" value="medium"/><el-option label="高学历" value="high"/></el-select><el-select v-model="draft.trend" clearable placeholder="趋势"><el-option label="上升" value="rising"/><el-option label="稳定" value="stable"/><el-option label="下降" value="falling"/></el-select><el-select v-model="draft.is_core" clearable placeholder="是否重点"><el-option label="重点题材" :value="true"/><el-option label="普通题材" :value="false"/></el-select></div>
    <div class="filter-foot"><span>热度范围</span><el-slider v-model="draft.heat_min" :min="0" :max="Number(draft.heat_max??100)" :show-tooltip="true"/><b>{{ draft.heat_min??0 }}</b><i>—</i><el-slider v-model="draft.heat_max" :min="Number(draft.heat_min??0)" :max="100"/><b>{{ draft.heat_max??100 }}</b><el-button :icon="Refresh" @click="emit('reset')">清空</el-button><el-button type="primary" :icon="Search" @click="apply">应用筛选</el-button></div>
  </section>
</template>

<style scoped>
.metric-filter{padding:14px;border-radius:10px}.filter-grid{display:grid;grid-template-columns:repeat(8,minmax(100px,1fr));gap:8px}.filter-foot{display:grid;grid-template-columns:70px minmax(100px,1fr) 28px 12px minmax(100px,1fr) 28px auto auto;align-items:center;gap:8px;margin-top:9px;color:var(--text-muted);font-size:9px}.filter-foot b{color:var(--text-secondary);font-weight:600}.filter-foot i{font-style:normal;text-align:center}@media(max-width:1250px){.filter-grid{grid-template-columns:repeat(4,1fr)}}
</style>
