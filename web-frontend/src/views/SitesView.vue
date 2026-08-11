<script setup lang="ts">
import { onMounted, reactive, ref, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { Plus, Refresh, Search } from '@element-plus/icons-vue'
import { ApiError } from '../api/http'
import { ensureDefaultKnowledgeBase } from '../api/kb'
import {
  createSource,
  listSources,
  probeSources,
  updateSource,
} from '../api/sources'
import { categoryLabel } from '../mock/data'
import type { SourceSite, SiteStatus } from '../types'

const kbId = ref<number | null>(null)
const kbName = ref('')
const sites = ref<SourceSite[]>([])
const total = ref(0)
const loading = ref(false)
const saving = ref(false)

const keyword = ref('')
const region = ref('')
const category = ref('')
const status = ref('')

const drawerVisible = ref(false)
const drawerMode = ref<'create' | 'edit'>('edit')
const form = reactive({
  site_id: '',
  name: '',
  region: 'CN' as SourceSite['region'],
  category: 'registration' as SourceSite['category'],
  entry_url: '',
  crawl_mode: 'manual' as SourceSite['crawl_mode'],
  status: 'pending_url' as SiteStatus,
  notes: '',
})
const domainsText = ref('')

function statusType(st: SiteStatus) {
  if (st === 'active') return 'success'
  if (st === 'pending_url') return 'warning'
  if (st === 'broken') return 'danger'
  return 'info'
}

function errMsg(e: unknown) {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error) return e.message
  return '请求失败'
}

async function ensureKb() {
  const kb = await ensureDefaultKnowledgeBase()
  kbId.value = kb.id
  kbName.value = kb.name
}

