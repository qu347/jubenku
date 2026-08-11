<script setup lang="ts">
import { computed, ref, watch, type Component } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as ElementIcons from '@element-plus/icons-vue'
import { Collection, Refresh } from '@element-plus/icons-vue'
import { getGenreModuleBySlug } from '../api/genreModules'
import { ApiError } from '../api/http'
import type { GenreModuleDetail } from '../types/genreModule'

const route = useRoute()
const router = useRouter()
const iconRegistry = ElementIcons as Record<string, Component>
const module = ref<GenreModuleDetail | null>(null)
const activeSectionId = ref('')
const loading = ref(false)
const error = ref('')
const notFound = ref(false)

const activeSection = computed(() => module.value?.sections.find((item) => item.id === activeSectionId.value) || null)
const isInactive = computed(() => module.value?.status !== 'active')

async function loadModule() {
  const slug = String(route.params.slug || '')
  loading.value = true
  error.value = ''
  notFound.value = false
  module.value = null
  try {
    const detail = await getGenreModuleBySlug(slug)
    module.value = detail
    const queryKey = typeof route.query.section === 'string' ? route.query.section : ''
    activeSectionId.value = detail.sections.find((item) => item.section_key === queryKey)?.id || detail.sections[0]?.id || ''
  } catch (reason) {
    if (reason instanceof ApiError && reason.status === 404) notFound.value = true
    else error.value = reason instanceof Error ? reason.message : '题材模块加载失败'
  } finally {
    loading.value = false
  }
}

function selectSection(sectionId: string) {
  activeSectionId.value = sectionId
  const section = module.value?.sections.find((item) => item.id === sectionId)
  if (section && route.query.section !== section.section_key) {
    void router.replace({ query: { ...route.query, section: section.section_key } })
  }
}

function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

watch(() => route.params.slug, () => void loadModule(), { immediate: true })
</script>

