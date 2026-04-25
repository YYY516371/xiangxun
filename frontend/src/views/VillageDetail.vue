<template>
  <div class="village-detail" v-loading="loading">
    <div class="mock-banner" v-if="usingMockData">
      ⚠️ 当前使用虚拟数据（后端接口未就绪，部分信息为示例）
    </div>

    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <el-button @click="goRanking" type="info" plain>🔥 热门排行榜</el-button>
    </div>

    <div v-if="village" class="content">
      <div class="title-section">
        <h1>{{ simplifyName(village.name) }}</h1>
        <div class="tags">
          <el-tag type="success">{{ village.industry_type || '特色产业' }}</el-tag>
          <el-tag v-if="village.product_name" type="info">主打产品：{{ village.product_name }}</el-tag>
        </div>
        <div class="action-buttons">
          <el-button :type="isLiked ? 'danger' : 'default'" @click="toggleLike" :loading="likeLoading">
            <el-icon><StarFilled v-if="isLiked" /><Star v-else /></el-icon>
            {{ isLiked ? '已点赞' : '点赞' }}
          </el-button>
          <el-button :type="isFavorited ? 'warning' : 'default'" @click="toggleFavorite" :loading="favLoading">
            <el-icon><Collection /></el-icon>
            {{ isFavorited ? '已收藏' : '收藏' }}
          </el-button>
          <el-button :type="isWanted ? 'success' : 'default'" @click="toggleWant" :loading="wantLoading">
            <el-icon><Flag /></el-icon>
            {{ isWanted ? '已想去' : '想去' }}
          </el-button>
        </div>
      </div>

      <div class="image-wrapper">
        <img src="https://picsum.photos/id/104/800/400" class="main-image" />
      </div>

      <div class="section">
        <h2>村庄简介</h2>
        <p><strong>地址：</strong>{{ village.province }} · {{ village.city }} · {{ village.county || '' }}</p>
        <p><strong>特产：</strong>{{ village.sub_category ? village.sub_category + ' - ' : '' }}{{ village.product_name || '无' }}</p>
        <div v-if="village.baike_urls" class="baike-link">
          <el-button type="primary" link @click="openBaike(village.baike_urls)">
            📖 查看百度百科完整介绍
          </el-button>
        </div>
      </div>

      <div class="section story">
        <h2>✨ AI 为你讲述村庄故事</h2>
        <div v-if="village.ai_story" class="story-content">
          <p>{{ village.ai_story }}</p>
        </div>
        <div v-else class="story-placeholder">
          <p>还没有生成故事，点击下方按钮，AI 将为你创作一段专属介绍。</p>
          <el-button type="primary" @click="generateStory" :loading="storyLoading">生成 AI 故事</el-button>
        </div>
      </div>

      <div class="section comments-section">
        <h2>💬 用户评论</h2>
        <div v-if="comments.length" class="comment-list">
          <div v-for="c in comments" :key="c.id" class="comment-item">
            <div class="comment-header">
              <strong>{{ c.username }}</strong>
              <span class="comment-time">{{ formatDate(c.createdAt) }}</span>
            </div>
            <p>{{ c.content }}</p>
          </div>
          <div v-if="showMoreComments" class="show-more">
            <el-button link @click="loadAllComments">查看全部评论</el-button>
          </div>
        </div>
        <div v-else class="comment-empty">暂无评论，抢个沙发吧～</div>

        <div v-if="isLoggedIn" class="comment-input">
          <el-input v-model="newComment" type="textarea" rows="3" placeholder="分享你的看法..." />
          <div class="comment-actions">
            <el-button type="primary" @click="submitComment" :loading="commentLoading">发表评论</el-button>
          </div>
        </div>
        <div v-else class="login-prompt">
          <el-button link @click="goLogin">登录后发表评论</el-button>
        </div>
      </div>
    </div>

    <div v-else class="empty">
      <h2>未找到该村庄信息</h2>
      <el-button @click="$router.back()">返回上一页</el-button>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Star, StarFilled, Collection, Flag } from '@element-plus/icons-vue'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const villageId = route.params.id

