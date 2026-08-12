<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh } from '@element-plus/icons-vue'
import { ApiError } from '../api/http'
import * as orgsApi from '../api/orgs'
import type { ActiveStatus, Org } from '../types/auth'

const loading = ref(false)
const saving = ref(false)
const items = ref<Org[]>([])

const drawerVisible = ref(false)
const drawerMode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const form = reactive({
  parent_id: null as number | null,
  code: '',
  name: '',
  sort_order: 0,
  status: 'active' as ActiveStatus,
  remark: '',
})

const parentOptions = computed(() =>
  items.value
    .filter((o) => o.status === 'active')
    .map((o) => ({ value: o.id, label: o.name })),
)

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error) return e.message
  return '操作失败'
}

function parentName(parentId: number | null): string {
  if (parentId == null) return '—'
  return items.value.find((o) => o.id === parentId)?.name ?? String(parentId)
}

async function loadData() {
  loading.value = true
  try {
    const res = await orgsApi.listOrgs()
    items.value = res.items.sort((a, b) => a.sort_order - b.sort_order)
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  drawerMode.value = 'create'
  editingId.value = null
  form.parent_id = null
  form.code = ''
  form.name = ''
  form.sort_order = 0
  form.status = 'active'
  form.remark = ''
  drawerVisible.value = true
}

function openEdit(row: Org) {
  drawerMode.value = 'edit'
  editingId.value = row.id
  form.parent_id = row.parent_id
  form.code = row.code ?? ''
  form.name = row.name
  form.sort_order = row.sort_order
  form.status = row.status
  form.remark = row.remark ?? ''
  drawerVisible.value = true
}

async function onSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写组织名称')
    return
  }
  saving.value = true
  try {
    const body = {
      parent_id: form.parent_id,
      code: form.code.trim() || undefined,
      name: form.name.trim(),
      sort_order: form.sort_order,
      status: form.status,
      remark: form.remark.trim() || null,
    }
    if (drawerMode.value === 'create') {
      await orgsApi.createOrg(body)
      ElMessage.success('组织已创建')
    } else if (editingId.value != null) {
      await orgsApi.updateOrg(editingId.value, body)
      ElMessage.success('组织已更新')
    }
    drawerVisible.value = false
    await loadData()
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    saving.value = false
  }
}

async function toggleStatus(row: Org) {
  const next: ActiveStatus = row.status === 'active' ? 'disabled' : 'active'
  try {
    await orgsApi.updateOrg(row.id, { status: next })
    ElMessage.success(next === 'active' ? '已启用' : '已停用')
    await loadData()
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

onMounted(loadData)
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>组织管理</h1>
      <p>维护组织架构，支持上级组织与启用/停用</p>
    </div>

    <div class="panel">
      <div class="toolbar">
        <el-button type="primary" :icon="Plus" @click="openCreate">新建组织</el-button>
        <el-button :icon="Refresh" @click="loadData">刷新</el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="code" label="编码" width="120" />
        <el-table-column prop="name" label="名称" min-width="160" />
        <el-table-column label="上级组织" min-width="140">
          <template #default="{ row }">{{ parentName(row.parent_id) }}</template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="remark" label="备注" min-width="160" show-overflow-tooltip />
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
      :title="drawerMode === 'create' ? '新建组织' : '编辑组织'"
      size="420px"
    >
      <el-form label-width="88px">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" placeholder="组织名称" />
        </el-form-item>
        <el-form-item label="编码">
          <el-input v-model="form.code" placeholder="可选" />
        </el-form-item>
        <el-form-item label="上级组织">
          <el-select v-model="form.parent_id" clearable placeholder="无上级" style="width: 100%">
            <el-option
              v-for="opt in parentOptions"
              :key="opt.value"
              :label="opt.label"
              :value="opt.value"
              :disabled="opt.value === editingId"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="排序">
          <el-input-number v-model="form.sort_order" :min="0" />
        </el-form-item>
        <el-form-item label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" />
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
</style>
