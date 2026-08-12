<script setup lang="ts">
import { computed, onMounted, ref, type Component } from 'vue'
import { useRoute } from 'vue-router'
import * as ElementIcons from '@element-plus/icons-vue'
import { ArrowDown, Collection, DataAnalysis, Document, Files, Menu, Moon, Refresh, Setting, Sunny } from '@element-plus/icons-vue'
import { useGenreModulesStore } from '../../stores/genreModules'

const route = useRoute()
const store = useGenreModulesStore()
const collapsed = ref(false)
const materialMenuOpen = ref(false)
const scriptMenuOpen = ref(false)
const theme = ref(localStorage.getItem('script-library-theme') || 'dark')
const isDark = computed(() => theme.value === 'dark')
const iconRegistry = ElementIcons as Record<string, Component>
const currentMaterialModule = computed(() => store.materialModules.find((item) => materialModuleActive(item.slug)))
const currentScriptModule = computed(() => store.scriptModules.find((item) => scriptModuleActive(item.slug)))

onMounted(() => void store.fetchNavigationModules())
function toggleTheme() { theme.value = isDark.value ? 'light' : 'dark'; document.documentElement.dataset.theme = theme.value; localStorage.setItem('script-library-theme', theme.value) }
function materialModuleActive(slug: string) { return route.name === 'genre-materials' && route.params.slug === slug }
function scriptModuleActive(slug: string) { return route.name === 'genre-scripts' && route.params.slug === slug }
</script>

<template>
  <div class="module-app" :class="{ collapsed }">
    <header class="module-header">
      <div class="brand"><div class="brand-mark">题</div><div><b>题材引擎</b><small>MODULAR STORY LAB</small></div></div>
      <button class="collapse-button" aria-label="折叠导航" @click="collapsed = !collapsed"><el-icon><Menu /></el-icon></button>
      <div class="header-context"><span>企业内容资产平台</span><i></i><b>V1.0 · 企业内网版</b></div>
      <div class="header-actions"><button aria-label="切换主题" @click="toggleTheme"><el-icon><Moon v-if="isDark" /><Sunny v-else /></el-icon></button><div class="avatar">创</div></div>
    </header>

    <aside class="module-sidebar">
      <nav>
        <div class="nav-group primary-nav">
          <span class="group-label">工作台</span>
          <RouterLink to="/materials" :class="{ active: route.path === '/materials' }"><el-icon><Files /></el-icon><span>素材库</span></RouterLink>
          <RouterLink to="/scripts" :class="{ active: route.path === '/scripts' }"><el-icon><Document /></el-icon><span>剧本库</span></RouterLink>
          <RouterLink to="/genre-map" :class="{ active: route.path === '/genre-map' }"><el-icon><DataAnalysis /></el-icon><span>平台热度趋势</span></RouterLink>
          <RouterLink to="/settings/modules" :class="{ active: route.path === '/settings/modules' }"><el-icon><Setting /></el-icon><span>题材配置</span></RouterLink>
        </div>

        <div class="nav-group module-group">
          <div v-if="store.loading" class="nav-skeleton" aria-label="题材导航加载中"><i v-for="item in 3" :key="item"></i></div>
          <div v-else-if="store.error" class="nav-state error-state"><span>{{ store.error }}</span><button @click="store.fetchNavigationModules()"><el-icon><Refresh /></el-icon>重新加载</button></div>
          <template v-else>
            <section class="genre-picker-section">
              <span class="group-label">素材题材库 <em>{{ store.materialModules.length }}</em></span>
              <el-popover v-if="store.materialModules.length" v-model:visible="materialMenuOpen" placement="right-start" :width="230" trigger="click" popper-class="genre-picker-popover">
                <template #reference><button class="module-picker" :aria-expanded="materialMenuOpen" aria-label="选择素材题材"><el-icon><component :is="iconRegistry[currentMaterialModule?.icon || 'Collection'] || Collection" /></el-icon><span>{{ currentMaterialModule?.name || '全部素材题材' }}</span><el-icon class="picker-arrow"><ArrowDown /></el-icon></button></template>
                <div class="genre-picker-menu"><header><b>素材题材库</b><span>{{ store.materialModules.length }} 个</span></header><RouterLink v-for="item in store.materialModules" :key="item.id" :to="`/genres/${item.slug}`" :class="{ active: materialModuleActive(item.slug) }" @click="materialMenuOpen = false"><i :style="{ background: item.theme_color }"></i><span>{{ item.name }}</span></RouterLink></div>
              </el-popover>
              <div v-else class="picker-empty">暂无素材题材</div>
            </section>
            <section class="genre-picker-section">
              <span class="group-label">剧本题材库 <em>{{ store.scriptModules.length }}</em></span>
              <el-popover v-if="store.scriptModules.length" v-model:visible="scriptMenuOpen" placement="right-start" :width="230" trigger="click" popper-class="genre-picker-popover">
                <template #reference><button class="module-picker" :aria-expanded="scriptMenuOpen" aria-label="选择剧本题材"><el-icon><component :is="iconRegistry[currentScriptModule?.icon || 'Document'] || Document" /></el-icon><span>{{ currentScriptModule?.name || '全部剧本题材' }}</span><el-icon class="picker-arrow"><ArrowDown /></el-icon></button></template>
                <div class="genre-picker-menu"><header><b>剧本题材库</b><span>{{ store.scriptModules.length }} 个</span></header><RouterLink v-for="item in store.scriptModules" :key="item.id" :to="`/script-genres/${item.slug}`" :class="{ active: scriptModuleActive(item.slug) }" @click="scriptMenuOpen = false"><i :style="{ background: item.theme_color }"></i><span>{{ item.name }}</span></RouterLink></div>
              </el-popover>
              <div v-else class="picker-empty">暂无剧本题材</div>
            </section>
          </template>
        </div>
      </nav>
      <div class="sidebar-foot"><el-icon><Collection /></el-icon><div><b>内部内容资产</b><span>数据与文件由服务端持久化</span></div></div>
    </aside>

    <main class="module-main"><RouterView /></main>
  </div>
