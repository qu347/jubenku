import { createRouter, createWebHistory } from 'vue-router'

export default createRouter({
  history: createWebHistory(),
  routes: [
    { path: '/', redirect: '/materials' },
    { path: '/materials', name: 'materials', component: () => import('../views/materials/MaterialLibraryView.vue') },
    { path: '/scripts', name: 'scripts', component: () => import('../views/materials/MaterialLibraryView.vue'), props: { libraryType: 'script' } },
    { path: '/genre-map', name: 'genre-map', component: () => import('../views/GenreMapView.vue') },
    { path: '/genres/:slug', name: 'genre-materials', component: () => import('../views/GenreModuleView.vue'), props: { libraryType: 'material' } },
    { path: '/script-genres/:slug', name: 'genre-scripts', component: () => import('../views/GenreModuleView.vue'), props: { libraryType: 'script' } },
    { path: '/settings/modules', name: 'module-settings', component: () => import('../views/settings/ModuleSettingsView.vue') },
    { path: '/:pathMatch(.*)*', name: 'not-found', component: () => import('../views/NotFoundView.vue') },
  ],
  scrollBehavior: () => ({ top: 0 }),
})
