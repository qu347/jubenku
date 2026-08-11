<script setup lang="ts">
import { computed, onMounted, reactive, ref, type Component } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import * as ElementIcons from '@element-plus/icons-vue'
import { ArrowDown, ArrowUp, Collection, CopyDocument, Delete, EditPen, Plus, Refresh, Setting } from '@element-plus/icons-vue'
import {
  createModuleSection,
  listModuleSections,
} from '../../api/genreModules'
import {
  deleteModuleSection,
  disableModuleSection,
  enableModuleSection,
  reorderModuleSections,
  updateModuleSection,
} from '../../api/moduleSections'
import { useGenreModulesStore } from '../../stores/genreModules'
import type { GenreModule, GenreModulePayload, GenreModuleStatus } from '../../types/genreModule'
import type { FieldDefinition, FieldType, ModuleSection, ModuleSectionPayload } from '../../types/moduleSection'
import { HEX_COLOR_PATTERN, isValidGenreSlug, SECTION_KEY_PATTERN } from '../../utils/validation'

const store = useGenreModulesStore()
const iconRegistry = ElementIcons as Record<string, Component>
const modules = computed(() => store.allModules)
const selectedModuleId = ref('')
const selectedModule = computed(() => modules.value.find((item) => item.id === selectedModuleId.value) || null)

const moduleDialogOpen = ref(false)
const moduleFormRef = ref<FormInstance>()
const editingModule = ref<GenreModule | null>(null)
const savingModule = ref(false)
const moduleForm = reactive<GenreModulePayload>({
  name: '', slug: '', icon: 'Collection', description: '', theme_color: '#FF7A45',
  sort_order: 0, status: 'active', visible: true, profile_json: {}, create_default_sections: true,
})
const moduleRules: FormRules<GenreModulePayload> = {
  name: [{ required: true, min: 2, max: 50, message: '名称长度为 2—50 个字符', trigger: 'blur' }],
  slug: [
    { required: true, message: '请输入 slug', trigger: 'blur' },
    { validator: (_rule, value: string, callback) => isValidGenreSlug(value) ? callback() : callback(new Error('仅允许小写字母、数字和连字符')), trigger: 'blur' },
  ],
  theme_color: [{ validator: (_rule, value: string, callback) => HEX_COLOR_PATTERN.test(value) ? callback() : callback(new Error('请输入六位十六进制颜色')), trigger: 'blur' }],
  sort_order: [{ type: 'number', min: 0, message: '排序值不能小于 0', trigger: 'change' }],
}

const sections = ref<ModuleSection[]>([])
const sectionsLoading = ref(false)
const sectionsError = ref('')
const sectionDialogOpen = ref(false)
const sectionFormRef = ref<FormInstance>()
const editingSection = ref<ModuleSection | null>(null)
const savingSection = ref(false)
const sectionForm = reactive({
  section_key: '', section_name: '', icon: 'Document', sort_order: 0, enabled: true,
  field_schema_text: '[]', filter_schema_text: '{}', card_schema_text: '{}',
})
const sectionRules: FormRules = {
  section_name: [{ required: true, min: 2, max: 50, message: '板块名称长度为 2—50 个字符', trigger: 'blur' }],
  section_key: [
    { required: true, message: '请输入板块 key', trigger: 'blur' },
    { validator: (_rule, value: string, callback) => SECTION_KEY_PATTERN.test(value) ? callback() : callback(new Error('仅允许小写字母、数字和下划线')), trigger: 'blur' },
  ],
  sort_order: [{ type: 'number', min: 0, message: '排序值不能小于 0', trigger: 'change' }],
}

const allowedFieldTypes = new Set<FieldType>(['text', 'textarea', 'markdown', 'number', 'date', 'select', 'multiselect', 'tags', 'image', 'url', 'relation'])
const moduleDragIndex = ref<number | null>(null)
const sectionDragIndex = ref<number | null>(null)

onMounted(async () => {
  await store.fetchAllModules()
  selectedModuleId.value = modules.value[0]?.id || ''
  if (selectedModuleId.value) await loadSections()
})

function statusLabel(status: GenreModuleStatus) {
  return status === 'active' ? '启用' : status === 'archived' ? '归档' : '停用'
}

