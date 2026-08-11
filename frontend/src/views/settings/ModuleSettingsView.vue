<script setup lang="ts">
import { computed, onMounted, reactive, ref, type Component } from 'vue'
import { ElMessage, ElMessageBox, type FormInstance, type FormRules } from 'element-plus'
import * as ElementIcons from '@element-plus/icons-vue'
import { ArrowDown, ArrowUp, Collection, CopyDocument, Delete, EditPen, Plus, Refresh, Setting } from '@element-plus/icons-vue'
import { useGenreModulesStore } from '../../stores/genreModules'
import type { GenreModule, GenreModulePayload, GenreModuleStatus } from '../../types/genreModule'
import { HEX_COLOR_PATTERN, isValidGenreSlug } from '../../utils/validation'

const store = useGenreModulesStore()
const iconRegistry = ElementIcons as Record<string, Component>
const modules = computed(() => store.allModules)
const selectedModuleId = ref('')
const moduleDialogOpen = ref(false)
const moduleFormRef = ref<FormInstance>()
const editingModule = ref<GenreModule | null>(null)
const savingModule = ref(false)
const moduleDragIndex = ref<number | null>(null)

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

onMounted(async () => {
  await store.fetchAllModules()
  selectedModuleId.value = modules.value[0]?.id || ''
})

function statusLabel(status: GenreModuleStatus) {
  return status === 'active' ? '启用' : status === 'archived' ? '归档' : '停用'
}

async function retryModules() {
  await store.fetchAllModules()
  if (!selectedModuleId.value && modules.value.length) selectedModuleId.value = modules.value[0]!.id
}

