<script setup lang="ts">
import { QuestionFilled, Reading, Setting, UserFilled } from '@element-plus/icons-vue'
import { currentApp } from '../mock/data'

withDefaults(
  defineProps<{
    showAppName?: boolean
    variant?: 'workbench' | 'chat'
  }>(),
  { showAppName: true, variant: 'workbench' },
)
</script>

<template>
  <header class="topbar" :class="variant">
    <div class="left">
      <div class="logo">
        <span class="logo-mark">⬡</span>
        <strong>CACCH AI</strong>
      </div>
      <template v-if="variant === 'workbench' && showAppName">
        <span class="divider" />
        <span class="app-name">{{ currentApp.name }}</span>
      </template>
      <template v-else-if="variant === 'chat'">
        <div class="chips">
          <span class="chip">
            <el-icon><Reading /></el-icon>
            {{ currentApp.name }}
          </span>
          <span class="chip">
            <el-icon><Setting /></el-icon>
            {{ currentApp.model_profile_id }}
          </span>
        </div>
      </template>
    </div>
    <div class="right">
      <el-button v-if="variant === 'chat'" text :icon="QuestionFilled" />
      <el-button v-if="variant === 'chat'" text :icon="Reading" />
      <el-button v-if="variant === 'chat'" text :icon="Setting" />
      <div class="user">
        <el-avatar :size="28" class="avatar">
          <el-icon><UserFilled /></el-icon>
        </el-avatar>
        <span v-if="variant === 'workbench'" class="uname">张三</span>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  height: var(--cacch-header-h);
  background: #fff;
  border-bottom: 1px solid var(--cacch-border);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 16px 0 20px;
  flex-shrink: 0;
}

.left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.logo {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--cacch-primary-dark);
}

.logo-mark {
  color: var(--cacch-primary);
  font-size: 18px;
}

.divider {
  width: 1px;
  height: 18px;
  background: var(--cacch-border);
}

.app-name {
  color: var(--cacch-text-secondary);
  font-size: 14px;
}

.chips {
  display: flex;
  gap: 8px;
  margin-left: 8px;
}

.chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--cacch-border);
  border-radius: 999px;
  padding: 4px 12px;
  font-size: 13px;
  color: var(--cacch-text);
  background: #fff;
}

.right {
  display: flex;
  align-items: center;
  gap: 4px;
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 8px;
}

.avatar {
  background: var(--cacch-primary);
  color: #fff;
}

.uname {
  font-size: 14px;
}
</style>
