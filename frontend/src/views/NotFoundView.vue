<template>
  <section class="not-found">
    <span>404</span>
    <h1>页面不存在</h1>
    <p>当前地址没有对应的题材或设置页面。</p>
    <RouterLink to="/settings/modules">返回模块设置</RouterLink>
  </section>
</template>

<style scoped>
.not-found{min-height:calc(100vh - 64px);display:grid;place-content:center;justify-items:center;color:var(--text-muted)}
.not-found span{color:var(--accent);font:700 54px/1 monospace}.not-found h1{margin:14px 0 6px;color:var(--text);font-size:22px}.not-found p{margin:0 0 18px;font-size:11px}.not-found a{padding:9px 14px;border-radius:8px;background:var(--accent);color:#17110a;text-decoration:none;font-size:11px;font-weight:700}
</style>
