<script setup lang="ts">
import { EditPen, Files } from '@element-plus/icons-vue'
import type { GenreMetric } from '../../types/genreMetric'
import { AGE_LABEL, EDUCATION_LABEL } from '../../utils/genreMap'
import { formatDateTime } from '../../utils/format'
const open=defineModel<boolean>({required:true})
defineProps<{metric:GenreMetric|null}>()
const emit=defineEmits<{edit:[metric:GenreMetric];materials:[metric:GenreMetric]}>()
const trend={rising:'上升',stable:'稳定',falling:'下降'}
function name(item:GenreMetric){return item.genre_module?.name||item.genre_name||'—'}
</script>

<template><el-drawer v-model="open" title="定位数据详情" size="500px"><div v-if="metric" class="detail"><header><i :style="{background:metric.genre_module?.theme_color||metric.theme_color||'#f59e0b'}"></i><div><span>AUDIENCE METRIC</span><h2>{{ name(metric) }}</h2></div><em v-if="metric.is_core">重点题材</em></header><div class="hero-metrics"><div><small>平均年龄</small><b>{{ metric.average_age }}</b><span>岁 · {{ AGE_LABEL[metric.age_group] }}</span></div><div><small>学历层级</small><b>{{ EDUCATION_LABEL[metric.education_level] }}</b><span>图表位置 {{ {low:1,medium:2,high:3}[metric.education_level] }}</span></div><div><small>用户占比</small><b>{{ metric.audience_share }}%</b><span>决定气泡大小</span></div><div><small>热度指数</small><b>{{ metric.heat_index }}</b><span>满分 100</span></div></div><dl><div><dt>数据平台</dt><dd>{{ metric.platform }}</dd></div><div><dt>频道</dt><dd>{{ metric.channel }}</dd></div><div><dt>周期</dt><dd>{{ metric.period }}</dd></div><div><dt>趋势</dt><dd>{{ trend[metric.trend] }}</dd></div><div><dt>样本量</dt><dd>{{ metric.sample_size.toLocaleString() }}</dd></div><div><dt>数据来源</dt><dd>{{ metric.data_source||'—' }}</dd></div><div><dt>更新时间</dt><dd>{{ formatDateTime(metric.updated_at) }}</dd></div></dl><section><h3>备注</h3><p>{{ metric.remark||'暂无备注' }}</p></section></div><template #footer><el-button @click="open=false">关闭</el-button><el-button v-if="metric" :icon="EditPen" @click="emit('edit',metric)">编辑</el-button><el-button v-if="metric" type="primary" :icon="Files" @click="emit('materials',metric)">查看该题材素材</el-button></template></el-drawer></template>

<style scoped>
.detail{padding:22px 24px}.detail header{display:flex;align-items:center;gap:11px}.detail header>i{width:9px;height:42px;border-radius:5px}.detail header span{color:var(--text-muted);font-size:7px;letter-spacing:.15em}.detail header h2{margin:3px 0 0;font-size:18px}.detail header em{margin-left:auto;padding:4px 8px;border:1px solid var(--accent);border-radius:99px;color:var(--accent);font-size:8px;font-style:normal}.hero-metrics{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin:18px 0}.hero-metrics>div{display:grid;padding:13px;border:1px solid var(--border-soft);border-radius:8px;background:var(--panel-raised)}.hero-metrics small{color:var(--text-muted);font-size:8px}.hero-metrics b{margin-top:5px;font-size:18px}.hero-metrics span{margin-top:3px;color:var(--text-muted);font-size:8px}dl{margin:0}dl div{display:grid;grid-template-columns:100px 1fr;padding:10px 0;border-bottom:1px solid var(--border-soft);font-size:9px}dt{color:var(--text-muted)}dd{margin:0;color:var(--text-secondary)}section{margin-top:17px}section h3{font-size:10px}section p{color:var(--text-secondary);font-size:9px;line-height:1.7}
</style>
