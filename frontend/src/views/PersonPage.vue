<template>
  <div class="person-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>个人中心</h1>
    </div>

    <!-- 用户信息卡片 -->
    <el-card class="profile-card">
      <div class="profile-header">
        <el-avatar :size="80" :src="userInfo.avatar || 'https://picsum.photos/id/64/80/80'" />
        <div class="info">
          <h2>{{ userInfo.username || '游客' }}</h2>
          <p>注册时间：{{ userInfo.regtime || '未知' }}</p>
        </div>
      </div>
    </el-card>

    <!-- 三个标签页 -->
    <el-tabs v-model="activeTab" class="tabs">
      <el-tab-pane label="我的收藏" name="favorites">
        <el-row :gutter="20">
          <el-col :span="12" v-for="v in paginatedFavorites" :key="v.id" style="margin-bottom: 20px;">
            <el-card @click="goDetail(v.id)" class="village-card">
              <div class="card-content">
                <img src="https://picsum.photos/id/104/100/100" class="village-img" />
                <div class="info">
                  <h3>{{ simplifyName(v.name) }}</h3>
                  <p>{{ v.product_name || '特色产品' }}</p>
                </div>
              </div>
              <div class="card-actions">
                <el-button type="danger" size="small" @click.stop="removeFavorite(v.id)">取消收藏</el-button>
              </div>
            </el-card>
          </el-col>
        </el-row>
        <div class="pagination">
          <el-pagination
            v-model:current-page="favPage"
            :page-size="favPageSize"
            :total="favoritesList.length"
            layout="prev, pager, next"
            @current-change="favPageChange"
          />
        </div>
      </el-tab-pane>

      <el-tab-pane label="我的想去" name="wants">
        <!-- 类似结构，数据 wantsList -->
      </el-tab-pane>

      <el-tab-pane label="我的点赞" name="likes">
        <!-- 类似结构，数据 likesList -->
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const activeTab = ref('favorites')

// 用户信息
const userInfo = ref({})

// 收藏列表
const favoritesList = ref([])
const favPage = ref(1)
const favPageSize = ref(6)
const paginatedFavorites = computed(() => {
  const start = (favPage.value - 1) * favPageSize.value
  return favoritesList.value.slice(start, start + favPageSize.value)
})

// 想去列表、点赞列表（结构类似，省略）

const simplifyName = (fullName) => { /* 同其他页面 */ }

const goDetail = (id) => router.push(`/village/${id}`)

const removeFavorite = async (id) => {
  // 调用后端取消收藏接口
  await axios.post(`/api/villages/${id}/unfavorite`)
  favoritesList.value = favoritesList.value.filter(v => v.id !== id)
  ElMessage.success('已取消收藏')
}

// 加载用户数据和收藏列表等
const loadUserData = async () => {
  try {
    const res = await axios.get('/api/user/profile')
    userInfo.value = res.data
    const favRes = await axios.get('/api/user/favorites')
    favoritesList.value = favRes.data
    // 类似加载 wants, likes
  } catch (error) {
    console.error('加载个人数据失败', error)
  }
}

onMounted(() => loadUserData())
</script>

<style scoped>
/* 样式参考其他页面，略 */
</style>