<template>
  <div class="theme-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>{{ currentThemeLabel }} · 全国示范村</h1>
      <div class="count">{{ villages.length }} 个村庄</div>
    </div>

    <el-row :gutter="20">
      <el-col :span="12" v-for="v in villages" :key="v.id" style="margin-bottom: 20px;">
        <el-card class="village-card">
          <div class="card-content" @click="goDetail(v.id)">
            <img src="https://picsum.photos/id/104/150/150" class="village-img" />
            <div class="info">
              <h3>{{ v.name }}</h3>
              <p class="province">{{ v.province }} · {{ v.city }}</p>
              <p class="desc">{{ v.product_name || v.sub_category || (v.industry_type ? '特色产业：' + v.industry_type : '暂无简介') }}</p>
            </div>
          </div>
          <div class="card-actions">
            <el-button type="primary" size="small" link @click.stop="openBaike(v.baike_urls)">
              查看百度百科
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div v-if="villages.length === 0" class="empty">暂无该产业类型的示范村数据</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const themeType = route.params.type
const themeMap = { '茶': '茶乡', '果': '果乡', '药': '药材之乡', '渔': '渔乡', '菌': '菌乡', '花': '花乡' }
const currentThemeLabel = computed(() => themeMap[themeType] || themeType)
const villages = ref([])

onMounted(async () => {
  try {
    const res = await axios.get(`/api/villages?industry=${themeType}`)
    villages.value = res.data
  } catch (error) {
    console.error('获取主题村庄失败', error)
  }
})

const goDetail = (id) => router.push(`/village/${id}`)
const openBaike = (url) => {
  if (url) {
    let firstUrl = url.split(',')[0].trim()
    window.open(firstUrl, '_blank')
  } else {
    alert('暂无百科链接')
  }
}
</script>

<style scoped>
.theme-page {
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
  border-radius: 20px;
  overflow: hidden;
  transition: all 0.25s ease;
  border: none;
  box-shadow: 0 4px 12px rgba(0,0,0,0.05);
}
.village-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 24px -8px rgba(43,94,43,0.2);
}
.card-content {
  display: flex;
  gap: 16px;
  cursor: pointer;
  padding: 12px;
}
.village-img {
  width: 110px;
  height: 110px;
  object-fit: cover;
  border-radius: 16px;
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
  border-radius: 20px;
  padding: 2px 12px;
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
  padding: 0 12px 12px 0;
}
.empty {
  text-align: center;
  padding: 50px;
  color: #999;
}
</style>