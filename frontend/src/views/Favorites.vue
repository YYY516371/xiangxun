<template>
  <div class="favorites-page">
    <!-- 模拟数据提示（可选，因收藏数据来自 localStorage，但若后端接口失败可提示） -->
    <div v-if="usingMockData" class="mock-banner">
      ⚠️ 当前部分数据为虚拟示例（后端接口未就绪）
    </div>

    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>我的收藏</h1>
      <div class="count">{{ favoritesList.length }} 个村庄</div>
    </div>

    <el-row :gutter="20">
      <el-col :span="12" v-for="v in favoritesList" :key="v.id" style="margin-bottom: 20px;">
        <el-card class="village-card">
          <div class="card-content" @click="goDetail(v.id)">
            <img src="https://picsum.photos/id/104/150/150" class="village-img" />
            <div class="info">
              <h3>{{ simplifyName(v.name) }}</h3>
              <p class="province">{{ v.province }} · {{ v.industry_type }}</p>
              <p class="desc">{{ v.product_name || v.sub_category || (v.industry_type ? '特色产业：' + v.industry_type : '暂无简介') }}</p>
            </div>
          </div>
          <div class="card-actions">
            <el-button type="danger" size="small" @click="removeFavorite(v.id)">取消收藏</el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div v-if="favoritesList.length === 0" class="empty">
      <el-empty description="暂无收藏，去首页添加吧" />
      <el-button type="primary" @click="$router.push('/')">去首页浏览</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import axios from 'axios'

const router = useRouter()
const favoritesList = ref([])
const usingMockData = ref(false)

// 简化村名（与其他页面一致）
const simplifyName = (fullName) => {
  if (!fullName) return ''
  let name = fullName
  const districtIdx = name.indexOf('区')
  if (districtIdx !== -1) name = name.substring(districtIdx + 1)
  const townIdx = name.indexOf('镇')
  if (townIdx !== -1) name = name.substring(townIdx + 1)
  return name || fullName
}

const getFavoriteIds = () => {
  const fav = localStorage.getItem('favoriteVillages')
  return fav ? JSON.parse(fav) : []
}

const loadFavorites = async () => {
  const ids = getFavoriteIds()
  if (ids.length === 0) {
    favoritesList.value = []
    return
  }
  try {
    const promises = ids.map(id => axios.get(`/api/village/${id}`))
    const responses = await Promise.all(promises)
    favoritesList.value = responses.map(res => res.data)
    usingMockData.value = false
  } catch (error) {
    console.error('加载收藏失败，使用模拟数据', error)
    usingMockData.value = true
    // 模拟数据（根据 id 生成示例，实际可省略或提示）
    ElMessage.warning('加载部分收藏失败，显示示例数据')
    favoritesList.value = []
  }
}

const removeFavorite = (id) => {
  const ids = getFavoriteIds()
  const newIds = ids.filter(i => i !== id)
  localStorage.setItem('favoriteVillages', JSON.stringify(newIds))
  favoritesList.value = favoritesList.value.filter(v => v.id !== id)
  ElMessage.success('已取消收藏')
}

const goDetail = (id) => {
  router.push(`/village/${id}`)
}

onMounted(() => {
  loadFavorites()
})
</script>

<style scoped>
.favorites-page {
  padding: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: baseline;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 32px;
  border-left: 5px solid #e67e22;
  padding-left: 20px;
}

.header h1 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #2b5e2b;
  margin: 0;
}

.count {
  background: #e8dccc;
  padding: 4px 12px;
  border-radius: 40px;
  font-size: 0.85rem;
  font-weight: 500;
  color: #5a3e2b;
}

.village-card {
  border-radius: 24px;
  overflow: hidden;
  transition: all 0.25s ease;
  border: none;
  background: rgba(255, 255, 245, 0.8);
  backdrop-filter: blur(4px);
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.05);
}

.village-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 30px -12px rgba(43, 94, 43, 0.15);
}

.card-content {
  display: flex;
  gap: 16px;
  cursor: pointer;
  padding: 16px;
}

.village-img {
  width: 110px;
  height: 110px;
  object-fit: cover;
  border-radius: 20px;
  transition: transform 0.3s;
}

.village-card:hover .village-img {
  transform: scale(1.02);
}

.info h3 {
  font-size: 1.25rem;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #2b5e2b;
}

.province {
  display: inline-block;
  background: #f0e7db;
  border-radius: 40px;
  padding: 4px 14px;
  font-size: 0.75rem;
  color: #8b5a2b;
  margin-bottom: 8px;
}

.desc {
  font-size: 0.85rem;
  color: #5a5a4a;
  line-height: 1.4;
}

.card-actions {
  text-align: right;
  padding: 0 16px 16px 0;
}

.empty {
  text-align: center;
  padding: 80px 20px;
  background: rgba(255, 255, 245, 0.5);
  border-radius: 32px;
}

@media (max-width: 768px) {
  .favorites-page {
    padding: 16px;
  }
  .header h1 {
    font-size: 1.4rem;
  }
  .village-img {
    width: 70px;
    height: 70px;
  }
  .info h3 {
    font-size: 1rem;
  }
}
</style>