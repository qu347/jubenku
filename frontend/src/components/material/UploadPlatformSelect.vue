<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useUploadPlatformsStore } from '../../stores/uploadPlatforms'

const model = defineModel<string>({ required: true })
const props = withDefaults(defineProps<{
  options?: readonly string[]
  selectTestId?: string
}>(), {
  selectTestId: 'upload-platform',
})

const store = useUploadPlatformsStore()
const adding = ref(false)
const customName = ref('')
const saving = ref(false)

onMounted(() => {
  void store.fetchPlatforms().catch(() => undefined)
})

function platformKey(value: string) {
  return value.trim().normalize('NFKC').toLocaleLowerCase()
}

const visibleOptions = computed(() => {
  const unique = new Map<string, string>()
  for (const option of props.options ?? store.platforms) {
    const display = option.trim().normalize('NFKC')
    if (display && !unique.has(platformKey(display))) unique.set(platformKey(display), display)
  }
  const selected = model.value.trim().normalize('NFKC')
  if (selected && !unique.has(platformKey(selected))) unique.set(platformKey(selected), selected)
  return [...unique.values()]
})

function openCustomInput() {
  customName.value = ''
  adding.value = true
}

function cancelCustomInput() {
  customName.value = ''
  adding.value = false
}

async function confirmCustom() {
  const value = customName.value.trim().normalize('NFKC')
  if (!value) return ElMessage.warning('请输入自定义平台名称')
  if (value.length > 60) return ElMessage.warning('平台名称不能超过 60 个字符')
  const existing = visibleOptions.value.find((option) => platformKey(option) === platformKey(value))
  if (existing) {
    model.value = existing
    cancelCustomInput()
    return
  }
  saving.value = true
  try {
    model.value = await store.createPlatform(value)
    cancelCustomInput()
  } catch {
    return
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <div class="platform-select">
    <el-select
      v-model="model"
      :data-test="selectTestId"
      filterable
      default-first-option
      clearable
      class="full"
      placeholder="选择上传平台"
    >
      <el-option v-for="item in visibleOptions" :key="item" :label="item" :value="item" />
    </el-select>
    <button v-if="!adding" data-test="add-custom-platform" class="custom-trigger" type="button" @click="openCustomInput">
      ＋ 添加自定义平台
    </button>
    <div v-else class="custom-row">
      <el-input
        v-model="customName"
        data-test="custom-platform-input"
        maxlength="60"
        placeholder="输入平台名称，例如：星河短剧"
        @keyup.enter="confirmCustom"
      />
      <button data-test="confirm-custom-platform" class="confirm" type="button" :disabled="saving" @click="confirmCustom">{{ saving ? '保存中' : '添加' }}</button>
      <button class="cancel" type="button" :disabled="saving" @click="cancelCustomInput">取消</button>
    </div>
    <small>常用平台可直接选择，列表中没有时可添加自定义平台。</small>
  </div>
</template>

<style scoped>
.platform-select{display:grid;gap:7px;width:100%}.full{width:100%}.custom-trigger{justify-self:start;padding:0;border:0;background:transparent;color:var(--accent);font-size:12px;font-weight:700;cursor:pointer}.custom-trigger:hover{text-decoration:underline}.custom-row{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:7px}.custom-row button{padding:0 12px;border:1px solid var(--border);border-radius:6px;background:var(--panel-raised);color:var(--text-secondary);font-size:12px;cursor:pointer}.custom-row .confirm{border-color:var(--accent);background:var(--accent);color:#fff}.platform-select small{color:var(--text-muted);font-size:11px;line-height:1.45}@media(max-width:520px){.custom-row{grid-template-columns:1fr auto}.custom-row :deep(.el-input){grid-column:1/-1}}
</style>
