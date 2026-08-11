<script setup lang="ts">
import { reactive, ref, watch } from 'vue'
import { Download, EditPen } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import MaterialPreview from './MaterialPreview.vue'
import type { GenreModule } from '../../types/genreModule'
import type { Material, MaterialUpdatePayload } from '../../types/material'
import { formatDateTime } from '../../utils/format'

const open=defineModel<boolean>({required:true})
const props=defineProps<{ material: Material|null; modules: GenreModule[]; initialMode?: 'view'|'edit'; saving?: boolean }>()
const emit=defineEmits<{ save:[payload:MaterialUpdatePayload];download:[material:Material] }>()
const form=reactive({title:'',genre_module_id:'',material_type:'',tags:'',source:'',description:''})
const mode=ref<'view'|'edit'>('view')
watch([open,()=>props.material,()=>props.initialMode],()=>{mode.value=props.initialMode||'view';if(props.material)Object.assign(form,{title:props.material.title,genre_module_id:props.material.genre_module_id||'',material_type:props.material.material_type,tags:props.material.tags.join('，'),source:props.material.source,description:props.material.description})},{immediate:true})
function edit(){mode.value='edit'}
function save(){const title=form.title.trim();const materialType=form.material_type.trim();const parsedTags=form.tags.split(/[,，]/).map(i=>i.trim()).filter(Boolean);if(!title)return ElMessage.warning('标题不能为空');if(title.length>100)return ElMessage.warning('标题不能超过 100 个字符');if(!form.genre_module_id)return ElMessage.warning('请选择题材');if(!materialType)return ElMessage.warning('素材类型不能为空');if(materialType.length>30)return ElMessage.warning('素材类型不能超过 30 个字符');if(parsedTags.length>30||parsedTags.some(tag=>tag.length>50))return ElMessage.warning('最多 30 个标签，单个标签不超过 50 个字符');if(form.source.trim().length>200)return ElMessage.warning('来源不能超过 200 个字符');if(form.description.trim().length>20000)return ElMessage.warning('说明不能超过 20000 个字符');emit('save',{title,genre_module_id:form.genre_module_id,material_type:materialType,tags:parsedTags,source:form.source.trim(),description:form.description.trim()})}
function size(value:number){return value<1024**2?`${(value/1024).toFixed(1)} KB`:`${(value/1024**2).toFixed(1)} MB`}
</script>