async function retryModules() {
  await store.fetchAllModules()
  if (!selectedModuleId.value && modules.value.length) selectedModuleId.value = modules.value[0]!.id
  if (selectedModuleId.value) await loadSections()
}

async function selectModule(id: string) {
  selectedModuleId.value = id
  await loadSections()
}

function openModuleDialog(item?: GenreModule) {
  editingModule.value = item || null
  if (item) {
    Object.assign(moduleForm, {
      name: item.name,
      slug: item.slug,
      icon: item.icon,
      description: item.description,
      theme_color: item.theme_color,
      sort_order: item.sort_order,
      status: item.status,
      visible: item.visible,
      profile_json: structuredClone(item.profile_json),
      create_default_sections: false,
    })
  } else {
    Object.assign(moduleForm, {
      name: '', slug: '', icon: 'Collection', description: '', theme_color: '#FF7A45',
      sort_order: modules.value.length, status: 'active', visible: true, profile_json: {}, create_default_sections: true,
    })
  }
  moduleDialogOpen.value = true
}

async function saveModule() {
  if (!await moduleFormRef.value?.validate().catch(() => false)) return
  savingModule.value = true
  try {
    const saved = editingModule.value
      ? await store.updateModule(editingModule.value.id, { ...moduleForm })
      : await store.createModule({ ...moduleForm })
    moduleDialogOpen.value = false
    selectedModuleId.value = saved.id
    await loadSections()
    ElMessage.success(editingModule.value ? '题材模块已更新' : '题材模块已创建，导航已刷新')
  } finally {
    savingModule.value = false
  }
}

async function toggleEnabled(item: GenreModule) {
  if (item.status === 'active') {
    await store.disableModule(item.id)
    ElMessage.success('模块已停用，数据保持不变')
  } else {
    await store.enableModule(item.id)
    ElMessage.success('模块已启用，导航已刷新')
  }
}

async function toggleVisible(item: GenreModule) {
  await store.updateModule(item.id, { visible: !item.visible })
  ElMessage.success(item.visible ? '模块已从普通导航隐藏' : '模块已显示在普通导航')
}

async function duplicateModule(item: GenreModule) {
  const duplicate = await store.duplicateModule(item.id)
  ElMessage.success(`已复制为“${duplicate.name}”，副本默认停用并隐藏`)
}

async function removeModule(item: GenreModule) {
  await ElMessageBox.confirm(`软删除“${item.name}”？该模块将从普通查询中消失。`, '删除题材模块', { type: 'warning', confirmButtonText: '确认删除' })
  await store.deleteModule(item.id)
  if (selectedModuleId.value === item.id) {
    selectedModuleId.value = modules.value[0]?.id || ''
    sections.value = []
    if (selectedModuleId.value) await loadSections()
  }
  ElMessage.success('题材模块已软删除')
}

function startModuleDrag(index: number) { moduleDragIndex.value = index }
async function dropModule(targetIndex: number) {
  const sourceIndex = moduleDragIndex.value
  moduleDragIndex.value = null
  if (sourceIndex === null || sourceIndex === targetIndex) return
  const reordered = [...modules.value]
  const [moved] = reordered.splice(sourceIndex, 1)
  if (!moved) return
  reordered.splice(targetIndex, 0, moved)
  await store.reorderModules(reordered.map((item, index) => ({ id: item.id, sort_order: index })))
  ElMessage.success('模块顺序已保存')
}

async function moveModule(index: number, direction: -1 | 1) {
  const target = index + direction
  if (target < 0 || target >= modules.value.length) return
  const reordered = [...modules.value]
  ;[reordered[index], reordered[target]] = [reordered[target]!, reordered[index]!]
  await store.reorderModules(reordered.map((item, order) => ({ id: item.id, sort_order: order })))
  ElMessage.success('模块顺序已保存')
}

async function loadSections() {
  if (!selectedModuleId.value) return
  sectionsLoading.value = true
  sectionsError.value = ''
  try {
    sections.value = await listModuleSections(selectedModuleId.value, true)
  } catch (reason) {
    sectionsError.value = reason instanceof Error ? reason.message : '板块加载失败'
    sections.value = []
  } finally {
    sectionsLoading.value = false
  }
}

