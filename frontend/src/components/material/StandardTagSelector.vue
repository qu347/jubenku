<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import {
  decodeStandardTags, encodeStandardTags, standardTagGroups,
  type StandardTagGroupKey,
} from '../../utils/materialTaxonomy'

const props = defineProps<{ modelValue: string[]; disabled?: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [value: string[]] }>()
const selections = reactive<Record<StandardTagGroupKey, string[]>>({ plot: [], emotion: [], era: [], role: [] })
const customTags = ref<string[]>([])
const customInput = ref('')
const customError = ref('')
let syncing = false
const tagCount = computed(() => standardTagGroups.reduce((total, group) => total + selections[group.key].length, 0) + customTags.value.length)

watch(() => props.modelValue, (value) => {
  syncing = true
  const decoded = decodeStandardTags(value || [])
  customTags.value = [...decoded.passthrough]
  for (const group of standardTagGroups) selections[group.key] = [...decoded.selections[group.key]]
  syncing = false
}, { immediate: true, deep: true })

function toggle(groupKey: StandardTagGroupKey, value: string, multiple: boolean) {
  if (props.disabled) return
  const selected = selections[groupKey]
  const index = selected.indexOf(value)
  if (index >= 0) selected.splice(index, 1)
  else if (multiple) selected.push(value)
  else selections[groupKey] = [value]
  emitValue()
}

function emitValue() {
  if (!syncing) emit('update:modelValue', encodeStandardTags(selections, customTags.value))
}

function addCustomTags() {
  if (props.disabled) return
  customError.value = ''
  const candidates = customInput.value.split(/[,，]/).map((value) => value.trim()).filter(Boolean)
  if (!candidates.length) return
  for (const tag of candidates) {
    if (tag.length > 50) {
      customError.value = `“${tag.slice(0, 12)}…”超过 50 个字符`
      return
    }
    if (customTags.value.includes(tag)) continue
    if (tagCount.value >= 30) {
      customError.value = '标准标签和自定义标签合计最多 30 个'
      return
    }
    customTags.value.push(tag)
  }
  customInput.value = ''
  emitValue()
}

function removeCustomTag(tag: string) {
  if (props.disabled) return
  customTags.value = customTags.value.filter((item) => item !== tag)
  customError.value = ''
  emitValue()
}

function handleCustomKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' && event.key !== ',' && event.key !== '，') return
  event.preventDefault()
  addCustomTags()
}
</script>

<template>
  <div class="taxonomy">
    <section v-for="group in standardTagGroups" :key="group.key">
      <header><b>{{ group.label }}</b><span>{{ group.multiple ? '多选' : '单选' }}</span></header>
      <div class="chip-list">
        <button
          v-for="option in group.options"
          :key="option"
          type="button"
          :class="{ selected: selections[group.key].includes(option) }"
          :disabled="disabled"
          @click="toggle(group.key, option, group.multiple)"
        >{{ option }}</button>
      </div>
    </section>
    <section class="custom-section">
      <header><b>自定义标签</b><span>补充特殊设定，最多 30 个标签</span></header>
      <div v-if="customTags.length" class="custom-list">
        <button v-for="tag in customTags" :key="tag" type="button" :disabled="disabled" :aria-label="`删除自定义标签 ${tag}`" @click="removeCustomTag(tag)"><span>{{ tag }}</span><i v-if="!disabled">×</i></button>
      </div>
      <div v-if="!disabled" class="custom-input">
        <input v-model="customInput" maxlength="200" placeholder="输入自定义标签，可用逗号分隔" @keydown="handleCustomKeydown" />
        <button type="button" :disabled="!customInput.trim()" @click="addCustomTags">添加</button>
      </div>
      <p v-if="customError" class="custom-error">{{ customError }}</p>
    </section>
  </div>
</template>

<style scoped>
.taxonomy{display:grid;gap:20px}.taxonomy section{display:grid;gap:10px}.taxonomy header{display:flex;align-items:center;justify-content:space-between;gap:12px}.taxonomy header b{color:var(--text);font-size:13px}.taxonomy header span{color:var(--text-muted);font-size:11px}.chip-list{display:flex;flex-wrap:wrap;gap:8px}.chip-list button{min-height:34px;padding:6px 13px;border:1px solid var(--border);border-radius:999px;background:transparent;color:var(--text-secondary);font-size:12px;cursor:pointer;transition:.16s ease}.chip-list button:hover{border-color:var(--accent);color:var(--text)}.chip-list button.selected{border-color:var(--accent);background:var(--accent-soft);color:var(--accent);box-shadow:inset 0 0 0 1px color-mix(in srgb,var(--accent) 25%,transparent)}.chip-list button:disabled{cursor:default;opacity:.9}.custom-section{padding-top:4px;border-top:1px solid var(--border-soft)}.custom-list{display:flex;flex-wrap:wrap;gap:8px}.custom-list button{display:flex;align-items:center;gap:7px;min-height:34px;padding:6px 10px 6px 13px;border:1px solid color-mix(in srgb,var(--accent) 42%,var(--border));border-radius:999px;background:var(--accent-soft);color:var(--text);font-size:12px;cursor:pointer}.custom-list i{color:var(--accent);font-size:16px;font-style:normal;line-height:1}.custom-input{display:grid;grid-template-columns:1fr auto;gap:9px}.custom-input input{width:100%;height:38px;padding:0 12px;border:1px solid var(--border);border-radius:8px;outline:none;background:var(--panel-raised);color:var(--text);font-size:13px}.custom-input input:focus{border-color:var(--accent);box-shadow:0 0 0 2px var(--accent-soft)}.custom-input input::placeholder{color:var(--text-muted)}.custom-input button{min-width:72px;border:1px solid var(--border);border-radius:8px;background:var(--panel-hover);color:var(--text-secondary);font-size:13px;cursor:pointer}.custom-input button:not(:disabled):hover{border-color:var(--accent);color:var(--accent)}.custom-input button:disabled{cursor:not-allowed;opacity:.5}.custom-error{margin:0;color:var(--danger);font-size:12px}@media(max-width:600px){.taxonomy header{align-items:flex-start;flex-direction:column;gap:3px}.custom-input{grid-template-columns:1fr}.custom-input button{height:38px}}
</style>