<template>
  <el-drawer v-model="open" :title="mode==='edit'?'编辑素材元数据':'素材详情'" size="720px">
    <div v-if="material" class="detail-body">
      <template v-if="mode==='view'">
        <div class="detail-heading"><span>{{ material.has_attachment ? material.file_extension.toUpperCase() : '无附件' }}</span><div><h2>{{ material.title }}</h2><p>{{ material.has_attachment ? material.original_filename : '升级前保留的素材记录' }}</p></div></div>
        <MaterialPreview :material="material" @download="emit('download',material)" />
        <dl><div><dt>所属题材</dt><dd>{{ material.genre_module?.name || '—' }}</dd></div><div><dt>素材类型</dt><dd>{{ material.material_type }}</dd></div><div><dt>文件大小</dt><dd>{{ material.has_attachment ? size(material.file_size) : '—' }}</dd></div><div><dt>MIME</dt><dd>{{ material.has_attachment ? material.mime_type : '—' }}</dd></div><div><dt>来源</dt><dd>{{ material.source || '—' }}</dd></div><div><dt>上传时间</dt><dd>{{ formatDateTime(material.created_at) }}</dd></div></dl>
        <section class="detail-section"><h3>标签</h3><div class="tags"><span v-for="tag in material.tags" :key="tag">{{ tag }}</span><i v-if="!material.tags.length">暂无标签</i></div></section>
        <section v-if="!material.has_attachment" class="detail-section legacy-note"><h3>附件状态</h3><p>该记录没有关联物理文件。删除时只会删除数据库记录，不会访问或删除磁盘中的其他文件。</p></section>
        <section v-if="!material.has_attachment && material.legacy_summary" class="detail-section"><h3>旧素材摘要</h3><p>{{ material.legacy_summary }}</p></section>
        <section v-if="!material.has_attachment && material.legacy_content" class="detail-section"><h3>旧素材正文</h3><p class="legacy-content">{{ material.legacy_content }}</p></section>
        <section v-if="material.description || (material.has_attachment && !material.description)" class="detail-section"><h3>{{ material.has_attachment ? '素材说明' : '补充说明' }}</h3><p>{{ material.description || '暂无说明' }}</p></section>
      </template>
      <el-form v-else label-position="top"><el-form-item label="标题" required><el-input v-model="form.title" maxlength="100" show-word-limit /></el-form-item><div class="edit-grid"><el-form-item label="所属题材" required><el-select v-model="form.genre_module_id" filterable class="full"><el-option v-for="item in modules" :key="item.id" :label="item.name" :value="item.id" /></el-select></el-form-item><el-form-item label="素材类型" required><el-input v-model="form.material_type" /></el-form-item></div><el-form-item label="标签"><el-input v-model="form.tags" placeholder="多个标签使用逗号分隔" /></el-form-item><el-form-item label="来源"><el-input v-model="form.source" /></el-form-item><el-form-item label="说明"><el-input v-model="form.description" type="textarea" :rows="6" /></el-form-item><div class="locked-file"><b>文件字段不可编辑</b><span>{{ material.has_attachment ? `${material.original_filename} · ${size(material.file_size)} · ${material.mime_type}` : '该旧素材记录没有附件' }}</span></div></el-form>
    </div>
    <template #footer><el-button @click="open=false">关闭</el-button><template v-if="material"><el-button v-if="mode==='view' && material.has_attachment" :icon="Download" @click="emit('download',material)">下载</el-button><el-button v-if="mode==='view'" type="primary" :icon="EditPen" @click="edit">编辑元数据</el-button><el-button v-else type="primary" :loading="saving" @click="save">保存修改</el-button></template></template>
  </el-drawer>
</template>

<style scoped>
.detail-body{padding:20px 24px 35px}.detail-heading{display:flex;align-items:center;gap:12px;margin-bottom:15px}.detail-heading>span{display:grid;place-items:center;width:52px;height:43px;border-radius:8px;background:var(--accent-soft);color:var(--accent);font-size:10px;font-weight:900}.detail-heading h2{margin:0;font-size:17px}.detail-heading p{margin:4px 0 0;color:var(--text-muted);font-size:9px}dl{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;margin:14px 0;background:var(--border-soft);border:1px solid var(--border-soft);border-radius:8px;overflow:hidden}dl div{padding:11px;background:var(--panel-raised)}dt{color:var(--text-muted);font-size:8px}dd{margin:4px 0 0;color:var(--text-secondary);font-size:10px}.detail-section{padding:13px 0;border-top:1px solid var(--border-soft)}.detail-section h3{margin:0 0 8px;font-size:10px}.detail-section p{margin:0;color:var(--text-secondary);font-size:10px;line-height:1.7}.detail-section .legacy-content{white-space:pre-wrap}.legacy-note{margin-top:14px;padding:12px;border:1px solid var(--border-soft);border-radius:8px;background:var(--panel-raised)}.tags{display:flex;gap:5px;flex-wrap:wrap}.tags span{padding:3px 7px;border:1px solid var(--border);border-radius:99px;color:var(--text-secondary);font-size:8px}.tags i{color:var(--text-muted);font-size:9px;font-style:normal}.edit-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}.full{width:100%}.locked-file{display:grid;gap:4px;padding:12px;border:1px solid var(--border-soft);border-radius:8px;background:var(--panel-raised)}.locked-file b{font-size:9px}.locked-file span{color:var(--text-muted);font-size:8px}
</style>