function openSectionDialog(item?: ModuleSection) {
  editingSection.value = item || null
  if (item) {
    Object.assign(sectionForm, {
      section_key: item.section_key,
      section_name: item.section_name,
      icon: item.icon,
      sort_order: item.sort_order,
      enabled: item.enabled,
      field_schema_text: JSON.stringify(item.field_schema, null, 2),
      filter_schema_text: JSON.stringify(item.filter_schema, null, 2),
      card_schema_text: JSON.stringify(item.card_schema, null, 2),
    })
  } else {
    Object.assign(sectionForm, {
      section_key: '', section_name: '', icon: 'Document', sort_order: sections.value.length,
      enabled: true, field_schema_text: '[]', filter_schema_text: '{}', card_schema_text: '{}',
    })
  }
  sectionDialogOpen.value = true
}

function parseObject(value: string, label: string): Record<string, unknown> {
  const parsed: unknown = JSON.parse(value)
  if (!parsed || Array.isArray(parsed) || typeof parsed !== 'object') throw new Error(`${label} 必须是 JSON 对象`)
  return parsed as Record<string, unknown>
}

function parseFields(value: string): FieldDefinition[] {
  const parsed: unknown = JSON.parse(value)
  if (!Array.isArray(parsed)) throw new Error('field_schema 必须是 JSON 数组')
  return parsed.map((raw, index) => {
    if (!raw || typeof raw !== 'object') throw new Error(`第 ${index + 1} 个字段必须是对象`)
    const field = raw as Partial<FieldDefinition>
    if (!field.key || !/^[a-zA-Z][a-zA-Z0-9_]*$/.test(field.key)) throw new Error(`第 ${index + 1} 个字段 key 格式错误`)
    if (!field.label || typeof field.label !== 'string') throw new Error(`第 ${index + 1} 个字段缺少 label`)
    if (!field.type || !allowedFieldTypes.has(field.type)) throw new Error(`第 ${index + 1} 个字段 type 不受支持`)
    const options = Array.isArray(field.options) ? field.options.map(String) : []
    if (['select', 'multiselect'].includes(field.type) && !options.length) throw new Error(`第 ${index + 1} 个选择字段必须提供 options`)
    return {
      key: field.key,
      label: field.label,
      type: field.type,
      required: Boolean(field.required),
      sort_order: Number(field.sort_order ?? index),
      options,
      placeholder: String(field.placeholder || ''),
    }
  })
}

async function saveSection() {
  if (!selectedModuleId.value || !await sectionFormRef.value?.validate().catch(() => false)) return
  let payload: ModuleSectionPayload
  try {
    payload = {
      section_key: sectionForm.section_key,
      section_name: sectionForm.section_name,
      icon: sectionForm.icon,
      sort_order: sectionForm.sort_order,
      enabled: sectionForm.enabled,
      field_schema: parseFields(sectionForm.field_schema_text),
      filter_schema: parseObject(sectionForm.filter_schema_text, 'filter_schema'),
      card_schema: parseObject(sectionForm.card_schema_text, 'card_schema'),
    }
  } catch (reason) {
    ElMessage.error(reason instanceof Error ? reason.message : 'JSON 格式错误')
    return
  }
  savingSection.value = true
  try {
    if (editingSection.value) await updateModuleSection(editingSection.value.id, payload)
    else await createModuleSection(selectedModuleId.value, payload)
    sectionDialogOpen.value = false
    await Promise.all([loadSections(), store.fetchAllModules(), store.fetchNavigationModules()])
    ElMessage.success(editingSection.value ? '功能板块已更新' : '功能板块已创建')
  } finally {
    savingSection.value = false
  }
}

async function toggleSection(item: ModuleSection) {
  if (item.enabled) await disableModuleSection(item.id)
  else await enableModuleSection(item.id)
  await loadSections()
  ElMessage.success(item.enabled ? '板块已停用' : '板块已启用')
}

async function removeSection(item: ModuleSection) {
  await ElMessageBox.confirm(`软删除“${item.section_name}”？`, '删除功能板块', { type: 'warning', confirmButtonText: '确认删除' })
  await deleteModuleSection(item.id)
  await Promise.all([loadSections(), store.fetchAllModules()])
  ElMessage.success('功能板块已软删除')
}

