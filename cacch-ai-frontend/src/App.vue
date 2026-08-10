<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import WorkbenchLayout from './layouts/WorkbenchLayout.vue'

const route = useRoute()
const useWorkbench = computed(() => route.meta.layout === 'workbench')
</script>

<template>
  <WorkbenchLayout v-if="useWorkbench" />
  <router-view v-else />
</template>