const village = ref(null)
const loading = ref(false)
const storyLoading = ref(false)
const usingMockData = ref(false)

const isLiked = ref(false)
const isFavorited = ref(false)
const isWanted = ref(false)
const likeLoading = ref(false)
const favLoading = ref(false)
const wantLoading = ref(false)

const comments = ref([])
const newComment = ref('')
const commentLoading = ref(false)
const showMoreComments = ref(false)
const allCommentsLoaded = ref(false)

const token = localStorage.getItem('token')
const isLoggedIn = computed(() => !!token)

const simplifyName = (fullName) => {
  if (!fullName) return ''
  let name = fullName
  const districtIdx = name.indexOf('区')
  if (districtIdx !== -1) name = name.substring(districtIdx + 1)
  const townIdx = name.indexOf('镇')
  if (townIdx !== -1) name = name.substring(townIdx + 1)
  return name || fullName
}

const formatDate = (isoString) => {
  if (!isoString) return ''
  const date = new Date(isoString)
  return `${date.getMonth()+1}/${date.getDate()} ${date.getHours()}:${date.getMinutes().toString().padStart(2,'0')}`
}

const fetchUserInteractions = async () => {
  if (!isLoggedIn.value) return
  try {
    const res = await axios.get(`/api/villages/${villageId}/interactions`)
    isLiked.value = res.data.liked
    isFavorited.value = res.data.favorited
    isWanted.value = res.data.wanted
  } catch (error) {
    console.error('获取用户交互状态失败', error)
  }
}

const toggleLike = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  likeLoading.value = true
  try {
    if (isLiked.value) {
      await axios.post(`/api/villages/${villageId}/unlike`)
      isLiked.value = false
      ElMessage.success('已取消点赞')
    } else {
      await axios.post(`/api/villages/${villageId}/like`)
      isLiked.value = true
      ElMessage.success('点赞成功')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    likeLoading.value = false
  }
}

const toggleFavorite = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  favLoading.value = true
  try {
    if (isFavorited.value) {
      await axios.post(`/api/villages/${villageId}/unfavorite`)
      isFavorited.value = false
      ElMessage.success('已取消收藏')
    } else {
      await axios.post(`/api/villages/${villageId}/favorite`)
      isFavorited.value = true
      ElMessage.success('收藏成功')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    favLoading.value = false
  }
}

const toggleWant = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  wantLoading.value = true
  try {
    if (isWanted.value) {
      await axios.post(`/api/villages/${villageId}/unwant`)
      isWanted.value = false
      ElMessage.success('已取消想去')
    } else {
      await axios.post(`/api/villages/${villageId}/want`)
      isWanted.value = true
      ElMessage.success('已添加到想去列表')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '操作失败')
  } finally {
    wantLoading.value = false
  }
}

const loadComments = async (loadAll = false) => {
  try {
    const params = loadAll ? {} : { limit: 5 }
    const res = await axios.get(`/api/villages/${villageId}/comments`, { params })
    comments.value = res.data
    showMoreComments.value = (!loadAll && res.data.length === 5)
    allCommentsLoaded.value = loadAll
  } catch (error) {
    console.error('加载评论失败', error)
  }
}

const loadAllComments = async () => {
  await loadComments(true)
}

const submitComment = async () => {
  if (!newComment.value.trim()) {
    ElMessage.warning('请输入评论内容')
    return
  }
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录')
    router.push('/login')
    return
  }
  commentLoading.value = true
  try {
    await axios.post(`/api/villages/${villageId}/comments`, { content: newComment.value })
    await loadComments(false)
    newComment.value = ''
    ElMessage.success('评论成功')
  } catch (error) {
    ElMessage.error(error.response?.data?.message || '评论失败')
  } finally {
    commentLoading.value = false
  }
}

const generateStory = async () => {
  if (!isLoggedIn.value) {
    ElMessage.warning('请先登录以使用AI故事功能')
    router.push('/login')
    return
  }
  storyLoading.value = true
  try {
    const res = await axios.post(`/api/generate_story/${villageId}`)
    village.value.ai_story = res.data.story
    ElMessage.success('故事生成成功！')
  } catch (error) {
    ElMessage.error('生成失败，请稍后重试')
  } finally {
    storyLoading.value = false
  }
}

