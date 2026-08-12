<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ApiError } from '../api/http'
import * as menusApi from '../api/menus'
import * as orgsApi from '../api/orgs'
import * as rolesApi from '../api/roles'
import * as usersApi from '../api/users'
import { showPasswordOnce } from '../utils/password-dialog'
import type { ActiveStatus, HrPreview, MenuRecord, Org, Role, UserListItem } from '../types/auth'

const loading = ref(false)
const saving = ref(false)
const items = ref<UserListItem[]>([])
const total = ref(0)

const orgs = ref<Org[]>([])
const roles = ref<Role[]>([])
const menuOptions = ref<MenuRecord[]>([])

const keyword = ref('')
const filterOrgId = ref<number | null>(null)
const filterStatus = ref<ActiveStatus | ''>('')

const drawerVisible = ref(false)
const drawerMode = ref<'create' | 'edit'>('create')
const editingId = ref<number | null>(null)
const hrPreview = ref<HrPreview | null>(null)
const previewLoading = ref(false)

const form = reactive({
  mobile: '',
  org_id: null as number | null,
  role_id: null as number | null,
  menu_ids: [] as string[],
  remark: '',
  status: 'active' as ActiveStatus,
})

const orgOptions = computed(() =>
  orgs.value.filter((o) => o.status === 'active').map((o) => ({ value: o.id, label: o.name })),
)
const roleOptions = computed(() =>
  roles.value.filter((r) => r.status === 'active').map((r) => ({ value: r.id, label: r.name })),
)

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error) return e.message
  return '操作失败'
}

function formatTime(v: string | null): string {
  if (!v) return '—'
  return v.replace('T', ' ').slice(0, 19)
}

async function loadRefs() {
  const [orgRes, roleRes, menuRes] = await Promise.all([
    orgsApi.listOrgs(),
    rolesApi.listRoles(),
    menusApi.listMenus(),
  ])
  orgs.value = orgRes.items
  roles.value = roleRes.items
  menuOptions.value = menuRes.items.filter((m) => m.status === 'active')
}

