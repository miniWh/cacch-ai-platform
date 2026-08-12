<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ApiError } from '../api/http'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = reactive({
  oldPassword: '',
  newPassword: '',
  confirmPassword: '',
})
const loading = ref(false)

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error) return e.message
  return '修改失败'
}

async function onSubmit() {
  if (!form.oldPassword || !form.newPassword) {
    ElMessage.warning('请填写完整')
    return
  }
  if (form.newPassword.length < 8) {
    ElMessage.warning('新密码至少 8 位')
    return
  }
  if (form.newPassword !== form.confirmPassword) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  loading.value = true
  try {
    await auth.changePassword(form.oldPassword, form.newPassword)
    ElMessage.success('密码已修改')
    await router.replace('/chat')
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <div class="card">
      <h1>修改密码</h1>
      <p v-if="auth.mustChangePassword.value" class="hint">
        首次登录或管理员重置密码后，请先修改密码后再使用系统。
      </p>
      <p v-else class="hint">您可以在此修改登录密码。</p>

      <el-form label-position="top" class="form" @submit.prevent="onSubmit">
        <el-form-item label="当前密码">
          <el-input
            v-model="form.oldPassword"
            type="password"
            show-password
            placeholder="请输入当前密码"
          />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input
            v-model="form.newPassword"
            type="password"
            show-password
            placeholder="至少 8 位"
          />
        </el-form-item>
        <el-form-item label="确认新密码">
          <el-input
            v-model="form.confirmPassword"
            type="password"
            show-password
            placeholder="再次输入新密码"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-button type="primary" :loading="loading" @click="onSubmit">
          确认修改
        </el-button>
      </el-form>
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
  width: 100%;
  max-width: 440px;
  background: #fff;
  border: 1px solid var(--cacch-border);
  border-radius: 12px;
  padding: 28px;
}

.card h1 {
  margin: 0;
  font-size: 22px;
}

.hint {
  margin: 8px 0 20px;
  font-size: 13px;
  color: var(--cacch-text-secondary);
  line-height: 1.5;
}

.form {
  max-width: 100%;
}
</style>
