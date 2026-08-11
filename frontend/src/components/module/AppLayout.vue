<script setup lang="ts">
import { computed, onMounted, ref, type Component } from 'vue'
import { useRoute } from 'vue-router'
import * as ElementIcons from '@element-plus/icons-vue'
import { Collection, DataAnalysis, Files, Menu, Moon, Refresh, Setting, Sunny } from '@element-plus/icons-vue'
import { useGenreModulesStore } from '../../stores/genreModules'

const route = useRoute()
const store = useGenreModulesStore()
const collapsed = ref(false)
const theme = ref(localStorage.getItem('script-library-theme') || 'dark')
const isDark = computed(() => theme.value === 'dark')
const iconRegistry = ElementIcons as Record<string, Component>

onMounted(() => void store.fetchNavigationModules())

function toggleTheme() {
  theme.value = isDark.value ? 'light' : 'dark'
  document.documentElement.dataset.theme = theme.value
  localStorage.setItem('script-library-theme', theme.value)
}

function moduleActive(slug: string) {
  return route.name === 'genre-module' && route.params.slug === slug
}
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
          <RouterLink to="/genre-map" :class="{ active: route.path === '/genre-map' }"><el-icon><DataAnalysis /></el-icon><span>题材定位图</span></RouterLink>
          <RouterLink to="/settings/modules" :class="{ active: route.path === '/settings/modules' }"><el-icon><Setting /></el-icon><span>题材配置</span></RouterLink>
        </div>
        <div class="nav-group module-group">
          <span class="group-label">题材模块 <em>{{ store.modules.length }}</em></span>
          <div v-if="store.loading" class="nav-skeleton" aria-label="题材导航加载中"><i v-for="item in 5" :key="item"></i></div>
          <div v-else-if="store.error" class="nav-state error-state"><span>{{ store.error }}</span><button @click="store.fetchNavigationModules()"><el-icon><Refresh /></el-icon>重新加载</button></div>
          <div v-else-if="!store.modules.length" class="nav-state"><el-icon><Collection /></el-icon><span>暂无启用题材</span><RouterLink to="/settings/modules">前往创建</RouterLink></div>
          <RouterLink
            v-for="item in store.modules"
            v-else
            :key="item.id"
            :to="`/genres/${item.slug}`"
            :class="{ active: moduleActive(item.slug) }"
          >
            <el-icon><component :is="iconRegistry[item.icon] || Collection" /></el-icon>
            <span>{{ item.name }}</span>
            <i class="module-dot" :style="{ background: item.theme_color }"></i>
          </RouterLink>
        </div>

      </nav>
      <div class="sidebar-foot"><el-icon><Collection /></el-icon><div><b>内部内容资产</b><span>数据与文件由服务端持久化</span></div></div>
    </aside>

    <main class="module-main"><RouterView /></main>
  </div>
</template>

<style scoped>
.module-app{min-height:100vh;padding-left:238px;padding-top:64px;transition:padding-left .2s}.module-header{position:fixed;z-index:50;top:0;left:0;right:0;height:64px;display:flex;align-items:center;padding:0 22px;background:color-mix(in srgb,var(--bg-soft) 94%,transparent);border-bottom:1px solid var(--border-soft);backdrop-filter:blur(16px)}.brand{width:216px;display:flex;align-items:center;gap:10px}.brand-mark{width:34px;height:34px;display:grid;place-items:center;border-radius:9px;background:var(--accent);color:#17110a;font-family:"Songti SC",serif;font-weight:900}.brand b{display:block;font-size:15px}.brand small{display:block;margin-top:2px;color:var(--text-muted);font-size:7px;letter-spacing:.18em}.collapse-button,.header-actions button{width:34px;height:34px;display:grid;place-items:center;border:1px solid var(--border);border-radius:8px;background:var(--panel);color:var(--text-secondary);cursor:pointer}.header-context{flex:1;display:flex;align-items:center;gap:10px;margin-left:20px;color:var(--text-muted);font-size:11px}.header-context i{width:1px;height:12px;background:var(--border)}.header-context b{color:var(--text-secondary);font-weight:600}.header-actions{display:flex;align-items:center;gap:10px}.avatar{width:32px;height:32px;display:grid;place-items:center;border-radius:50%;background:linear-gradient(135deg,#475569,#1e293b);color:#fff;font-size:11px}
.module-sidebar{position:fixed;z-index:40;top:64px;bottom:0;left:0;width:238px;display:flex;flex-direction:column;padding:16px 12px;background:var(--bg-soft);border-right:1px solid var(--border-soft);transition:width .2s}.module-sidebar nav{flex:1;overflow-y:auto}.nav-group{padding-bottom:14px}.nav-group+.nav-group{padding-top:14px;border-top:1px solid var(--border-soft)}.group-label{display:flex;align-items:center;justify-content:space-between;margin:0 9px 8px;color:var(--text-muted);font-size:9px;font-weight:800;letter-spacing:.1em}.group-label em{color:var(--accent);font-style:normal}.nav-group a{min-height:37px;display:grid;grid-template-columns:22px 1fr auto;align-items:center;gap:8px;padding:7px 9px;border-radius:7px;color:var(--text-secondary);font-size:12px;text-decoration:none}.nav-group a:hover{background:var(--panel);color:var(--text)}.nav-group a.active{background:var(--accent-soft);color:var(--text);box-shadow:inset 2px 0 var(--accent)}.module-dot{width:7px;height:7px;border-radius:50%}.bottom-nav{margin-top:10px}.nav-skeleton{display:grid;gap:7px;padding:4px}.nav-skeleton i{height:34px;border-radius:7px;background:linear-gradient(90deg,var(--panel),var(--panel-raised),var(--panel));background-size:200% 100%;animation:loading 1.2s infinite}.nav-state{display:grid;justify-items:center;gap:7px;padding:20px 10px;border:1px dashed var(--border);border-radius:8px;color:var(--text-muted);font-size:9px;text-align:center}.nav-state a,.nav-state button{border:0;background:transparent;color:var(--accent);font-size:9px;text-decoration:none;cursor:pointer}.nav-state button{display:flex;align-items:center;gap:4px}.error-state{color:var(--danger)}.sidebar-foot{display:flex;align-items:center;gap:9px;padding:12px;border:1px solid var(--border-soft);border-radius:8px;color:var(--accent)}.sidebar-foot b,.sidebar-foot span{display:block}.sidebar-foot b{color:var(--text-secondary);font-size:10px}.sidebar-foot span{margin-top:3px;color:var(--text-muted);font-size:8px}.module-main{min-height:calc(100vh - 64px);background:var(--bg)}
.collapsed{padding-left:72px}.collapsed .module-sidebar{width:72px}.collapsed .module-sidebar span:not(.module-dot),.collapsed .sidebar-foot div,.collapsed .group-label,.collapsed .nav-state,.collapsed .nav-skeleton{display:none}.collapsed .nav-group a{grid-template-columns:1fr;justify-items:center}.collapsed .module-dot{display:none}.collapsed .sidebar-foot{justify-content:center}@keyframes loading{to{background-position:-200% 0}}@media(max-width:1050px){.module-app{padding-left:72px}.module-sidebar{width:72px}.module-sidebar span:not(.module-dot),.sidebar-foot div,.group-label,.nav-state,.nav-skeleton{display:none}.nav-group a{grid-template-columns:1fr;justify-items:center}.module-dot{display:none}.sidebar-foot{justify-content:center}}
</style>