async function loadData() {
  loading.value = true
  try {
    const res = await usersApi.listUsers({
      keyword: keyword.value.trim() || undefined,
      org_id: filterOrgId.value ?? undefined,
      status: filterStatus.value || undefined,
    })
    items.value = res.items
    total.value = res.total
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

watch(
  () => form.role_id,
  (roleId) => {
    if (drawerMode.value !== 'create' || roleId == null) return
    const role = roles.value.find((r) => r.id === roleId)
    if (role) form.menu_ids = [...role.menu_ids]
  },
)

async function previewMobile() {
  if (!form.mobile.trim()) {
    ElMessage.warning('请先输入手机号')
    return
  }
  previewLoading.value = true
  hrPreview.value = null
  try {
    const res = await usersApi.previewHr(form.mobile.trim())
    hrPreview.value = res
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    previewLoading.value = false
  }
}

function openCreate() {
  drawerMode.value = 'create'
  editingId.value = null
  form.mobile = ''
  form.org_id = null
  form.role_id = null
  form.menu_ids = []
  form.remark = ''
  form.status = 'active'
  hrPreview.value = null
  drawerVisible.value = true
}

function openEdit(row: UserListItem) {
  drawerMode.value = 'edit'
  editingId.value = row.id
  form.mobile = row.mobile
  form.org_id = row.org_id
  form.role_id = row.role_id
  form.menu_ids = [...row.menu_ids]
  form.remark = ''
  form.status = row.status
  hrPreview.value = null
  drawerVisible.value = true
}

async function onSave() {
  if (drawerMode.value === 'create') {
    if (!form.mobile.trim() || form.org_id == null) {
      ElMessage.warning('请填写手机号并选择组织')
      return
    }
    saving.value = true
    try {
      const res = await usersApi.createUser({
        mobile: form.mobile.trim(),
        org_id: form.org_id,
        role_id: form.role_id,
        menu_ids: form.menu_ids.length ? form.menu_ids : undefined,
        generate_password: true,
        remark: form.remark.trim() || null,
      })
      drawerVisible.value = false
      ElMessage.success('用户已创建')
      if (res.plain_password) {
        await showPasswordOnce(res.plain_password, '用户初始密码')
      }
      await loadData()
    } catch (e) {
      ElMessage.error(errMsg(e))
    } finally {
      saving.value = false
    }
    return
  }

  if (editingId.value == null) return

  saving.value = true
  try {
    await usersApi.updateUser(editingId.value, {
      org_id: form.org_id ?? undefined,
      role_id: form.role_id,
      menu_ids: form.menu_ids,
      status: form.status,
      remark: form.remark.trim() || null,
    })
    drawerVisible.value = false
    ElMessage.success('用户已更新')
    await loadData()
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    saving.value = false
  }
}

async function onResetPassword(row: UserListItem) {
  try {
    const res = await usersApi.resetPassword(row.id, { generate_password: true })
    if (res.plain_password) {
      await showPasswordOnce(res.plain_password, '重置密码')
    }
    ElMessage.success('密码已重置')
    await loadData()
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

async function toggleStatus(row: UserListItem) {
  const next: ActiveStatus = row.status === 'active' ? 'disabled' : 'active'
  try {
    await usersApi.updateUser(row.id, { status: next })
    ElMessage.success(next === 'active' ? '已启用' : '已停用')
    await loadData()
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

onMounted(async () => {
  await loadRefs()
  await loadData()
})
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>用户管理</h1>
      <p>创建平台用户、分配组织与角色，支持重置密码与启用/停用</p>
    </div>

    <div class="panel">
      <div class="toolbar">
        <el-input
          v-model="keyword"
          placeholder="姓名/手机号/工号"
          clearable
          style="width: 220px"
          @keyup.enter="loadData"
        />
        <el-select v-model="filterOrgId" clearable placeholder="组织" style="width: 160px">
          <el-option v-for="o in orgOptions" :key="o.value" :label="o.label" :value="o.value" />
        </el-select>
        <el-select v-model="filterStatus" clearable placeholder="状态" style="width: 120px">
          <el-option label="启用" value="active" />
          <el-option label="停用" value="disabled" />
        </el-select>
        <el-button type="primary" :icon="Search" @click="loadData">查询</el-button>
        <el-button type="primary" :icon="Plus" @click="openCreate">新建用户</el-button>
        <el-button :icon="Refresh" @click="loadData">刷新</el-button>
      </div>

      <el-table v-loading="loading" :data="items" stripe>
        <el-table-column prop="staff_no" label="工号" width="100" />
        <el-table-column prop="name" label="姓名" width="100" />
        <el-table-column prop="mobile" label="手机号" width="130" />
        <el-table-column prop="org_name" label="组织" min-width="120" />
        <el-table-column prop="role_name" label="角色" min-width="120" />
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="row.status === 'active' ? 'success' : 'info'">
              {{ row.status === 'active' ? '启用' : '停用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="须改密" width="80">
          <template #default="{ row }">
            <el-tag v-if="row.must_change_password" type="warning" size="small">是</el-tag>
            <span v-else>—</span>
          </template>
        </el-table-column>
        <el-table-column label="最后登录" width="170">
          <template #default="{ row }">{{ formatTime(row.last_login_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="220" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="onResetPassword(row)">重置密码</el-button>
            <el-button link type="warning" @click="toggleStatus(row)">
              {{ row.status === 'active' ? '停用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="foot">共 {{ total }} 条</div>
    </div>

    <el-drawer
      v-model="drawerVisible"
      :title="drawerMode === 'create' ? '新建用户' : '编辑用户'"
      size="520px"
    >
      <el-form label-width="88px">
        <el-form-item label="手机号" required>
          <div class="mobile-row">
            <el-input
              v-model="form.mobile"
              :disabled="drawerMode === 'edit'"
              placeholder="HR 手机号"
            />
            <el-button
              v-if="drawerMode === 'create'"
              :loading="previewLoading"
              @click="previewMobile"
            >
              HR 预览
            </el-button>
          </div>
        </el-form-item>
        <el-form-item v-if="hrPreview" label="HR 信息">
          <div class="hr-box">
            <div>{{ hrPreview.name }}（{{ hrPreview.staff_no }}）</div>
            <div class="sub">
              {{ hrPreview.email ?? '—' }} · {{ hrPreview.staff_status }}
            </div>
          </div>
        </el-form-item>
        <el-form-item label="组织" required>
          <el-select v-model="form.org_id" placeholder="选择组织" style="width: 100%">
            <el-option v-for="o in orgOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="form.role_id" clearable placeholder="可选" style="width: 100%">
            <el-option v-for="r in roleOptions" :key="r.value" :label="r.label" :value="r.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="菜单权限">
          <el-checkbox-group v-model="form.menu_ids">
            <el-checkbox v-for="m in menuOptions" :key="m.id" :label="m.id">
              {{ m.title }}
            </el-checkbox>
          </el-checkbox-group>
        </el-form-item>
        <el-form-item v-if="drawerMode === 'edit'" label="状态">
          <el-radio-group v-model="form.status">
            <el-radio value="active">启用</el-radio>
            <el-radio value="disabled">停用</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="2" />
        </el-form-item>
        <p v-if="drawerMode === 'create'" class="tip">
          创建后将自动生成随机密码，请通过弹窗保存。
        </p>
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
  flex-wrap: wrap;
  gap: 8px;
}

.foot {
  margin-top: 12px;
  font-size: 13px;
  color: var(--cacch-text-secondary);
}

.mobile-row {
  display: flex;
  gap: 8px;
  width: 100%;
}

.hr-box {
  font-size: 14px;
  line-height: 1.5;
}

.hr-box .sub {
  color: var(--cacch-text-secondary);
  font-size: 13px;
}

.tip {
  margin: 0;
  font-size: 12px;
  color: var(--cacch-text-secondary);
}

:deep(.el-checkbox-group) {
  display: flex;
  flex-direction: column;
  gap: 6px;
}
</style>
