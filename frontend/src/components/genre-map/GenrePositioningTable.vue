<script setup lang="ts">
import { View } from '@element-plus/icons-vue'
import type { GenrePositioningTimelinePoint } from '../../types/genrePositioning'

defineProps<{ points: GenrePositioningTimelinePoint[]; uploadPlatform: string; loading?: boolean }>()
const emit = defineEmits<{ view: [point: GenrePositioningTimelinePoint] }>()
</script>

<template>
  <el-table :data="points" v-loading="loading" empty-text="当前平台暂无月度题材数据" class="positioning-table">
    <el-table-column label="题材" min-width="150"><template #default="{ row }"><span class="genre"><i :style="{ background: row.theme_color }"></i>{{ row.genre_name }}</span></template></el-table-column>
    <el-table-column label="上传平台" min-width="130"><template #default>{{ uploadPlatform }}</template></el-table-column>
    <el-table-column prop="period" label="上传月份" width="120" />
    <el-table-column label="平均热度" width="120"><template #default="{ row }"><b class="heat">{{ row.average_heat.toFixed(1) }}</b></template></el-table-column>
    <el-table-column label="素材数量" width="110"><template #default="{ row }">{{ row.material_count }} 份</template></el-table-column>
    <el-table-column label="操作" width="120" fixed="right"><template #default="{ row }"><el-button link type="primary" :icon="View" data-test="view-materials" @click="emit('view', row)">查看素材</el-button></template></el-table-column>
  </el-table>
</template>

<style scoped>
.positioning-table{width:100%}.genre{display:flex;align-items:center;gap:9px;font-weight:700}.genre i{width:9px;height:9px;border-radius:50%}.heat{color:var(--accent);font-size:14px}
</style>
