<script setup lang="ts">
import { computed, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Search } from '@element-plus/icons-vue'
import { categoryLabel, mockSites } from '../mock/data'
import type { SourceSite, SiteStatus } from '../types'

const sites = ref<SourceSite[]>(structuredClone(mockSites))
const keyword = ref('')
const region = ref('')
const category = ref('')
const status = ref('')

const drawerVisible = ref(false)
const drawerMode = ref<'create' | 'edit'>('edit')
const form = reactive<SourceSite>({
  site_id: '',
  name: '',
  region: 'US',
  category: 'registration',
  entry_url: '',
  crawl_mode: 'connector',
  allowed_domains: [],
  status: 'active',
  notes: '',
  last_probe_at: null,
  last_probe_status: null,
})
const domainsText = ref('')

const filtered = computed(() =>
  sites.value.filter((s) => {
    const q = keyword.value.trim().toLowerCase()
    if (q && !(`${s.name} ${s.entry_url}`.toLowerCase().includes(q))) return false
    if (region.value && s.region !== region.value) return false
    if (category.value && s.category !== category.value) return false
    if (status.value && s.status !== status.value) return false
    return true
  }),
)

function statusType(st: SiteStatus) {
  if (st === 'active') return 'success'
  if (st === 'pending_url') return 'warning'
  if (st === 'broken') return 'danger'
  return 'info'
}

function openCreate() {
  drawerMode.value = 'create'
  Object.assign(form, {
    site_id: `site_${Date.now()}`,
    name: '',
    region: 'CN',
    category: 'registration',
    entry_url: '',
    crawl_mode: 'manual',
    allowed_domains: [],
    status: 'pending_url',
    notes: '',
    last_probe_at: null,
    last_probe_status: null,
  })
  domainsText.value = ''
  drawerVisible.value = true
}

function openEdit(row: SourceSite) {
  drawerMode.value = 'edit'
  Object.assign(form, structuredClone(row))
  domainsText.value = row.allowed_domains.join('\n')
  drawerVisible.value = true
}

function save() {
  if (!form.name.trim()) {
    ElMessage.warning('请填写名称')
    return
  }
  form.allowed_domains = domainsText.value
    .split(/[\n,]/)
    .map((x) => x.trim())
    .filter(Boolean)
  if (!form.entry_url.trim()) form.status = 'pending_url'

  const idx = sites.value.findIndex((s) => s.site_id === form.site_id)
  const payload = structuredClone(form)
  if (idx >= 0) sites.value[idx] = payload
  else sites.value.unshift(payload)
  drawerVisible.value = false
  ElMessage.success('已保存（测试数据，仅前端）')
}

function probeOne(row: SourceSite) {
  row.last_probe_at = new Date().toLocaleString('zh-CN', { hour12: false })
  if (!row.entry_url) {
    row.last_probe_status = 'skip'
    row.status = 'pending_url'
    ElMessage.warning(`${row.name} 无入口 URL，标记为 pending_url`)
    return
  }
  row.last_probe_status = '200'
  if (row.status === 'broken') row.status = 'active'
  ElMessage.success(`${row.name} 探活完成（模拟）`)
}

function probeBatch() {
  filtered.value.forEach((row) => probeOne(row))
}

