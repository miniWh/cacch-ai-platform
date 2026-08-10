<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import AppHeader from '../components/AppHeader.vue'
import AppSidebar from '../components/AppSidebar.vue'

const collapsed = ref(false)
const route = useRoute()
</script>

<template>
  <div class="shell">
    <AppHeader variant="workbench" />
    <div class="body">
      <AppSidebar v-model:collapsed="collapsed" />
      <main class="main">
        <slot>
          <router-view :key="route.fullPath" />
        </slot>
      </main>
    </div>
  </div>
</template>

<style scoped>
.shell {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.body {
  flex: 1;
  display: flex;
  min-height: 0;
}

.main {
  flex: 1;
  min-width: 0;
  overflow: auto;
  background: var(--cacch-bg);
}
</style>