<template>
  <div class="genre-page">
    <div v-if="loading" class="page-state loading-state">
      <div class="hero-skeleton"></div><div class="tab-skeleton"></div><div class="content-skeleton"></div>
    </div>

    <section v-else-if="notFound" class="page-state message-state">
      <strong>404</strong><h1>题材不存在</h1><p>该题材可能已被软删除，或当前 slug 不正确。</p><RouterLink to="/settings/modules">返回模块设置</RouterLink>
    </section>

    <section v-else-if="error" class="page-state message-state error-state">
      <el-icon><Collection /></el-icon><h1>题材加载失败</h1><p>{{ error }}</p><el-button :icon="Refresh" @click="loadModule">重新加载</el-button>
    </section>

    <template v-else-if="module">
      <div v-if="isInactive" class="inactive-banner">该题材已停用，仅通过直接地址访问；普通左侧导航不会显示。</div>
      <section class="genre-hero" :style="{ '--genre-color': module.theme_color }">
        <div class="hero-identity">
          <span class="module-icon"><el-icon><component :is="iconRegistry[module.icon] || Collection" /></el-icon></span>
          <div><div class="hero-kicker">GENRE MODULE · /genres/{{ module.slug }}</div><h1>{{ module.name }}</h1><p>{{ module.description || '暂无题材简介' }}</p></div>
        </div>
        <dl>
          <div><dt>状态</dt><dd :class="module.status">{{ module.status === 'active' ? '启用' : module.status === 'archived' ? '归档' : '停用' }}</dd></div>
          <div><dt>导航显示</dt><dd>{{ module.visible ? '显示' : '隐藏' }}</dd></div>
          <div><dt>启用板块</dt><dd>{{ module.sections.length }} 个</dd></div>
          <div><dt>最近更新</dt><dd>{{ formatTime(module.updated_at) }}</dd></div>
        </dl>
      </section>

      <section class="module-body">
        <nav v-if="module.sections.length" class="section-tabs" aria-label="功能板块">
          <button v-for="section in module.sections" :key="section.id" :class="{ active: activeSectionId === section.id }" @click="selectSection(section.id)">
            <el-icon><component :is="iconRegistry[section.icon] || Collection" /></el-icon><span>{{ section.section_name }}</span>
          </button>
        </nav>

        <div v-if="activeSection" class="section-content surface">
          <header><span class="section-icon"><el-icon><component :is="iconRegistry[activeSection.icon] || Collection" /></el-icon></span><div><small>SECTION · {{ activeSection.section_key }}</small><h2>{{ activeSection.section_name }}</h2></div></header>
          <div class="sprint-placeholder">
            <el-icon><Collection /></el-icon>
            <h3>板块配置已就绪</h3>
            <p>当前板块包含 {{ activeSection.field_schema.length }} 个字段定义。题材配置与素材数据均由服务端持久化，素材请在素材库中统一维护。</p>
          </div>
        </div>

        <div v-else class="section-content surface empty-sections">
          <el-icon><Collection /></el-icon><h2>暂无启用板块</h2><p>请在模块设置中启用或新增功能板块。</p><RouterLink to="/settings/modules">进入模块设置</RouterLink>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.genre-page{min-height:100%}.inactive-banner{padding:9px 30px;background:rgba(245,158,11,.1);border-bottom:1px solid rgba(245,158,11,.2);color:#fbbf24;font-size:10px}.genre-hero{position:relative;display:flex;align-items:center;justify-content:space-between;gap:30px;padding:34px 36px;background:linear-gradient(120deg,color-mix(in srgb,var(--genre-color) 10%,var(--panel)),var(--bg-soft));border-bottom:1px solid var(--border-soft);overflow:hidden}.genre-hero:after{content:"";position:absolute;right:-100px;top:-190px;width:430px;height:430px;border:1px solid color-mix(in srgb,var(--genre-color) 35%,transparent);border-radius:50%;opacity:.35}.hero-identity{position:relative;z-index:1;display:flex;align-items:center;gap:16px;min-width:0}.module-icon{width:56px;height:56px;display:grid;place-items:center;flex:0 0 auto;border-radius:12px;background:var(--genre-color);color:#fff;font-size:24px}.hero-kicker{color:var(--genre-color);font-size:8px;font-weight:800;letter-spacing:.14em}.hero-identity h1{margin:6px 0 4px;font-family:"Songti SC",serif;font-size:29px}.hero-identity p{max-width:560px;margin:0;color:var(--text-secondary);font-size:11px;line-height:1.7}.genre-hero dl{position:relative;z-index:1;display:grid;grid-template-columns:repeat(2,minmax(120px,1fr));gap:8px;margin:0}.genre-hero dl>div{padding:10px 12px;border:1px solid color-mix(in srgb,var(--genre-color) 18%,var(--border-soft));border-radius:8px;background:color-mix(in srgb,var(--panel) 88%,transparent)}.genre-hero dt{color:var(--text-muted);font-size:8px}.genre-hero dd{margin:5px 0 0;color:var(--text);font-size:11px;font-weight:700}.genre-hero dd.active{color:#34d399}.genre-hero dd.inactive,.genre-hero dd.disabled{color:#fbbf24}.module-body{padding:0 36px 50px}.section-tabs{display:flex;gap:2px;overflow-x:auto;border-bottom:1px solid var(--border-soft)}.section-tabs button{position:relative;display:flex;align-items:center;gap:6px;flex:0 0 auto;padding:15px 13px;border:0;background:transparent;color:var(--text-muted);font-size:10px;cursor:pointer}.section-tabs button.active{color:var(--text)}.section-tabs button.active:after{content:"";position:absolute;left:10px;right:10px;bottom:-1px;height:2px;background:var(--genre-color)}.section-content{margin-top:22px;min-height:390px;border-radius:10px}.section-content>header{display:flex;align-items:center;gap:12px;padding:18px;border-bottom:1px solid var(--border-soft)}.section-icon{width:38px;height:38px;display:grid;place-items:center;border-radius:8px;background:color-mix(in srgb,var(--genre-color) 13%,var(--panel));color:var(--genre-color);font-size:17px}.section-content small{color:var(--text-muted);font-size:8px;letter-spacing:.1em}.section-content h2{margin:4px 0 0;font-size:15px}.sprint-placeholder,.empty-sections{display:grid;place-content:center;justify-items:center;padding:80px 20px;text-align:center;color:var(--text-muted)}.sprint-placeholder>.el-icon,.empty-sections>.el-icon{font-size:34px;color:var(--genre-color)}.sprint-placeholder h3,.empty-sections h2{margin:14px 0 6px;color:var(--text);font-size:15px}.sprint-placeholder p,.empty-sections p{max-width:520px;margin:0;font-size:10px;line-height:1.8}.empty-sections a{margin-top:15px;color:var(--accent);font-size:10px;text-decoration:none}.page-state{min-height:calc(100vh - 64px)}.loading-state{padding:32px}.hero-skeleton,.tab-skeleton,.content-skeleton{border-radius:10px;background:linear-gradient(90deg,var(--panel),var(--panel-raised),var(--panel));background-size:200% 100%;animation:loading 1.2s infinite}.hero-skeleton{height:190px}.tab-skeleton{height:44px;margin-top:12px}.content-skeleton{height:360px;margin-top:18px}.message-state{display:grid;place-content:center;justify-items:center;color:var(--text-muted);text-align:center}.message-state strong{color:var(--accent);font:700 52px monospace}.message-state>.el-icon{font-size:34px;color:var(--danger)}.message-state h1{margin:12px 0 5px;color:var(--text);font-size:20px}.message-state p{margin:0 0 16px;font-size:10px}.message-state a{padding:9px 14px;border-radius:8px;background:var(--accent);color:#17110a;text-decoration:none;font-size:10px;font-weight:700}@keyframes loading{to{background-position:-200% 0}}@media(max-width:1150px){.genre-hero{align-items:flex-start;flex-direction:column}.genre-hero dl{width:100%;grid-template-columns:repeat(4,1fr)}}
</style>