function openModuleDialog(item?: GenreModule) {
  editingModule.value = item || null
  if (item) {
    Object.assign(moduleForm, {
      name: item.name, slug: item.slug, icon: item.icon, description: item.description,
      theme_color: item.theme_color, sort_order: item.sort_order, status: item.status,
      visible: item.visible, profile_json: structuredClone(item.profile_json), create_default_sections: false,
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
    ElMessage.success(editingModule.value ? '题材模块已更新' : '题材模块已创建，已自动使用“标题”板块')
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
  if (selectedModuleId.value === item.id) selectedModuleId.value = modules.value[0]?.id || ''
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
</script>

<template>
  <div class="settings-page">
    <header class="page-heading">
      <div><span>CONFIGURATION CENTER</span><h1>题材配置</h1><p>维护题材名称、显示状态和排序；每个题材统一使用一个“标题”功能板块。</p></div>
      <el-button type="primary" :icon="Plus" @click="openModuleDialog()">新增题材</el-button>
    </header>

    <div v-if="store.loading && !modules.length" class="full-state surface"><el-skeleton :rows="8" animated /></div>
    <div v-else-if="store.error && !modules.length" class="full-state surface"><el-icon><Setting /></el-icon><h2>模块加载失败</h2><p>{{ store.error }}</p><el-button :icon="Refresh" @click="retryModules">重新加载</el-button></div>
    <div v-else-if="!modules.length" class="full-state surface"><el-icon><Collection /></el-icon><h2>暂无题材模块</h2><p>创建第一个题材后，它会自动出现在题材导航中。</p><el-button type="primary" :icon="Plus" @click="openModuleDialog()">新增题材</el-button></div>

    <div v-else class="settings-grid">
      <section class="module-list surface">
        <header><div><h2>题材模块</h2><span>{{ modules.length }} 个数据库配置</span></div><el-icon><Setting /></el-icon></header>
        <div class="module-table-head"><span>题材</span><span>状态</span><span>显示</span><span>板块</span><span>排序</span><span>操作</span></div>
        <div class="module-rows">
          <article v-for="(item,index) in modules" :key="item.id" class="module-row" :class="{ selected: selectedModuleId === item.id }" draggable="true" @dragstart="startModuleDrag(index)" @dragover.prevent @drop="dropModule(index)" @click="selectedModuleId=item.id">
            <div class="module-name"><span class="module-icon" :style="{ color: item.theme_color, background: `${item.theme_color}18` }"><el-icon><component :is="iconRegistry[item.icon] || Collection" /></el-icon></span><div><b>{{ item.name }}</b><small>{{ item.slug }} · {{ new Date(item.updated_at).toLocaleDateString('zh-CN') }}</small></div></div>
            <em :class="item.status">{{ statusLabel(item.status) }}</em>
            <el-switch :model-value="item.visible" @click.stop @change="toggleVisible(item)" />
            <span>1</span><code>{{ item.sort_order }}</code>
            <el-dropdown trigger="click" @click.stop><button class="more-button">•••</button><template #dropdown><el-dropdown-menu><el-dropdown-item :icon="ArrowUp" :disabled="index === 0" @click="moveModule(index, -1)">上移</el-dropdown-item><el-dropdown-item :icon="ArrowDown" :disabled="index === modules.length - 1" @click="moveModule(index, 1)">下移</el-dropdown-item><el-dropdown-item :icon="EditPen" @click="openModuleDialog(item)">编辑模块</el-dropdown-item><el-dropdown-item @click="toggleEnabled(item)">{{ item.status === 'active' ? '停用模块' : '启用模块' }}</el-dropdown-item><el-dropdown-item @click="toggleVisible(item)">{{ item.visible ? '隐藏模块' : '显示模块' }}</el-dropdown-item><el-dropdown-item :icon="CopyDocument" @click="duplicateModule(item)">复制模块</el-dropdown-item><el-dropdown-item :icon="Delete" divided @click="removeModule(item)">软删除</el-dropdown-item></el-dropdown-menu></template></el-dropdown>
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
          <el-form-item v-if="!editingModule" label="自动建立“标题”板块"><el-switch v-model="moduleForm.create_default_sections" /></el-form-item>
        </div>
      </el-form>
      <template #footer><el-button @click="moduleDialogOpen = false">取消</el-button><el-button type="primary" :loading="savingModule" @click="saveModule">保存模块</el-button></template>
    </el-dialog>
  </div>
</template>

<style scoped>
.settings-page{max-width:1540px;margin:0 auto;padding:30px 32px 54px}.page-heading{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin-bottom:22px}.page-heading span{color:var(--accent);font-size:11px;font-weight:800;letter-spacing:.14em}.page-heading h1{margin:6px 0 5px;font-family:"Songti SC",serif;font-size:30px}.page-heading p{margin:0;color:var(--text-muted);font-size:14px;line-height:1.6}.settings-grid{display:grid;grid-template-columns:minmax(560px,.95fr) minmax(500px,1fr);gap:14px;align-items:start}.module-list,.section-panel,.full-state{border-radius:12px;overflow:hidden}.module-list>header,.section-panel>header{min-height:72px;display:flex;align-items:center;justify-content:space-between;padding:15px 18px;border-bottom:1px solid var(--border-soft)}.module-list h2,.section-panel h2{margin:0;font-size:16px}.module-list header span,.section-panel header p{margin:5px 0 0;color:var(--text-muted);font-size:12px}.module-list header>.el-icon{color:var(--accent)}.module-table-head,.module-row{display:grid;grid-template-columns:minmax(210px,1.6fr) 58px 56px 44px 44px 36px;align-items:center;gap:10px;padding:10px 14px}.module-table-head{background:var(--bg-soft);color:var(--text-muted);font-size:11px;font-weight:700}.module-rows{max-height:calc(100vh - 240px);overflow-y:auto}.module-row{min-height:66px;border-top:1px solid var(--border-soft);cursor:grab}.module-row:hover,.module-row.selected{background:var(--panel-raised)}.module-row.selected{box-shadow:inset 3px 0 var(--accent)}.module-name{display:flex;align-items:center;gap:10px;min-width:0}.module-icon{width:36px;height:36px;display:grid;place-items:center;flex:0 0 auto;border-radius:8px}.module-name b,.module-name small{display:block;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}.module-name b{font-size:14px}.module-name small{margin-top:4px;color:var(--text-muted);font-size:11px}.module-row>em{padding:4px 6px;border-radius:5px;background:var(--panel-hover);color:var(--text-muted);font-size:11px;font-style:normal;text-align:center}.module-row>em.active{background:rgba(52,211,153,.1);color:#34d399}.module-row>em.inactive,.module-row>em.disabled{background:rgba(245,158,11,.1);color:#fbbf24}.module-row>span,.module-row>code{color:var(--text-secondary);font-size:12px}.more-button{width:30px;height:30px;border:0;border-radius:6px;background:transparent;color:var(--text-muted);font-size:16px;cursor:pointer}.more-button:hover{background:var(--panel-hover);color:var(--text)}.section-panel>header>div{display:flex;align-items:center;gap:11px}.accent-bar{width:6px;height:38px;border-radius:4px}.fixed-badge{padding:5px 9px;border:1px solid color-mix(in srgb,var(--accent) 34%,var(--border));border-radius:999px;background:var(--accent-soft);color:var(--accent)!important;font-size:11px!important;letter-spacing:0!important}.fixed-section{padding:22px}.fixed-title{display:grid;grid-template-columns:48px 1fr auto;align-items:center;gap:14px;padding:20px;border:1px solid var(--border);border-radius:11px;background:var(--panel-raised)}.fixed-icon{width:48px;height:48px;display:grid;place-items:center;border-radius:10px;background:var(--accent-soft);color:var(--accent);font-size:22px}.fixed-title small{color:var(--text-muted);font-size:11px}.fixed-title h3{margin:4px 0;font-size:20px}.fixed-title p{margin:0;color:var(--text-secondary);font-size:13px}.fixed-title em{padding:5px 9px;border-radius:999px;background:rgba(52,211,153,.1);color:#34d399;font-size:12px;font-style:normal}.field-preview{margin-top:18px}.field-preview>span{display:block;margin-bottom:9px;color:var(--text-muted);font-size:12px}.field-preview>div{display:flex;flex-wrap:wrap;gap:8px}.field-preview b{padding:8px 11px;border:1px solid var(--border);border-radius:7px;background:var(--bg-soft);font-size:12px}.fixed-note{margin-top:20px;padding:16px;border-left:3px solid var(--accent);background:var(--accent-soft)}.fixed-note b{font-size:13px}.fixed-note p{margin:6px 0 0;color:var(--text-secondary);font-size:13px;line-height:1.7}.full-state{min-height:400px;display:grid;place-content:center;justify-items:center;padding:30px;color:var(--text-muted);text-align:center}.full-state>.el-icon{font-size:34px;color:var(--accent)}.full-state h2{margin:12px 0 5px;color:var(--text)}.full-state p{margin:0 0 15px;font-size:13px}.form-grid{display:grid;grid-template-columns:1fr 1fr;gap:0 16px}.wide{grid-column:1/-1}.form-help{display:block;margin-top:6px;color:var(--text-muted);font-size:12px}.color-field{display:grid;grid-template-columns:35px 1fr;gap:8px;width:100%}.w-full{width:100%}@media(max-width:1180px){.settings-grid{grid-template-columns:1fr}.module-rows{max-height:none}}@media(max-width:720px){.settings-page{padding:20px 16px}.page-heading{align-items:flex-start;flex-direction:column}.module-table-head{display:none}.module-row{grid-template-columns:1fr 54px 50px 36px}.module-row>span,.module-row>code{display:none}.form-grid{grid-template-columns:1fr}}
.settings-grid{display:block}.module-list{width:100%}.module-list>header{min-height:84px;padding:18px 24px}.module-list h2{font-size:19px}.module-list header span{font-size:13px}.module-table-head,.module-row{grid-template-columns:minmax(320px,2fr) 90px 90px 80px 80px 52px;gap:18px;padding-left:24px;padding-right:24px}.module-table-head{min-height:42px;font-size:12px}.module-row{min-height:78px}.module-icon{width:44px;height:44px;border-radius:10px;font-size:18px}.module-name{gap:14px}.module-name b{font-size:16px}.module-name small{font-size:12px}.module-row>em,.module-row>span,.module-row>code{font-size:13px}.more-button{width:36px;height:36px}
</style>
