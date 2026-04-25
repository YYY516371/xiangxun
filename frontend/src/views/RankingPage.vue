<template>
  <div class="ranking-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>排行榜</h1>
    </div>

    <el-tabs v-model="activeRanking" class="ranking-tabs">
      <el-tab-pane label="点赞排行榜" name="like">
        <div v-for="village in likeRankingList" :key="village.id" class="ranking-item">
          <el-card>
            <div class="village-info">
              <span class="rank">#{{ village.rank }}</span>
              <span class="name">{{ village.name }}</span>
              <span class="count">{{ village.likeCount }} 点赞</span>
              <el-button size="small" @click="goDetail(village.id)">查看详情</el-button>
            </div>
            <!-- 热门评论区域 -->
            <div class="hot-comments">
              <h4>热门评论</h4>
              <div v-for="comment in village.topComments" :key="comment.id" class="comment">
                <div class="comment-user">{{ comment.username }}</div>
                <div class="comment-content">{{ comment.content }}</div>
                <div class="comment-footer">
                  <span>{{ comment.likeCount }} 点赞</span>
                  <el-button size="small" link @click="likeComment(comment.id)">点赞</el-button>
                </div>
              </div>
              <div v-if="!village.topComments?.length" class="no-comment">暂无热门评论</div>
            </div>
          </el-card>
        </div>
      </el-tab-pane>

      <el-tab-pane label="旅行排行榜" name="want">
        <!-- 结构类似，数据 from wantRankingList -->
      </el-tab-pane>
    </el-tabs>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { ElMessage } from 'element-plus'

const router = useRouter()
const activeRanking = ref('like')
const likeRankingList = ref([])
const wantRankingList = ref([])

// 加载排行榜数据（需要后端提供接口）
const loadRankings = async () => {
  try {
    const likeRes = await axios.get('/api/rankings/like')  // 返回 [{ id, name, likeCount, rank, topComments: [{ id, username, content, likeCount }] }]
    likeRankingList.value = likeRes.data
    const wantRes = await axios.get('/api/rankings/want')
    wantRankingList.value = wantRes.data
  } catch (error) {
    console.error('加载排行榜失败', error)
  }
}

const goDetail = (id) => router.push(`/village/${id}`)

// 评论点赞
const likeComment = async (commentId) => {
  try {
    await axios.post(`/api/comments/${commentId}/like`)
    // 更新本地数据（重新加载或乐观更新）
    ElMessage.success('点赞成功')
  } catch (error) {
    ElMessage.error('点赞失败')
  }
}

onMounted(() => {
  loadRankings()
})
</script>

<style scoped>
.ranking-page { max-width: 1000px; margin: 20px auto; padding: 0 20px; }
.ranking-item { margin-bottom: 24px; }
.village-info { display: flex; align-items: center; gap: 20px; margin-bottom: 12px; }
.rank { font-size: 1.5rem; font-weight: bold; color: #e67e22; }
.name { font-size: 1.2rem; font-weight: bold; }
.count { color: #666; }
.hot-comments { background: #f9f9f0; padding: 12px; border-radius: 12px; margin-top: 12px; }
.comment { border-bottom: 1px solid #e0e0d0; padding: 8px 0; }
.comment-user { font-weight: bold; }
.comment-footer { display: flex; gap: 12px; margin-top: 4px; font-size: 12px; color: #888; }
</style>