<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ChatDotRound,
  Document,
  Fold,
  Expand,
  List,
  Menu as MenuIcon,
  Setting,
} from '@element-plus/icons-vue'
import { useMenuStore, type MenuIconName } from '../stores/menu'

defineProps<{ collapsed?: boolean }>()
const emit = defineEmits<{ 'update:collapsed': [boolean] }>()

const route = useRoute()
const router = useRouter()
const { visibleMenus } = useMenuStore()

const iconMap: Record<MenuIconName, unknown> = {
  chat: ChatDotRound,
  list: List,
  document: Document,
  setting: Setting,
  menu: MenuIcon,
}

const active = computed(() => route.path)
const menuKey = computed(() => visibleMenus.value.map((m) => `${m.id}:${m.title}:${m.sort}`).join('|'))

function go(path: string) {
  router.push(path)
}
</script>

<template>
  <aside class="side" :class="{ collapsed }">
    <el-menu :key="menuKey" :default-active="active" :collapse="collapsed" class="side-menu">
      <el-menu-item
        v-for="m in visibleMenus"
        :key="m.id"
        :index="m.path"
        @click="go(m.path)"
      >
        <el-icon><component :is="iconMap[m.icon]" /></el-icon>
        <template #title>{{ m.title }}</template>
      </el-menu-item>
    </el-menu>
    <button class="collapse-btn" type="button" @click="emit('update:collapsed', !collapsed)">
      <el-icon><Fold v-if="!collapsed" /><Expand v-else /></el-icon>
      <span v-if="!collapsed">收起菜单</span>
    </button>
    <div v-if="!collapsed" class="side-foot">CACCH AI 工作台</div>
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
  flex-shrink: 0;
}

.side.collapsed {
  width: 64px;
}

.side-menu {
  border-right: none;
  flex: 1;
  padding-top: 8px;
  overflow: auto;
}

.collapse-btn {
  margin: 8px;
  border: 1px solid var(--cacch-border);
  background: #fff;
  border-radius: 8px;
  height: 36px;
  cursor: pointer;
  color: var(--cacch-text-secondary);
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  font-size: 13px;
}

.side-foot {
  padding: 12px;
  font-size: 12px;
  color: var(--cacch-text-secondary);
  border-top: 1px solid var(--cacch-border);
  line-height: 1.4;
}
</style>
