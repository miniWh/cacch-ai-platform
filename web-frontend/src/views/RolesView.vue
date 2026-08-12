<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { ApiError } from '../api/http'
import * as menusApi from '../api/menus'
import * as rolesApi from '../api/roles'
import type { ActiveStatus, MenuRecord, Role } from '../types/auth'

const loading = ref(false)
const saving = ref(false)
const items = ref<Role[]>([])
const menuOptions = ref<MenuRecord[]>([])

const drawerVisible = ref(false)
const drawerMode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const form = reactive({
  code: '',
  name: '',
  description: '',
  status: 'active' as ActiveStatus,
  menu_ids: [] as string[],
})

const menuLabelMap = computed(() =>
  Object.fromEntries(menuOptions.value.map((m) => [m.id, m.title])),
)

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error) return e.message
  return '操作失败'
}

function menuSummary(ids: string[]): string {
  if (!ids.length) return '—'
  return ids.map((id) => menuLabelMap.value[id] ?? id).join('、')
}

async function loadMenus() {
  const res = await menusApi.listMenus()
  menuOptions.value = res.items.filter((m) => m.status === 'active')
}

async function loadData() {
  loading.value = true
  try {
    const res = await rolesApi.listRoles()
    items.value = res.items
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  drawerMode.value = 'create'
  editingId.value = null
  form.code = ''
  form.name = ''
  form.description = ''
  form.status = 'active'
  form.menu_ids = []
  drawerVisible.value = true
}

function openEdit(row: Role) {
  drawerMode.value = 'edit'
  editingId.value = row.id
  form.code = row.code
  form.name = row.name
  form.description = row.description ?? ''
  form.status = row.status
  form.menu_ids = [...row.menu_ids]
  drawerVisible.value = true
}

async function onSave() {
  if (!form.code.trim() || !form.name.trim()) {
    ElMessage.warning('请填写角色编码和名称')
    return
  }
  saving.value = true
  try {
    if (drawerMode.value === 'create') {
      await rolesApi.createRole({
        code: form.code.trim(),
        name: form.name.trim(),
        description: form.description.trim() || null,
        menu_ids: form.menu_ids,
      })
      ElMessage.success('角色已创建')
    } else if (editingId.value != null) {
      await rolesApi.updateRole(editingId.value, {
        name: form.name.trim(),
        description: form.description.trim() || null,
        status: form.status,
        menu_ids: form.menu_ids,
      })
      ElMessage.success('角色已更新')
    }
    drawerVisible.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: Role) {
  const next: ActiveStatus = row.status === 'active' ? 'disabled' : 'active'
  try {
    await rolesApi.updateRole(row.id, { status: next })
    ElMessage.success(next === 'active' ? '已启用' : '已停用')
    await loadData()
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

onMounted(async () => {
  await loadMenus()
  await loadData()
})
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>角色管理</h1>
      <p>配置角色及其可访问的菜单权限</p>
    </div>

    <div class="panel">
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="openCreate">新建角色</el-button>
        <el-button :icon="Refresh" @click="loadData">刷新</el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="name" label="名称" min-width="140" />
        <el-table-column prop="description" label="描述" min-width="180" show-overflow-tooltip />
        <el-table-column label="菜单权限" min-width="220" show-overflow-tooltip>
          <template #default="{ row }">{{ menuSummary(row.menu_ids) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="warning" @click="toggleStatus(row)">
              {{ row.status === 'active' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-drawer
      v-model="drawerVisible"
      :title="drawerMode === 'create' ? '新建角色' : '编辑角色'"
      size="480px"
    >
      <el-form label-width="88px">
        <el-form-item label="编码" required>
          <el-input v-model="form.code" :disabled="drawerMode === 'edit'" placeholder="唯一编码" />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="角色名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" :rows="2" />
        </el-form-item>
        <el-form-item v-if="drawerMode === 'edit'" label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="菜单权限">
          <el-checkbox-group v-model="form.menu_ids">
            <el-checkbox v-for="m in menuOptions" :key="m.id" :label="m.id">
              {{ m.title }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="onSave">保存</el-button>
      </template>
    </el-drawer>
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
  display: flex;
  gap: 8px;
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
</style>