function startSectionDrag(index: number) { sectionDragIndex.value = index }
async function dropSection(targetIndex: number) {
  const sourceIndex = sectionDragIndex.value
  sectionDragIndex.value = null
  if (sourceIndex === null || sourceIndex === targetIndex) return
  const reordered = [...sections.value]
  const [moved] = reordered.splice(sourceIndex, 1)
  if (!moved) return
  reordered.splice(targetIndex, 0, moved)
  sections.value = await reorderModuleSections(reordered.map((item, index) => ({ id: item.id, sort_order: index })))
  ElMessage.success('板块顺序已保存')
}

async function moveSection(index: number, direction: -1 | 1) {
  const target = index + direction
  if (target < 0 || target >= sections.value.length) return
  const reordered = [...sections.value]
  ;[reordered[index], reordered[target]] = [reordered[target]!, reordered[index]!]
  sections.value = await reorderModuleSections(reordered.map((item, order) => ({ id: item.id, sort_order: order })))
  ElMessage.success('板块顺序已保存')
}
</script>

<template>
  <div class="settings-page">
    <header class="page-heading"><div><span>CONFIGURATION CENTER</span><h1>模块与板块设置</h1><p>所有配置均写入后端数据库；拖拽排序会立即持久化。</p></div><el-button type="primary" :icon="Plus" @click="openModuleDialog()">新增题材</el-button></header>

    <div v-if="store.loading && !modules.length" class="full-state surface"><el-skeleton :rows="8" animated /></div>
    <div v-else-if="store.error && !modules.length" class="full-state surface"><el-icon><Setting /></el-icon><h2>模块加载失败</h2><p>{{ store.error }}</p><el-button :icon="Refresh" @click="retryModules">重新加载</el-button></div>
    <div v-else-if="!modules.length" class="full-state surface"><el-icon><Collection /></el-icon><h2>暂无题材模块</h2><p>创建第一个模块后，它会自动出现在动态导航中。</p><el-button type="primary" :icon="Plus" @click="openModuleDialog()">新增题材</el-button></div>

    <div v-else class="settings-grid">
      <section class="module-list surface">
        <header><div><h2>题材模块</h2><span>{{ modules.length }} 个数据库配置</span></div><el-icon><Setting /></el-icon></header>
        <div class="module-table-head"><span>题材</span><span>状态</span><span>显示</span><span>板块</span><span>排序</span><span>操作</span></div>
        <div class="module-rows">
          <article
            v-for="(item,index) in modules"
            :key="item.id"
            class="module-row"
            :class="{ selected: selectedModuleId === item.id }"
            draggable="true"
            @dragstart="startModuleDrag(index)"
            @dragover.prevent
            @drop="dropModule(index)"
            @click="selectModule(item.id)"
          >
            <div class="module-name"><span class="module-icon" :style="{ color: item.theme_color, background: `${item.theme_color}18` }"><el-icon><component :is="iconRegistry[item.icon] || Collection" /></el-icon></span><div><b>{{ item.name }}</b><small>{{ item.slug }} · {{ new Date(item.updated_at).toLocaleDateString('zh-CN') }}</small></div></div>
            <em :class="item.status">{{ statusLabel(item.status) }}</em>
            <el-switch :model-value="item.visible" @click.stop @change="toggleVisible(item)" />
            <span>{{ item.section_count }}</span><code>{{ item.sort_order }}</code>
            <el-dropdown trigger="click" @click.stop><button class="more-button">•••</button><template #dropdown><el-dropdown-menu><el-dropdown-item :icon="ArrowUp" :disabled="index === 0" @click="moveModule(index, -1)">上移</el-dropdown-item><el-dropdown-item :icon="ArrowDown" :disabled="index === modules.length - 1" @click="moveModule(index, 1)">下移</el-dropdown-item><el-dropdown-item :icon="EditPen" @click="openModuleDialog(item)">编辑模块</el-dropdown-item><el-dropdown-item @click="toggleEnabled(item)">{{ item.status === 'active' ? '停用模块' : '启用模块' }}</el-dropdown-item><el-dropdown-item @click="toggleVisible(item)">{{ item.visible ? '隐藏模块' : '显示模块' }}</el-dropdown-item><el-dropdown-item :icon="CopyDocument" @click="duplicateModule(item)">复制模块与板块</el-dropdown-item><el-dropdown-item @click="selectModule(item.id)">配置板块</el-dropdown-item><el-dropdown-item :icon="Delete" divided @click="removeModule(item)">软删除</el-dropdown-item></el-dropdown-menu></template></el-dropdown>
          </article>
        </div>
      </section>

      <section class="section-panel surface">
        <header v-if="selectedModule"><div><span class="accent-bar" :style="{ background: selectedModule.theme_color }"></span><div><h2>{{ selectedModule.name }} · 功能板块</h2><p>包含禁用板块；拖动行可调整顺序。</p></div></div><el-button :icon="Plus" @click="openSectionDialog()">新增板块</el-button></header>
        <div v-if="sectionsLoading" class="section-state"><el-skeleton :rows="7" animated /></div>
        <div v-else-if="sectionsError" class="section-state"><p>{{ sectionsError }}</p><el-button :icon="Refresh" @click="loadSections">重新加载</el-button></div>
        <div v-else-if="!sections.length" class="section-state"><el-icon><Collection /></el-icon><h3>暂无功能板块</h3><p>新增至少一个启用板块后，题材详情页才会显示标签。</p><el-button :icon="Plus" @click="openSectionDialog()">新增板块</el-button></div>
        <div v-else class="section-list">
          <div class="section-head"><span>板块</span><span>字段结构</span><span>JSON 配置</span><span>状态</span><span>排序</span><span>操作</span></div>
          <article v-for="(item,index) in sections" :key="item.id" draggable="true" @dragstart="startSectionDrag(index)" @dragover.prevent @drop="dropSection(index)">
            <div class="section-name"><el-icon><component :is="iconRegistry[item.icon] || Collection" /></el-icon><div><b>{{ item.section_name }}</b><small>{{ item.section_key }}</small></div></div>
            <div class="field-tags"><span v-for="field in item.field_schema.slice(0,2)" :key="field.key">{{ field.label }} · {{ field.type }}</span><i v-if="item.field_schema.length > 2">+{{ item.field_schema.length - 2 }}</i><em v-if="!item.field_schema.length">空结构</em></div>
            <details><summary>查看</summary><pre>filter {{ JSON.stringify(item.filter_schema, null, 2) }}
