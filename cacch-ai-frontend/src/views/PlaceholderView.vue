<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

const route = useRoute()
const title = computed(() => (route.meta.title as string) || '页面')
const hint = computed(() => (route.meta.hint as string) || '功能开发中')
</script>

<template>
  <div class="placeholder">
    <h1>{{ title }}</h1>
    <p>{{ hint }}</p>
  </div>
</template>

<style scoped>
.placeholder {
  padding: 48px 24px;
  text-align: center;
  color: var(--cacch-text-secondary);
}

h1 {
  color: var(--cacch-text);
  margin-bottom: 8px;
}
</style>
