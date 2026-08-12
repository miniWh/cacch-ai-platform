<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Refresh } from '@element-plus/icons-vue'
import { ApiError } from '../api/http'
import { useAuthStore } from '../stores/auth'

const auth = useAuthStore()
const loading = ref(false)

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error) return e.message
  return '加载失败'
}

async function loadData() {
  loading.value = true
  try {
    await auth.loadMenuCatalog()
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>菜单管理</h1>
      <p>系统菜单由服务端维护，此处为只读列表（侧栏根据当前用户 menu_ids 过滤显示）</p>
    </div>

    <div class="panel">
      <div class="toolbar">
        <el-button :icon="Refresh" @click="loadData">刷新</el-button>
      </div>

      <el-table v-loading="loading" :data="auth.menuCatalog.value" stripe>
        <el-table-column prop="id" label="标识" width="120" />
        <el-table-column prop="title" label="菜单名称" min-width="160" />
        <el-table-column prop="path" label="路由" min-width="140" />
        <el-table-column prop="icon" label="图标" width="100" />
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<style scoped>
.page {
  padding: 20px 24px;
  height: 100%;
  overflow: auto;
}

.page-head h1 {
  margin: 0;
  font-size: 22px;
}

.page-head p {
  margin: 6px 0 0;
  color: var(--cacch-text-secondary);
  font-size: 13px;
}

.panel {
  margin-top: 16px;
  background: #fff;
  border: 1px solid var(--cacch-border);
  border-radius: 12px;
  padding: 12px;
}

.toolbar {
  margin-bottom: 12px;
}
</style>
