import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/materials' },
    { path: '/materials', name: 'materials', component: () => import('../views/materials/MaterialLibraryView.vue') },
    { path: '/genre-map', name: 'genre-map', component: () => import('../views/GenreMapView.vue') },
    { path: '/genres/:slug', name: 'genre-module', component: () => import('../views/GenreModuleView.vue') },
    { path: '/settings/modules', name: 'module-settings', component: () => import('../views/settings/ModuleSettingsView.vue') },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundView.vue') },
  ],
  scrollBehavior: () => ({ top: 0 }),
})
