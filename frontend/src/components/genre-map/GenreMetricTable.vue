<script setup lang="ts">
import { Delete, EditPen, View } from '@element-plus/icons-vue'
import type { GenreMetric } from '../../types/genreMetric'
import { AGE_LABEL, EDUCATION_LABEL } from '../../utils/genreMap'
import { formatDateTime } from '../../utils/format'

defineProps<{ items: GenreMetric[]; loading?: boolean }>()
const emit = defineEmits<{ view: [item: GenreMetric]; edit: [item: GenreMetric]; delete: [item: GenreMetric] }>()
const trendLabel = { rising: '↑ 上升', stable: '— 稳定', falling: '↓ 下降' }
function name(item: GenreMetric) { return item.genre_module?.name || item.genre_name || '—' }
function ageLabel(value: unknown) { return typeof value === 'string' && value in AGE_LABEL ? AGE_LABEL[value as keyof typeof AGE_LABEL] : '—' }
function educationLabel(value: unknown) { return typeof value === 'string' && value in EDUCATION_LABEL ? EDUCATION_LABEL[value as keyof typeof EDUCATION_LABEL] : '—' }
</script>

<template>
  <el-table :data="items" v-loading="loading" height="650" class="metric-table">
    <el-table-column label="题材" min-width="130"><template #default="scope"><span class="genre"><i :style="{ background: scope.row.genre_module?.theme_color || scope.row.theme_color || '#f59e0b' }"></i>{{ name(scope.row) }}</span></template></el-table-column>
    <el-table-column prop="platform" label="平台" min-width="105" />
    <el-table-column prop="channel" label="频道" min-width="90" />
    <el-table-column prop="period" label="周期" min-width="90" />
    <el-table-column prop="average_age" label="平均年龄" width="90" />
    <el-table-column label="年龄层级" width="85"><template #default="scope">{{ ageLabel(scope.row.age_group) }}</template></el-table-column>
    <el-table-column label="学历层级" width="85"><template #default="scope">{{ educationLabel(scope.row.education_level) }}</template></el-table-column>
    <el-table-column label="用户占比" width="90"><template #default="scope">{{ scope.row.audience_share }}%</template></el-table-column>
    <el-table-column prop="heat_index" label="热度" width="70" />
    <el-table-column label="趋势" width="80"><template #default="scope">{{ trendLabel[scope.row.trend as keyof typeof trendLabel] }}</template></el-table-column>
    <el-table-column label="重点" width="65"><template #default="scope"><span :class="['core', scope.row.is_core && 'yes']">{{ scope.row.is_core ? '是' : '否' }}</span></template></el-table-column>
    <el-table-column prop="sample_size" label="样本量" width="90" />
    <el-table-column prop="data_source" label="数据来源" min-width="120" show-overflow-tooltip />
    <el-table-column label="更新时间" width="150"><template #default="scope">{{ formatDateTime(scope.row.updated_at) }}</template></el-table-column>
    <el-table-column label="操作" width="145" fixed="right"><template #default="scope"><el-button text :icon="View" @click="emit('view', scope.row)" /><el-button text :icon="EditPen" @click="emit('edit', scope.row)" /><el-button text type="danger" :icon="Delete" @click="emit('delete', scope.row)" /></template></el-table-column>
  </el-table>
</template>

<style scoped>
.metric-table{--el-table-bg-color:var(--panel);--el-table-tr-bg-color:var(--panel);--el-table-row-hover-bg-color:var(--panel-hover);--el-table-header-bg-color:var(--panel-raised);--el-table-border-color:var(--border-soft);--el-table-text-color:var(--text-secondary);--el-table-header-text-color:var(--text-muted)}.genre{display:flex;align-items:center;gap:7px;color:var(--text);font-weight:600}.genre i{width:7px;height:7px;border-radius:50%}.core{padding:2px 6px;border-radius:99px;background:var(--panel-raised);color:var(--text-muted);font-size:8px}.core.yes{background:var(--accent-soft);color:var(--accent)}
</style>
