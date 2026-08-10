<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ChatDotRound,
  Document,
  Fold,
  Expand,
  List,
  Setting,
} from '@element-plus/icons-vue'
import { currentApp } from '../mock/data'

defineProps<{ collapsed?: boolean }>()
const emit = defineEmits<{ 'update:collapsed': [boolean] }>()

const route = useRoute()
const router = useRouter()

const active = computed(() => route.path)

const menus = [
  { path: '/chat', label: '对话台', icon: ChatDotRound },
  { path: '/sites', label: '站点清单', icon: List },
  { path: '/documents', label: '文档与任务', icon: Document },
  { path: '/settings', label: '应用配置', icon: Setting },
]

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <aside class="side" :class="{ collapsed }">
    <el-menu :default-active="active" class="side-menu" :collapse="collapsed">
      <el-menu-item v-for="m in menus" :key="m.path" :index="m.path" @click="go(m.path)">
        <el-icon><component :is="m.icon" /></el-icon>
        <span>{{ m.label }}</span>
      </el-menu-item>
    </el-menu>
    <button class="collapse-btn" type="button" @click="emit('update:collapsed', !collapsed)">
      <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
    </button>
    <div v-if="!collapsed" class="side-foot">{{ currentApp.name }}</div>
  </aside>
</template>

<style scoped>
.side {
  width: var(--cacch-sidebar-w);
  background: #fff;
  border-right: 1px solid var(--cacch-border);
  display: flex;
  flex-direction: column;
  transition: width 0.2s;
}

.side.collapsed {
  width: 64px;
}

.side-menu {
  border-right: none;
  flex: 1;
  padding-top: 8px;
}

.collapse-btn {
  margin: 8px;
  border: 1px solid var(--cacch-border);
  background: #fff;
  border-radius: 8px;
  height: 36px;
  cursor: pointer;
  color: var(--cacch-text-secondary);
}

.side-foot {
  padding: 12px;
  font-size: 12px;
  color: var(--cacch-text-secondary);
  border-top: 1px solid var(--cacch-border);
  line-height: 1.4;
}
</style>