card {{ JSON.stringify(item.card_schema, null, 2) }}</pre></details>
            <el-switch :model-value="item.enabled" @change="toggleSection(item)" />
            <code>{{ item.sort_order }}</code>
            <div class="section-actions"><el-button text :icon="ArrowUp" :disabled="index === 0" aria-label="上移板块" @click="moveSection(index, -1)" /><el-button text :icon="ArrowDown" :disabled="index === sections.length - 1" aria-label="下移板块" @click="moveSection(index, 1)" /><el-button text :icon="EditPen" @click="openSectionDialog(item)">编辑</el-button><el-button text :icon="Delete" aria-label="删除板块" @click="removeSection(item)" /></div>
          </article>
        </div>
      </section>
    </div>

    <el-dialog v-model="moduleDialogOpen" :title="editingModule ? '编辑题材模块' : '新增题材模块'" width="680px" destroy-on-close>
      <el-form ref="moduleFormRef" :model="moduleForm" :rules="moduleRules" label-position="top">
        <div class="form-grid">
          <el-form-item label="模块名称" prop="name"><el-input v-model="moduleForm.name" maxlength="50" show-word-limit /></el-form-item>
          <el-form-item label="独立路由 slug" prop="slug"><el-input v-model="moduleForm.slug" placeholder="rule-horror"><template #prepend>/genres/</template></el-input><small class="form-help">仅小写英文字母、数字和连字符；保存后必须全局唯一。</small></el-form-item>
          <el-form-item label="图标名称" prop="icon"><el-input v-model="moduleForm.icon" placeholder="Collection" /></el-form-item>
          <el-form-item label="主题颜色" prop="theme_color"><div class="color-field"><el-color-picker v-model="moduleForm.theme_color" /><el-input v-model="moduleForm.theme_color" /></div></el-form-item>
          <el-form-item label="排序值" prop="sort_order"><el-input-number v-model="moduleForm.sort_order" :min="0" class="w-full" /></el-form-item>
          <el-form-item label="状态" prop="status"><el-select v-model="moduleForm.status" class="w-full"><el-option label="启用" value="active" /><el-option label="停用" value="inactive" /><el-option label="归档" value="archived" /></el-select></el-form-item>
          <el-form-item label="导航显示" prop="visible"><el-switch v-model="moduleForm.visible" active-text="显示" inactive-text="隐藏" /></el-form-item>
          <el-form-item label="模块简介" prop="description" class="wide"><el-input v-model="moduleForm.description" type="textarea" :rows="3" maxlength="5000" /></el-form-item>
          <el-form-item v-if="!editingModule" label="创建默认九个板块"><el-switch v-model="moduleForm.create_default_sections" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="moduleDialogOpen = false">取消</el-button><el-button type="primary" :loading="savingModule" @click="saveModule">保存模块</el-button></template>
    </el-dialog>

    <el-dialog v-model="sectionDialogOpen" :title="editingSection ? '编辑功能板块' : '新增功能板块'" width="860px" destroy-on-close>
      <el-form ref="sectionFormRef" :model="sectionForm" :rules="sectionRules" label-position="top">
        <div class="form-grid four-columns">
          <el-form-item label="板块名称" prop="section_name"><el-input v-model="sectionForm.section_name" /></el-form-item>
          <el-form-item label="板块 key" prop="section_key"><el-input v-model="sectionForm.section_key" placeholder="horror_rules" /></el-form-item>
          <el-form-item label="图标"><el-input v-model="sectionForm.icon" /></el-form-item>
          <el-form-item label="排序值" prop="sort_order"><el-input-number v-model="sectionForm.sort_order" :min="0" class="w-full" /></el-form-item>
          <el-form-item label="启用"><el-switch v-model="sectionForm.enabled" /></el-form-item>
        </div>
        <div class="json-grid">
          <el-form-item label="field_schema（JSON 数组）"><el-input v-model="sectionForm.field_schema_text" type="textarea" :rows="12" spellcheck="false" /></el-form-item>
          <div><el-form-item label="filter_schema（JSON 对象）"><el-input v-model="sectionForm.filter_schema_text" type="textarea" :rows="5" spellcheck="false" /></el-form-item><el-form-item label="card_schema（JSON 对象）"><el-input v-model="sectionForm.card_schema_text" type="textarea" :rows="5" spellcheck="false" /></el-form-item></div>
        </div>
      </el-form>
      <template #footer><el-button @click="sectionDialogOpen = false">取消</el-button><el-button type="primary" :loading="savingSection" @click="saveSection">保存板块</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.settings-page{max-width:1540px;margin:0 auto;padding:28px 30px 50px}.page-heading{display:flex;align-items:flex-end;justify-content:space-between;margin-bottom:20px}.page-heading span{color:var(--accent);font-size:8px;font-weight:800;letter-spacing:.16em}.page-heading h1{margin:5px 0 4px;font-family:"Songti SC",serif;font-size:27px}.page-heading p{margin:0;color:var(--text-muted);font-size:11px}.settings-grid{display:grid;grid-template-columns:minmax(540px,.95fr) minmax(580px,1.2fr);gap:12px;align-items:start}.module-list,.section-panel,.full-state{border-radius:10px;overflow:hidden}.module-list>header,.section-panel>header{min-height:64px;display:flex;align-items:center;justify-content:space-between;padding:13px 15px;border-bottom:1px solid var(--border-soft)}.module-list h2,.section-panel h2{margin:0;font-size:13px}.module-list header span,.section-panel header p{margin:4px 0 0;color:var(--text-muted);font-size:9px}.module-list header>.el-icon{color:var(--accent)}.module-table-head,.module-row{display:grid;grid-template-columns:minmax(190px,1.6fr) 52px 50px 40px 42px 35px;align-items:center;gap:9px;padding:9px 12px}.module-table-head{background:var(--bg-soft);color:var(--text-muted);font-size:8px;font-weight:700}.module-rows{max-height:calc(100vh - 225px);overflow-y:auto}.module-row{min-height:58px;border-top:1px solid var(--border-soft);cursor:grab}.module-row:hover,.module-row.selected{background:var(--panel-raised)}.module-row.selected{box-shadow:inset 2px 0 var(--accent)}.module-name{display:flex;align-items:center;gap:9px;min-width:0}.module-icon{width:32px;height:32px;display:grid;place-items:center;flex:0 0 auto;border-radius:7px}.module-name b,.module-name small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.module-name b{font-size:10px}.module-name small{margin-top:3px;color:var(--text-muted);font-size:8px}.module-row>em{padding:3px 5px;border-radius:4px;background:var(--panel-hover);color:var(--text-muted);font-size:8px;font-style:normal;text-align:center}.module-row>em.active{background:rgba(52,211,153,.1);color:#34d399}.module-row>em.inactive,.module-row>em.disabled{background:rgba(245,158,11,.1);color:#fbbf24}.module-row>span,.module-row>code{color:var(--text-secondary);font-size:9px}.more-button{width:28px;height:28px;border:0;border-radius:5px;background:transparent;color:var(--text-muted);cursor:pointer}.more-button:hover{background:var(--panel-hover);color:var(--text)}.section-panel>header>div{display:flex;align-items:center;gap:10px}.accent-bar{width:6px;height:34px;border-radius:4px}.section-list{max-height:calc(100vh - 210px);overflow-y:auto}.section-head,.section-list>article{display:grid;grid-template-columns:minmax(130px,1.2fr) minmax(140px,1.3fr) 80px 56px 42px 95px;align-items:center;gap:10px;padding:10px 13px}.section-head{background:var(--bg-soft);color:var(--text-muted);font-size:8px;font-weight:700}.section-list>article{min-height:62px;border-top:1px solid var(--border-soft);cursor:grab}.section-list>article:hover{background:var(--panel-raised)}.section-name{display:flex;align-items:center;gap:8px;min-width:0}.section-name>.el-icon{color:var(--accent)}.section-name b,.section-name small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.section-name b{font-size:10px}.section-name small{margin-top:3px;color:var(--text-muted);font-size:8px}.field-tags{display:flex;flex-wrap:wrap;gap:3px}.field-tags span,.field-tags i{padding:3px 5px;border-radius:4px;background:rgba(59,130,246,.08);color:#81aef1;font-size:7px;font-style:normal}.field-tags em{color:var(--text-muted);font-size:8px;font-style:normal}.section-list details{position:relative;color:var(--text-muted);font-size:8px}.section-list summary{cursor:pointer;color:var(--accent)}.section-list pre{position:absolute;z-index:5;right:0;width:280px;max-height:220px;overflow:auto;padding:10px;border:1px solid var(--border);border-radius:7px;background:var(--bg-soft);color:var(--text-secondary);font-size:8px;white-space:pre-wrap}.section-actions{display:flex;justify-content:flex-end}.section-state,.full-state{min-height:400px;display:grid;place-content:center;justify-items:center;padding:30px;color:var(--text-muted);text-align:center}.section-state>.el-icon,.full-state>.el-icon{font-size:30px;color:var(--accent)}.section-state h3,.full-state h2{margin:12px 0 5px;color:var(--text)}.section-state p,.full-state p{margin:0 0 15px;font-size:10px}.section-state .el-skeleton,.full-state .el-skeleton{width:min(720px,70vw)}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 14px}.four-columns{grid-template-columns:1fr 1fr 1fr 1fr}.wide{grid-column:1/-1}.form-help{display:block;margin-top:5px;color:var(--text-muted);font-size:8px}.color-field{display:grid;grid-template-columns:35px 1fr;gap:8px;width:100%}.w-full{width:100%}.json-grid{display:grid;grid-template-columns:1.15fr 1fr;gap:14px}.json-grid :deep(textarea){font-family:Consolas,monospace;font-size:10px;line-height:1.55}@media(max-width:1250px){.settings-grid{grid-template-columns:1fr}.module-rows,.section-list{max-height:none}.four-columns{grid-template-columns:1fr 1fr}}
@media(max-width:1400px){.settings-grid{grid-template-columns:1fr}.module-rows,.section-list{max-height:none}.four-columns{grid-template-columns:1fr 1fr}}
</style>
