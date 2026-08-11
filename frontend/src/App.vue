<script setup lang="ts">
import { onMounted } from 'vue'
import AppLayout from './components/module/AppLayout.vue'

onMounted(() => {
  document.documentElement.dataset.theme = localStorage.getItem('script-library-theme') || 'dark'
})
</script>

<template><AppLayout /></template>