</template>

<style scoped>
.module-app{min-height:100vh;padding-left:238px;padding-top:64px;transition:padding-left .2s}.module-header{position:fixed;z-index:50;top:0;left:0;right:0;height:64px;display:flex;align-items:center;padding:0 22px;background:color-mix(in srgb,var(--bg-soft) 94%,transparent);border-bottom:1px solid var(--border-soft);backdrop-filter:blur(16px)}.brand{width:216px;display:flex;align-items:center;gap:10px}.brand-mark{width:34px;height:34px;display:grid;place-items:center;border-radius:9px;background:var(--accent);color:#17110a;font-family:"Songti SC",serif;font-weight:900}.brand b{display:block;font-size:15px}.brand small{display:block;margin-top:2px;color:var(--text-muted);font-size:7px;letter-spacing:.18em}.collapse-button,.header-actions button{width:34px;height:34px;display:grid;place-items:center;border:1px solid var(--border);border-radius:8px;background:var(--panel);color:var(--text-secondary);cursor:pointer}.header-context{flex:1;display:flex;align-items:center;gap:10px;margin-left:20px;color:var(--text-muted);font-size:11px}.header-context i{width:1px;height:12px;background:var(--border)}.header-context b{color:var(--text-secondary);font-weight:600}.header-actions{display:flex;align-items:center;gap:10px}.avatar{width:32px;height:32px;display:grid;place-items:center;border-radius:50%;background:linear-gradient(135deg,#475569,#1e293b);color:#fff;font-size:11px}.module-sidebar{position:fixed;z-index:40;top:64px;bottom:0;left:0;width:238px;display:flex;flex-direction:column;padding:16px 12px;background:var(--bg-soft);border-right:1px solid var(--border-soft);transition:width .2s}.module-sidebar nav{flex:1;overflow-y:auto}.nav-group{padding-bottom:14px}.nav-group+.nav-group{padding-top:14px;border-top:1px solid var(--border-soft)}.group-label{display:flex;align-items:center;justify-content:space-between;margin:0 9px 8px;color:var(--text-muted);font-size:9px;font-weight:800;letter-spacing:.1em}.group-label em{color:var(--accent);font-style:normal}.nav-group a{min-height:37px;display:grid;grid-template-columns:22px 1fr auto;align-items:center;gap:8px;padding:7px 9px;border-radius:7px;color:var(--text-secondary);font-size:12px;text-decoration:none}.nav-group a:hover{background:var(--panel);color:var(--text)}.nav-group a.active{background:var(--accent-soft);color:var(--text);box-shadow:inset 2px 0 var(--accent)}.module-picker{width:100%;min-height:38px;display:grid;grid-template-columns:22px 1fr 16px;align-items:center;gap:8px;padding:8px 9px;border:1px solid var(--border-soft);border-radius:8px;background:var(--panel);color:var(--text-secondary);font-size:11px;text-align:left;cursor:pointer}.module-picker:hover,.module-picker[aria-expanded="true"]{border-color:var(--accent);color:var(--text)}.picker-arrow{transition:transform .16s}.module-picker[aria-expanded="true"] .picker-arrow{transform:rotate(180deg)}.nav-skeleton{display:grid;gap:7px;padding:4px}.nav-skeleton i{height:34px;border-radius:7px;background:linear-gradient(90deg,var(--panel),var(--panel-raised),var(--panel));background-size:200% 100%;animation:loading 1.2s infinite}.nav-state{display:grid;justify-items:center;gap:7px;padding:20px 10px;border:1px dashed var(--border);border-radius:8px;color:var(--text-muted);font-size:9px;text-align:center}.nav-state a,.nav-state button{border:0;background:transparent;color:var(--accent);font-size:9px;text-decoration:none;cursor:pointer}.nav-state button{display:flex;align-items:center;gap:4px}.error-state{color:var(--danger)}.sidebar-foot{display:flex;align-items:center;gap:9px;padding:12px;border:1px solid var(--border-soft);border-radius:8px;color:var(--accent)}.sidebar-foot b,.sidebar-foot span{display:block}.sidebar-foot b{color:var(--text-secondary);font-size:10px}.sidebar-foot span{margin-top:3px;color:var(--text-muted);font-size:8px}.module-main{min-height:calc(100vh - 64px);background:var(--bg)}.collapsed{padding-left:72px}.collapsed .module-sidebar{width:72px}.collapsed .module-sidebar span:not(.module-dot),.collapsed .sidebar-foot div,.collapsed .group-label,.collapsed .nav-state,.collapsed .nav-skeleton{display:none}.collapsed .nav-group a,.collapsed .module-picker{grid-template-columns:1fr;justify-items:center}.collapsed .module-picker span,.collapsed .module-picker .picker-arrow{display:none}.collapsed .sidebar-foot{justify-content:center}:global(.genre-picker-popover.el-popper){padding:6px;border-color:var(--border-soft);background:var(--panel);box-shadow:0 18px 45px rgba(0,0,0,.25)}:global(.genre-picker-menu){max-height:430px;overflow:auto}:global(.genre-picker-menu header){display:flex;align-items:center;justify-content:space-between;padding:9px 10px;border-bottom:1px solid var(--border-soft)}:global(.genre-picker-menu header b){font-size:10px}:global(.genre-picker-menu header span){color:var(--text-muted);font-size:8px}:global(.genre-picker-menu a){display:grid;grid-template-columns:8px 1fr;align-items:center;gap:9px;padding:9px 10px;border-radius:6px;color:var(--text-secondary);font-size:10px;text-decoration:none}:global(.genre-picker-menu a:hover),:global(.genre-picker-menu a.active){background:var(--accent-soft);color:var(--text)}:global(.genre-picker-menu a i){width:6px;height:6px;border-radius:50%}@keyframes loading{to{background-position:-200% 0}}@media(max-width:1050px){.module-app{padding-left:72px}.module-sidebar{width:72px}.module-sidebar span:not(.module-dot),.sidebar-foot div,.group-label,.nav-state,.nav-skeleton{display:none}.nav-group a,.module-picker{grid-template-columns:1fr;justify-items:center}.module-picker span,.module-picker .picker-arrow{display:none}.sidebar-foot{justify-content:center}}
</style>
<style scoped>
.genre-picker-section + .genre-picker-section { margin-top: 14px; }
.picker-empty { padding: 10px; border: 1px dashed var(--border); border-radius: 8px; color: var(--text-muted); font-size: 10px; text-align: center; }
</style>