function toggleDisable(row: SourceSite) {
  if (row.status === 'disabled') {
    row.status = row.entry_url ? 'active' : 'pending_url'
    ElMessage.success('已启用')
  } else {
    row.status = 'disabled'
    ElMessage.success('已停用')
  }
}
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>站点清单</h1>
      <p>仅页面维护 · 归属当前 App 知识库</p>
    </div>

    <div class="toolbar">
      <el-input
        v-model="keyword"
        clearable
        placeholder="搜索名称或 URL"
        :prefix-icon="Search"
        class="search"
      />
      <el-select v-model="region" clearable placeholder="地区 全部" class="filter">
        <el-option label="US" value="US" />
        <el-option label="EU" value="EU" />
        <el-option label="UK" value="UK" />
        <el-option label="AU" value="AU" />
        <el-option label="JP" value="JP" />
        <el-option label="CN" value="CN" />
        <el-option label="INT" value="INT" />
      </el-select>
      <el-select v-model="category" clearable placeholder="类别 全部" class="filter">
        <el-option label="登记" value="registration" />
        <el-option label="评审" value="evaluation" />
        <el-option label="标准" value="standard" />
        <el-option label="数据库" value="database" />
      </el-select>
      <el-select v-model="status" clearable placeholder="状态 全部" class="filter">
        <el-option label="active" value="active" />
        <el-option label="pending_url" value="pending_url" />
        <el-option label="broken" value="broken" />
        <el-option label="disabled" value="disabled" />
      </el-select>
      <div class="spacer" />
      <el-button type="primary" :icon="Plus" @click="openCreate">新建站点</el-button>
      <el-button @click="probeBatch">批量探活</el-button>
    </div>

    <div class="table-wrap">
      <el-table :data="filtered" stripe height="100%" empty-text="暂无站点，点击「新建站点」添加">
        <el-table-column prop="name" label="名称" min-width="160" fixed />
        <el-table-column prop="region" label="地区" width="80" />
        <el-table-column label="类别" width="90">
          <template #default="{ row }">{{ categoryLabel[row.category] || row.category }}</template>
        </el-table-column>
        <el-table-column label="入口 URL" min-width="240" show-overflow-tooltip>
          <template #default="{ row }">
            <a v-if="row.entry_url" :href="row.entry_url" target="_blank" rel="noreferrer">{{
              row.entry_url
            }}</a>
            <span v-else class="muted">—</span>
          </template>
        </el-table-column>
        <el-table-column prop="crawl_mode" label="采集模式" width="120" />
        <el-table-column label="状态" width="120">
          <template #default="{ row }">
            <el-tag :type="statusType(row.status)" size="small" effect="light">{{ row.status }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="最近探活" width="110">
          <template #default="{ row }">
            {{ row.last_probe_status || '—' }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="openEdit(row)">编辑</el-button>
            <el-button link type="primary" @click="probeOne(row)">探活</el-button>
            <el-button link type="primary" @click="toggleDisable(row)">
              {{ row.status === 'disabled' ? '启用' : '停用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-drawer
      v-model="drawerVisible"
      :title="drawerMode === 'create' ? '新建站点' : '编辑站点'"
      size="420px"
      destroy-on-close
    >
      <el-form label-position="top">
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="地区" required>
          <el-select v-model="form.region" style="width: 100%">
            <el-option v-for="r in ['US', 'EU', 'UK', 'AU', 'JP', 'CN', 'INT']" :key="r" :label="r" :value="r" />
          </el-select>
        </el-form-item>
        <el-form-item label="类别" required>
          <el-select v-model="form.category" style="width: 100%">
            <el-option label="登记" value="registration" />
            <el-option label="评审" value="evaluation" />
            <el-option label="标准" value="standard" />
            <el-option label="数据库" value="database" />
          </el-select>
        </el-form-item>
        <el-form-item label="入口 URL">
          <el-input v-model="form.entry_url" placeholder="可留空，状态将为 pending_url" />
        </el-form-item>
        <el-form-item label="采集模式" required>
          <el-select v-model="form.crawl_mode" style="width: 100%">
            <el-option label="manual" value="manual" />
            <el-option label="single_page" value="single_page" />
            <el-option label="list_harvest" value="list_harvest" />
            <el-option label="connector" value="connector" />
          </el-select>
        </el-form-item>
        <el-form-item label="域名白名单">
          <el-input
            v-model="domainsText"
            type="textarea"
            :rows="3"
            placeholder="每行一个域名"
            maxlength="1000"
            show-word-limit
          />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.notes" type="textarea" :rows="4" maxlength="500" show-word-limit />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="drawerVisible = false">取消</el-button>
        <el-button type="primary" @click="save">保存</el-button>
      </template>
    </el-drawer>
  </div>
</template>

<style scoped>
.page {
  height: 100%;
  padding: 20px 24px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 0;
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

.toolbar {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
}

.search {
  width: 240px;
}

.filter {
  width: 130px;
}

.spacer {
  flex: 1;
}

.table-wrap {
  flex: 1;
  min-height: 320px;
  background: #fff;
  border: 1px solid var(--cacch-border);
  border-radius: 12px;
  padding: 8px;
  overflow: hidden;
}

.muted {
  color: var(--cacch-text-secondary);
}
</style>
