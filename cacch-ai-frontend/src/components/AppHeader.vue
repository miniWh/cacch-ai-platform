<script setup lang="ts">
import { UserFilled } from '@element-plus/icons-vue'
import { currentApp } from '../mock/data'
</script>

<template>
  <header class="topbar">
    <div class="left">
      <router-link to="/chat" class="brand" title="CACCH AI 工作台">
        <img class="logo-img" src="/logo-cac-group.png" alt="泰禾集团 CAC GROUP" />
      </router-link>
      <span class="divider" />
      <span class="product">CACCH AI</span>
      <span class="app-name">{{ currentApp.name }}</span>
    </div>
    <div class="right">
      <div class="user">
        <el-avatar :size="28" class="avatar">
          <el-icon><UserFilled /></el-icon>
        </el-avatar>
        <span class="uname">张三</span>
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
  padding: 0 16px 0 12px;
  flex-shrink: 0;
}

.left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
}

.brand {
  display: flex;
  align-items: center;
  height: 40px;
}

.logo-img {
  height: 36px;
  width: auto;
  display: block;
  object-fit: contain;
}

.divider {
  width: 1px;
  height: 22px;
  background: var(--cacch-border);
}

.product {
  font-weight: 700;
  color: var(--cacch-primary-dark);
  font-size: 15px;
  white-space: nowrap;
}

.app-name {
  color: var(--cacch-text-secondary);
  font-size: 13px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.right {
  display: flex;
  align-items: center;
}

.user {
  display: flex;
  align-items: center;
  gap: 8px;
}

.avatar {
  background: var(--cacch-primary);
  color: #fff;
}

.uname {
  font-size: 14px;
}
</style>