async function loadSites() {
  if (kbId.value == null) return
  loading.value = true
  try {
    const data = await listSources(kbId.value, {
      keyword: keyword.value.trim() || undefined,
      region: region.value || undefined,
      category: category.value || undefined,
      status: status.value || undefined,
    })
    sites.value = data.items
    total.value = data.total
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}

function openCreate() {
  drawerMode.value = 'create'
  Object.assign(form, {
    site_id: '',
    name: '',
    region: 'CN',
    category: 'registration',
    entry_url: '',
    crawl_mode: 'manual',
    status: 'pending_url',
    notes: '',
  })
  domainsText.value = ''
  drawerVisible.value = true
}

function openEdit(row: SourceSite) {
  drawerMode.value = 'edit'
  Object.assign(form, {
    site_id: row.site_id,
    name: row.name,
    region: row.region,
    category: row.category,
    entry_url: row.entry_url || '',
    crawl_mode: row.crawl_mode,
    status: row.status,
    notes: row.notes || '',
  })
  domainsText.value = (row.allowed_domains || []).join('\n')
  drawerVisible.value = true
}

async function save() {
  if (kbId.value == null) return
  if (!form.name.trim()) {
    ElMessage.warning('请填写名称')
    return
  }
  if (drawerMode.value === 'create' && !form.site_id.trim()) {
    ElMessage.warning('请填写站点 ID（英文/数字/下划线）')
    return
  }

  const domains = domainsText.value
    .split(/[\n,]/)
    .map((x) => x.trim())
    .filter(Boolean)
  const entryUrl = form.entry_url.trim() || null

  saving.value = true
  try {
    if (drawerMode.value === 'create') {
      await createSource(kbId.value, {
        site_id: form.site_id.trim(),
        name: form.name.trim(),
        region: form.region,
        category: form.category,
        entry_url: entryUrl,
        crawl_mode: form.crawl_mode,
        allowed_domains: domains,
        notes: form.notes.trim() || null,
      })
      ElMessage.success('已创建')
    } else {
      await updateSource(kbId.value, form.site_id, {
        name: form.name.trim(),
        region: form.region,
        category: form.category,
        entry_url: entryUrl,
        crawl_mode: form.crawl_mode,
        allowed_domains: domains,
        status: form.status,
        notes: form.notes.trim() || null,
      })
      ElMessage.success('已保存')
    }
    drawerVisible.value = false
    await loadSites()
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    saving.value = false
  }
}

async function probeOne(row: SourceSite) {
  if (kbId.value == null) return
  try {
    const data = await probeSources(kbId.value, [row.site_id])
    const item = data.results[0]
    ElMessage.success(
      item
        ? `${item.name} 探活完成：${item.last_probe_status || '—'}`
        : '探活完成',
    )
    await loadSites()
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

async function probeBatch() {
  if (kbId.value == null) return
  if (!sites.value.length) {
    ElMessage.warning('当前列表无站点')
    return
  }
  try {
    const data = await probeSources(
      kbId.value,
      sites.value.map((s) => s.site_id),
    )
    ElMessage.success(`批量探活完成：${data.results.length} 条`)
    await loadSites()
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

async function toggleDisable(row: SourceSite) {
  if (kbId.value == null) return
  const next: SiteStatus =
    row.status === 'disabled'
      ? row.entry_url
        ? 'active'
        : 'pending_url'
      : 'disabled'
  try {
    await updateSource(kbId.value, row.site_id, { status: next })
    ElMessage.success(next === 'disabled' ? '已停用' : '已启用')
    await loadSites()
  } catch (e) {
    ElMessage.error(errMsg(e))
  }
}

let searchTimer: number | undefined
watch([keyword, region, category, status], () => {
  window.clearTimeout(searchTimer)
  searchTimer = window.setTimeout(() => {
    void loadSites()
  }, 300)
})

onMounted(async () => {
  try {
    await ensureKb()
    await loadSites()
  } catch (e) {
    ElMessage.error(`初始化失败：${errMsg(e)}`)
  }
})
</script>

<template>
  <div class="page">
    <div class="page-head">
      <h1>站点清单</h1>
      <p>
        功能模块站点维护 · 对接后端 API
        <template v-if="kbId != null">
          · 知识库 #{{ kbId }}（{{ kbName }}）· 共 {{ total }} 条
        </template>
      </p>
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
      <el-button :icon="Refresh" :loading="loading" @click="loadSites">刷新</el-button>
      <el-button type="primary" :icon="Plus" @click="openCreate">新建站点</el-button>
      <el-button :loading="loading" @click="probeBatch">批量探活</el-button>
    </div>

    <div class="table-wrap" v-loading="loading">
      <el-table :data="sites" stripe height="100%" empty-text="暂无站点，点击「新建站点」添加">
        <el-table-column prop="name" label="名称" min-width="160" fixed />
        <el-table-column prop="site_id" label="站点 ID" min-width="120" show-overflow-tooltip />
        <el-table-column prop="region" label="地区" width="80" />
        <el-table-column label="类别" width="90">
          <template #default="{ row }">{{ categoryLabel[row.category] || row.category }}</template>
        </el-table-column>
        <el-table-column label="入口 URL" min-width="220" show-overflow-tooltip>
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
            <el-tag :type="statusType(row.status)" size="small" effect="light">{{
              row.status
            }}</el-tag>
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
        <el-form-item label="站点 ID" required>
          <el-input
            v-model="form.site_id"
            :disabled="drawerMode === 'edit'"
            placeholder="如 us_ppis（英文/数字/_/-）"
          />
        </el-form-item>
        <el-form-item label="名称" required>
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="地区" required>
          <el-select v-model="form.region" style="width: 100%">
            <el-option
              v-for="r in ['US', 'EU', 'UK', 'AU', 'JP', 'CN', 'INT']"
              :key="r"
              :label="r"
              :value="r"
            />
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
        <el-form-item v-if="drawerMode === 'edit'" label="状态">
          <el-select v-model="form.status" style="width: 100%">
            <el-option label="active" value="active" />
            <el-option label="pending_url" value="pending_url" />
            <el-option label="broken" value="broken" />
            <el-option label="disabled" value="disabled" />
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
        <el-button type="primary" :loading="saving" @click="save">保存</el-button>
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
