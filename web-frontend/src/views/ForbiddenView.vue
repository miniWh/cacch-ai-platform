<script setup lang="ts">
import { useRouter } from 'vue-router'

const router = useRouter()

function goBack() {
  router.back()
}

function goHome() {
  router.push('/chat')
}
</script>

<template>
  <div class="page">
    <div class="card">
      <div class="code">403</div>
      <h1>无访问权限</h1>
      <p>您没有访问此页面的菜单权限，请联系管理员分配角色或菜单。</p>
      <div class="actions">
        <el-button @click="goBack">返回上一页</el-button>
        <el-button type="primary" @click="goHome">回到首页</el-button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--cacch-bg);
  padding: 24px;
}

.card {
  text-align: center;
  background: #fff;
  border: 1px solid var(--cacch-border);
  border-radius: 12px;
  padding: 40px 32px;
  max-width: 480px;
}

.code {
  font-size: 56px;
  font-weight: 700;
  color: var(--cacch-primary);
  line-height: 1;
}

.card h1 {
  margin: 12px 0 8px;
  font-size: 22px;
}

.card p {
  margin: 0 0 24px;
  color: var(--cacch-text-secondary);
  font-size: 14px;
  line-height: 1.6;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}
</style>
