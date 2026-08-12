<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { UserFilled } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const displayName = computed(() => auth.user.value?.name || '用户')

async function onLogout() {
  try {
    await ElMessageBox.confirm('确定退出登录？', '退出', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
    })
    await auth.logout()
    await router.replace('/login')
  } catch {
    /* cancelled */
  }
}
</script>

<template>
  <header class="topbar">
    <div class="left">
      <router-link to="/" class="brand" title="CACCH AI 平台">
        <img class="logo-img" src="/logo-cac-group.png" alt="泰禾集团 CAC GROUP" />
      </router-link>
      <span class="divider" />
      <span class="product">CACCH AI</span>
      <span class="product-sub">智能平台</span>
    </div>
    <div class="right">
      <div class="user">
        <el-avatar :size="32" class="avatar">
          <el-icon><UserFilled /></el-icon>
        </el-avatar>
        <span class="uname">{{ displayName }}</span>
        <el-button link type="primary" class="logout" @click="onLogout">退出</el-button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.topbar {
  height: 72px;
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
  gap: 14px;
  min-width: 0;
}

.brand {
  display: flex;
  align-items: center;
  height: 64px;
}

.logo-img {
  height: 58px;
  width: auto;
  max-width: 320px;
  display: block;
  object-fit: contain;
}

.divider {
  width: 1px;
  height: 28px;
  background: var(--cacch-border);
}

.product {
  font-weight: 700;
  color: var(--cacch-text);
  font-size: 16px;
  white-space: nowrap;
}

.product-sub {
  color: var(--cacch-text-secondary);
  font-size: 13px;
  white-space: nowrap;
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

.logout {
  margin-left: 4px;
}
</style>
