<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ApiError } from '../api/http'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()

const form = reactive({
  mobile: '',
  password: '',
  rememberToday: false,
})
const loading = ref(false)

function errMsg(e: unknown): string {
  if (e instanceof ApiError) return e.message
  if (e instanceof Error) return e.message
  return '登录失败'
}

async function onSubmit() {
  if (!form.mobile.trim() || !form.password) {
    ElMessage.warning('请输入手机号和密码')
    return
  }
  loading.value = true
  try {
    await auth.login(form.mobile.trim(), form.password, form.rememberToday)
    ElMessage.success('登录成功')
    if (auth.mustChangePassword.value) {
      await router.replace('/change-password')
    } else {
      const redirect = (route.query.redirect as string) || '/chat'
      await router.replace(redirect)
    }
  } catch (e) {
    ElMessage.error(errMsg(e))
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-page">
    <div class="login-card">
      <div class="brand-block">
        <img class="logo" src="/logo-cac-group.png" alt="泰禾集团" />
        <h1>CACCH AI 智能平台</h1>
        <p>请使用手机号登录</p>
      </div>

      <el-form label-position="top" @submit.prevent="onSubmit">
        <el-form-item label="手机号">
          <el-input
            v-model="form.mobile"
            placeholder="请输入手机号"
            maxlength="11"
            clearable
            size="large"
          />
        </el-form-item>
        <el-form-item label="密码">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            size="large"
            @keyup.enter="onSubmit"
          />
        </el-form-item>
        <el-form-item>
          <el-checkbox v-model="form.rememberToday">今日免登录</el-checkbox>
        </el-form-item>
        <el-button
          type="primary"
          size="large"
          class="submit-btn"
          :loading="loading"
          @click="onSubmit"
        >
          登录
        </el-button>
      </el-form>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  min-height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: var(--cacch-bg);
  padding: 24px;
}

.login-card {
  width: 100%;
  max-width: 400px;
  background: #fff;
  border: 1px solid var(--cacch-border);
  border-radius: 12px;
  padding: 32px 28px;
  box-shadow: 0 4px 24px rgba(15, 23, 42, 0.06);
}

.brand-block {
  text-align: center;
  margin-bottom: 28px;
}

.logo {
  height: 48px;
  width: auto;
  margin-bottom: 16px;
}

.brand-block h1 {
  margin: 0;
  font-size: 20px;
  color: var(--cacch-text);
}

.brand-block p {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--cacch-text-secondary);
}

.submit-btn {
  width: 100%;
  margin-top: 4px;
}
</style>