const openBaike = (url) => {
  if (url && url !== 'NaN') {
    let firstUrl = url.split(',')[0].split('|')[0].trim()
    if (firstUrl.startsWith('http')) window.open(firstUrl, '_blank')
    else ElMessage.warning('百科链接无效')
  } else {
    ElMessage.warning('暂无百科链接')
  }
}

const loadVillage = async () => {
  loading.value = true
  try {
    const res = await axios.get(`/api/village/${villageId}`)
    if (res.data && res.data.id) {
      village.value = res.data
      usingMockData.value = false
    } else {
      throw new Error('数据格式错误')
    }
  } catch (error) {
    console.error('加载失败', error)
    usingMockData.value = true
    ElMessage.error('加载村庄信息失败，使用模拟数据')
    // 可选：填充模拟数据
  } finally {
    loading.value = false
  }
}

const goRanking = () => router.push('/ranking')
const goLogin = () => router.push('/login')

onMounted(async () => {
  await loadVillage()
  await fetchUserInteractions()
  await loadComments(false)
})
</script>

<style scoped>
.village-detail {
  max-width: 1000px;
  margin: 40px auto;
  padding: 0 24px;
}
.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.title-section {
  background: white;
  border-radius: 32px;
  padding: 24px 28px;
  margin-bottom: 24px;
  box-shadow: 0 8px 20px rgba(0,0,0,0.05);
  border: 1px solid rgba(219,203,184,0.5);
}
.title-section h1 {
  font-size: 2.2rem;
  font-weight: 700;
  color: #2b5e2b;
  margin: 0 0 12px;
}
.tags {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 16px;
}
.action-buttons {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}
.image-wrapper {
  margin: 24px 0;
  border-radius: 32px;
  overflow: hidden;
  box-shadow: 0 8px 20px rgba(0,0,0,0.1);
}
.main-image {
  width: 100%;
  max-height: 420px;
  object-fit: cover;
  display: block;
  transition: transform 0.3s;
}
.image-wrapper:hover .main-image {
  transform: scale(1.02);
}
.section {
  background: white;
  border-radius: 28px;
  padding: 24px 28px;
  margin: 24px 0;
  box-shadow: 0 4px 12px rgba(0,0,0,0.03);
  border: 1px solid #f1e7dd;
}
.section h2 {
  font-size: 1.6rem;
  font-weight: 600;
  color: #2b5e2b;
  border-left: 4px solid #e67e22;
  padding-left: 16px;
  margin-bottom: 20px;
}
.baike-link {
  margin-top: 20px;
  padding-top: 12px;
  border-top: 1px dashed #ddd0bc;
}
.story-content {
  background: #fdf9ef;
  border-radius: 24px;
  padding: 24px;
  font-size: 1rem;
  line-height: 1.7;
  color: #4a3b2a;
  border-left: 6px solid #e67e22;
}
.story-placeholder {
  background: #faf5ea;
  border-radius: 24px;
  padding: 40px 24px;
  text-align: center;
  color: #9b8568;
}
.comments-section {
  background: #fefcf7;
}
.comment-item {
  border-bottom: 1px solid #eee;
  padding: 12px 0;
}
.comment-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 6px;
}
.comment-time {
  font-size: 12px;
  color: #999;
}
.comment-empty {
  text-align: center;
  padding: 20px;
  color: #aaa;
}
.comment-input {
  margin-top: 20px;
}
.comment-actions {
  margin-top: 12px;
  text-align: right;
}
.login-prompt {
  text-align: center;
  margin-top: 16px;
}
.show-more {
  text-align: center;
  margin-top: 12px;
}
.empty {
  text-align: center;
  padding: 80px 20px;
}
@media (max-width: 768px) {
  .village-detail { padding: 0 16px; margin: 20px auto; }
  .title-section h1 { font-size: 1.6rem; }
}
</style>