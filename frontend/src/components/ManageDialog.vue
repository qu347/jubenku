<script setup lang="ts">
import { ref, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Delete, Plus } from '@element-plus/icons-vue'
import { projectApi, tagApi } from '../api'
import type { Project, Tag } from '../types'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: boolean]; changed: [] }>()
const active = ref<'projects' | 'tags'>('projects')
const projects = ref<Project[]>([])
const tags = ref<Tag[]>([])
const projectName = ref('')
const projectDescription = ref('')
const tagName = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const [projectResponse, tagResponse] = await Promise.all([projectApi.list(), tagApi.list()])
    projects.value = projectResponse.data.data
    tags.value = tagResponse.data.data
  } finally { loading.value = false }
}
watch(() => props.modelValue, (open) => { if (open) void load() })

async function addProject() {
  if (!projectName.value.trim()) return ElMessage.warning('请输入项目名称')
  await projectApi.create({ name: projectName.value.trim(), description: projectDescription.value.trim() })
  projectName.value = ''; projectDescription.value = ''; ElMessage.success('项目已创建'); await load(); emit('changed')
}
async function addTag() {
  if (!tagName.value.trim()) return ElMessage.warning('请输入标签名称')
  await tagApi.create(tagName.value.trim()); tagName.value = ''; ElMessage.success('标签已创建'); await load(); emit('changed')
}
async function removeProject(project: Project) {
  await ElMessageBox.confirm(`删除项目“${project.name}”？项目中的素材会保留并变为未归项目。`, '删除项目', { type: 'warning' })
  await projectApi.remove(project.id); ElMessage.success('项目已删除'); await load(); emit('changed')
}
async function removeTag(tag: Tag) {
  await ElMessageBox.confirm(`删除标签“${tag.name}”？素材本身不会被删除。`, '删除标签', { type: 'warning' })
  await tagApi.remove(tag.id); ElMessage.success('标签已删除'); await load(); emit('changed')
}
</script>

<template>
  <el-dialog :model-value="modelValue" title="项目与标签管理" width="min(720px, 94vw)" @update:model-value="emit('update:modelValue', $event)">
    <div class="manage-tabs"><button :class="{ active: active === 'projects' }" @click="active = 'projects'">项目 {{ projects.length }}</button><button :class="{ active: active === 'tags' }" @click="active = 'tags'">标签 {{ tags.length }}</button></div>
    <div v-loading="loading" class="manage-body">
      <template v-if="active === 'projects'">
        <div class="add-project"><el-input v-model="projectName" maxlength="100" placeholder="新项目名称" /><el-input v-model="projectDescription" placeholder="一句话描述（可选）" @keyup.enter="addProject" /><el-button type="primary" :icon="Plus" @click="addProject">创建</el-button></div>
        <div class="manage-list"><div v-for="project in projects" :key="project.id" class="manage-row"><div><b>{{ project.name }}</b><small>{{ project.description || '暂无描述' }} · {{ project.material_count || 0 }} 条素材</small></div><el-button text :icon="Delete" @click="removeProject(project)">删除</el-button></div></div>
      </template>
      <template v-else>
        <div class="add-tag"><el-input v-model="tagName" maxlength="50" placeholder="新标签名称" @keyup.enter="addTag" /><el-button type="primary" :icon="Plus" @click="addTag">添加</el-button></div>
        <div class="tag-cloud"><span v-for="tag in tags" :key="tag.id"># {{ tag.name }} <small>{{ tag.material_count || 0 }}</small><button aria-label="删除标签" @click="removeTag(tag)">×</button></span></div>
      </template>
    </div>
  </el-dialog>
</template>

<style scoped>
.manage-tabs { display: flex; gap: 3px; padding: 3px; border-radius: 8px; background: var(--bg-soft); }.manage-tabs button { flex: 1; height: 34px; border: 0; border-radius: 6px; background: transparent; color: var(--text-muted); cursor: pointer; }.manage-tabs button.active { background: var(--panel-raised); color: var(--text); box-shadow: 0 1px 5px rgba(0,0,0,.15); }.manage-body { min-height: 330px; padding-top: 18px; }.add-project { display: grid; grid-template-columns: 1fr 1.5fr auto; gap: 8px; }.add-tag { display: flex; gap: 8px; }.add-tag .el-input { max-width: 360px; }.manage-list { margin-top: 16px; border: 1px solid var(--border-soft); border-radius: 8px; }.manage-row { display: flex; align-items: center; justify-content: space-between; padding: 12px 14px; border-bottom: 1px solid var(--border-soft); }.manage-row:last-child { border-bottom: 0; }.manage-row b { display: block; color: var(--text); font-size: 12px; }.manage-row small { display: block; margin-top: 4px; color: var(--text-muted); font-size: 9px; }.tag-cloud { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 18px; }.tag-cloud > span { display: inline-flex; align-items: center; gap: 6px; padding: 7px 9px; border: 1px solid var(--border-soft); border-radius: 6px; background: var(--panel-raised); color: #b7a0ee; font-size: 10px; }.tag-cloud small { color: var(--text-muted); }.tag-cloud button { border: 0; background: transparent; color: var(--text-muted); cursor: pointer; }.tag-cloud button:hover { color: var(--danger); }
@media (max-width: 650px) { .add-project { grid-template-columns: 1fr; } }
</style>
