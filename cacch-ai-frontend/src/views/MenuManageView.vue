<script setup lang="ts">
import { ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Bottom, Top } from '@element-plus/icons-vue'
import { useMenuStore } from '../stores/menu'

const { allMenus, setVisible, rename, move, resetMenus } = useMenuStore()
const editingId = ref('')
const editingTitle = ref('')

function startEdit(id: string, title: string) {
  editingId.value = id
  editingTitle.value = title
}

function commitEdit(id: string) {
  rename(id, editingTitle.value)
  editingId.value = ''
  ElMessage.success('菜单名称已更新')
}

function onVisibleChange(id: string, value: string | number | boolean) {
  setVisible(id, Boolean(value))
  ElMessage.success(value ? '已显示到侧栏' : '已从侧栏隐藏')
}

function onReset() {
  resetMenus()
  ElMessage.success('已恢复默认菜单')
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>菜单管理</h1>
      <p>动态配置左侧导航：显示/隐藏、排序、重命名（保存在浏览器本地，Mock 阶段）</p>
    </div>

    <div class="panel">
      <div class="toolbar">
        <el-button @click="onReset">恢复默认</el-button>
      </div>

      <el-table :data="allMenus" stripe>
        <el-table-column label="排序" width="120">
          <template #default="{ row }">
            <el-button :icon="Top" circle size="small" @click="move(row.id, 'up')" />
            <el-button :icon="Bottom" circle size="small" @click="move(row.id, 'down')" />
          </template>
        </el-table-column>
        <el-table-column prop="id" label="标识" width="120" />
        <el-table-column label="菜单名称" min-width="200">
          <template #default="{ row }">
            <div v-if="editingId === row.id" class="edit-row">
              <el-input v-model="editingTitle" size="small" @keyup.enter="commitEdit(row.id)" />
              <el-button size="small" type="primary" @click="commitEdit(row.id)">确定</el-button>
              <el-button size="small" @click="editingId = ''">取消</el-button>
            </div>
            <div v-else class="name-row">
              <span>{{ row.title }}</span>
              <el-button link type="primary" @click="startEdit(row.id, row.title)">重命名</el-button>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="path" label="路由" min-width="140" />
        <el-table-column label="侧栏显示" width="120">
          <template #default="{ row }">
            <el-switch
              :model-value="row.visible"
              :disabled="row.locked"
              @change="(v: boolean) => onVisibleChange(row.id, v)"
            />
            <span v-if="row.locked" class="tip">锁定</span>
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

.name-row,
.edit-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.tip {
  margin-left: 6px;
  font-size: 12px;
  color: var(--cacch-text-secondary);
}
</style>
