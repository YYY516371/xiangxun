<template>
  <div class="login-page">
    <div class="bg-decoration"></div>
    <el-card class="login-card">
      <h2>{{ isLogin ? '登录' : '注册' }}</h2>
      <el-form :model="form" :rules="rules" ref="formRef">
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" autocomplete="off" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input type="password" v-model="form.password" />
        </el-form-item>
        <el-form-item v-if="!isLogin" label="确认密码" prop="confirmPassword">
          <el-input type="password" v-model="form.confirmPassword" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="submit" :loading="loading">{{ isLogin ? '登录' : '注册' }}</el-button>
          <el-button @click="toggleMode">{{ isLogin ? '没有账号？去注册' : '已有账号？去登录' }}</el-button>
        </el-form-item>
      </el-form>
      <div v-if="useMock" class="mock-tip">
        ⚡ 当前使用模拟模式（后端未就绪），数据仅保存在浏览器中。
      </div>
    </el-card>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const isLogin = ref(true)
const loading = ref(false)
const formRef = ref(null)

// 临时开关：true = 使用模拟存储，false = 调用真实后端
const useMock = ref(true)  // 后端就绪后改为 false

const form = reactive({
  username: '',
  password: '',
  confirmPassword: ''
})

const rules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
  confirmPassword: [
    { validator: (rule, value, callback) => {
      if (!isLogin.value && value !== form.password) {
        callback(new Error('两次输入密码不一致'))
      } else {
        callback()
      }
    }, trigger: 'blur' }
  ]
}

// 模拟注册
const mockRegister = () => {
  const users = JSON.parse(localStorage.getItem('mock_users') || '[]')
  if (users.find(u => u.username === form.username)) {
    ElMessage.error('用户名已存在')
    return false
  }
  users.push({ username: form.username, password: form.password })
  localStorage.setItem('mock_users', JSON.stringify(users))
  ElMessage.success('注册成功，请登录')
  isLogin.value = true
  form.password = ''
  form.confirmPassword = ''
  return true
}

// 模拟登录
const mockLogin = () => {
  const users = JSON.parse(localStorage.getItem('mock_users') || '[]')
  const user = users.find(u => u.username === form.username && u.password === form.password)
  if (!user) {
    ElMessage.error('用户名或密码错误')
    return false
  }
  // 生成模拟 token
  const token = `mock-token-${Date.now()}`
  userStore.setToken(token)
  userStore.setUser({ username: user.username })
  ElMessage.success('登录成功')
  router.push('/')
  return true
}

const submit = async () => {
  await formRef.value.validate()
  loading.value = true
  try {
    if (useMock.value) {
      // 模拟模式
      if (isLogin.value) {
        mockLogin()
      } else {
        mockRegister()
      }
    } else {
      // 真实后端模式
      if (isLogin.value) {
        const res = await axios.post('/api/auth/login', {
          username: form.username,
          password: form.password
        })
        userStore.setToken(res.data.token)
        userStore.setUser(res.data.user)
        ElMessage.success('登录成功')
        router.push('/')
      } else {
        await axios.post('/api/auth/register', {
          username: form.username,
          password: form.password
        })
        ElMessage.success('注册成功，请登录')
        isLogin.value = true
        form.password = ''
        form.confirmPassword = ''
      }
    }
  } catch (err) {
    ElMessage.error(err.response?.data?.message || '操作失败')
  } finally {
    loading.value = false
  }
}

const toggleMode = () => {
  isLogin.value = !isLogin.value
  form.password = ''
  form.confirmPassword = ''
}
</script>

<style scoped>
.login-page {
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(145deg, #fef9ef 0%, #f0ede5 100%);
  overflow: hidden;
}

/* 背景装饰（自然元素） */
.bg-decoration {
  position: absolute;
  width: 100%;
  height: 100%;
  pointer-events: none;
  background-image: radial-gradient(circle at 10% 20%, rgba(43,94,43,0.05) 0%, transparent 50%),
                    radial-gradient(circle at 90% 80%, rgba(230,126,34,0.05) 0%, transparent 60%);
  z-index: 0;
}

.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  background: rgba(255, 255, 245, 0.9);
  backdrop-filter: blur(12px);
  border-radius: 48px;
  border: 1px solid rgba(219, 203, 184, 0.5);
  box-shadow: 0 25px 45px -12px rgba(0, 0, 0, 0.2);
  transition: all 0.3s ease;
}

.login-card :deep(.el-card__body) {
  padding: 32px 28px;
}

.login-card h2 {
  text-align: center;
  font-size: 28px;
  font-weight: 600;
  color: #2b5e2b;
  margin-bottom: 28px;
  letter-spacing: 1px;
}

.login-card :deep(.el-form-item__label) {
  font-weight: 500;
  color: #5a3e2b;
}

.login-card :deep(.el-input__wrapper) {
  border-radius: 40px;
  background: rgba(255,255,240,0.8);
  box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  transition: all 0.2s;
}

.login-card :deep(.el-input__wrapper:hover) {
  background: rgba(255,255,240,1);
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.login-card :deep(.el-input__wrapper.is-focus) {
  border-color: #e67e22;
  box-shadow: 0 0 0 1px #e67e22;
}

.login-card .el-button {
  border-radius: 40px;
  padding: 10px 24px;
  font-weight: 500;
  transition: all 0.2s;
}

.login-card .el-button--primary {
  background-color: #2b5e2b;
  border-color: #2b5e2b;
}

.login-card .el-button--primary:hover {
  background-color: #1e3f1e;
  border-color: #1e3f1e;
  transform: translateY(-2px);
  box-shadow: 0 6px 14px rgba(43,94,43,0.3);
}

.login-card .el-button:not(.el-button--primary) {
  background: transparent;
  border: none;
  color: #8b6b4a;
}

.login-card .el-button:not(.el-button--primary):hover {
  color: #e67e22;
  background: rgba(230,126,34,0.1);
}

.mock-tip {
  margin-top: 20px;
  font-size: 12px;
  color: #e6a23c;
  text-align: center;
  background: rgba(230,162,60,0.1);
  padding: 8px 12px;
  border-radius: 40px;
  backdrop-filter: blur(4px);
}

@media (max-width: 480px) {
  .login-card {
    width: 90%;
  }
  .login-card :deep(.el-card__body) {
    padding: 24px 20px;
  }
  .login-card h2 {
    font-size: 24px;
  }
}
</style>