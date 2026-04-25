<template>
  <div class="province-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>{{ provinceName }}</h1>
      <div class="mode-tag">{{ isIndustryMode ? `${displayIndustryName}类产业示范村` : '全部村庄' }}</div>
    </div>

    <!-- 饼图 + TOP10 产品 - 仅在区域模式（村庄数量图）下显示 -->
    <template v-if="!isIndustryMode">
      <el-row :gutter="20" class="stats-row">
        <el-col :span="12">
          <el-card class="chart-card">
            <h3>产业占比（按村庄数量）</h3>
            <div ref="pieChartRef" class="pie-chart"></div>
          </el-card>
        </el-col>
        <el-col :span="12">
          <el-card class="top-card">
            <h3>热门产品 TOP10（按点赞数）</h3>
            <el-table :data="topProducts" size="small" style="width: 100%" v-if="topProducts.length">
              <el-table-column prop="product" label="产品名称" />
              <el-table-column prop="totalLikes" label="总点赞数" width="100" sortable />
              <el-table-column label="操作" width="100">
                <template #default="{ row }">
                  <el-button size="small" type="primary" link @click="showProductVillages(row.product)">
                    查看村庄
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <div v-else class="no-data">暂无产品点赞数据</div>
          </el-card>
        </el-col>
      </el-row>
    </template>

    <!-- 一级筛选：产业类型 (industry_type) 仅在非产业地图模式下显示 -->
    <div v-if="!isIndustryMode && industryTypeList.length" class="filter-row">
      <el-radio-group v-model="selectedIndustryType" size="small" @change="onIndustryTypeChange">
        <el-radio-button label="">全部产业</el-radio-button>
        <el-radio-button v-for="ind in industryTypeList" :key="ind" :label="ind">{{ ind }}</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 二级筛选：产品类别 (sub_category) -->
    <div v-if="subCategoryList.length" class="filter-row">
      <el-radio-group v-model="selectedSubCategory" size="small">
        <el-radio-button label="">全部产品</el-radio-button>
        <el-radio-button v-for="cat in subCategoryList" :key="cat" :label="cat">{{ cat }}</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 区域筛选（仅非产业模式） -->
    <div v-if="!isIndustryMode" class="filter-row">
      <el-cascader
        v-model="selectedArea"
        :options="areaOptions"
        :props="{ expandTrigger: 'hover', label: 'name', value: 'name', children: 'children', checkStrictly: true }"
        placeholder="请选择市/区/镇"
        clearable
        size="small"
        style="width: 260px;"
      />
    </div>

<!-- 搜索框 -->
<div class="search-row">
  <el-input
    v-model="searchKeyword"
    placeholder="搜索村庄或产品"
    clearable
    prefix-icon="Search"
    style="width: 300px; margin-bottom: 16px;"
  />
</div>

    <!-- 村庄卡片网格 -->
    <el-row :gutter="20">
      <el-col :span="12" v-for="v in paginatedVillages" :key="v.id" style="margin-bottom: 20px;">
        <el-card class="village-card" @click="goDetail(v.id)">
          <div class="card-content">
            <img src="https://picsum.photos/id/104/150/150" class="village-img" />
            <div class="info">
              <h3>{{ simplifyName(v.name) }}</h3>
              <p class="product">{{ v.product_name || '特色产品' }}</p>
              <p class="location">{{ v.city }} · {{ v.county || '' }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <div class="pagination-row">
  <el-pagination
    v-model:current-page="currentPage"
    v-model:page-size="pageSize"
    :page-sizes="[6, 12, 18, 24]"
    :total="searchedVillages.length"
    layout="total, sizes, prev, pager, next"
    @size-change="handleSizeChange"
    @current-change="handleCurrentChange"
  />
</div>

    <div v-if="filteredVillages.length === 0" class="empty">暂无村庄数据</div>

    <!-- 弹窗：展示某个产品下的所有村庄 -->
    <el-dialog v-model="dialogVisible" :title="`「${currentProduct}」相关村庄`" width="600px">
      <el-table :data="productVillages" style="width: 100%" v-if="productVillages.length">
        <el-table-column prop="name" label="村庄名称" />
        <el-table-column prop="product_name" label="产品名称" />
        <el-table-column prop="likeCount" label="点赞数" width="80" />
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="primary" link @click="goDetail(row.id)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div v-else class="no-data">该产品暂无关联村庄</div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as echarts from 'echarts'
import axios from 'axios'

const route = useRoute()
const router = useRouter()
const provinceName = route.params.name
const industryTypeFromMap = route.query.industry
const isIndustryMode = !!industryTypeFromMap

// 预设产业列表（用于“其他”判断）
const predefinedIndustries = ['茶', '果', '药', '渔', '蔬', '花', '畜', '粮']

const displayIndustryName = computed(() => {
  if (industryTypeFromMap === '其他') return '其他'
  return industryTypeFromMap || ''
})

const allVillages = ref([])

// 筛选状态
const selectedIndustryType = ref('')
const selectedSubCategory = ref('')
const selectedArea = ref([])

const areaOptions = ref([])

// 搜索与分页
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(6)

// 基于现有筛选结果再进行搜索过滤
const searchedVillages = computed(() => {
  let result = filteredVillages.value
  if (searchKeyword.value) {
    const kw = searchKeyword.value.toLowerCase()
    result = result.filter(v =>
      v.name?.toLowerCase().includes(kw) ||
      v.product_name?.toLowerCase().includes(kw)
    )
  }
  return result
})

// 分页后的村庄列表（替代模板中的 filteredVillages）
const paginatedVillages = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return searchedVillages.value.slice(start, end)
})

// 监听所有筛选条件变化，重置页码
watch([selectedIndustryType, selectedSubCategory, selectedArea, searchKeyword], () => {
  currentPage.value = 1
})

// 分页方法
const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}
const handleCurrentChange = (val) => {
  currentPage.value = val
}

// 饼图实例
let pieChart = null
const pieChartRef = ref(null)

// 产业占比数据
const industryStats = ref([])
// TOP10 产品（按点赞数）
const topProducts = ref([])

// 弹窗相关
const dialogVisible = ref(false)
const currentProduct = ref('')
const productVillages = ref([])

// 从村庄 name 中提取区、镇
const parseDistrictTown = (fullName) => {
  let district = null
  let town = null
  const districtMatch = fullName.match(/(.+?区)/)
  if (districtMatch) district = districtMatch[1]
  const townMatch = fullName.match(/(.+?镇)/)
  if (townMatch) town = townMatch[1]
  return { district, town }
}

// 简化村名
const simplifyName = (fullName) => {
  if (!fullName) return ''
  let name = fullName
  const districtIdx = name.indexOf('区')
  if (districtIdx !== -1) name = name.substring(districtIdx + 1)
  const townIdx = name.indexOf('镇')
  if (townIdx !== -1) name = name.substring(townIdx + 1)
  return name || fullName
}

// 构建区域筛选选项（城市 → 区 → 镇）
const buildAreaOptions = () => {
  const cityMap = new Map()
  allVillages.value.forEach(v => {
    const city = v.city || '未知'
    const { district, town } = parseDistrictTown(v.name)
    if (!cityMap.has(city)) cityMap.set(city, new Map())
    const districtMap = cityMap.get(city)
    if (district) {
      if (!districtMap.has(district)) districtMap.set(district, new Set())
      if (town) districtMap.get(district).add(town)
    } else if (town) {
      if (!districtMap.has('')) districtMap.set('', new Set())
      districtMap.get('').add(town)
    }
  })
  const options = []
  for (let [city, districtMap] of cityMap.entries()) {
    const cityNode = { name: city, children: [] }
    for (let [district, towns] of districtMap.entries()) {
      const districtNode = { name: district || '直接镇', children: [] }
      for (let town of towns) {
        districtNode.children.push({ name: town })
      }
      cityNode.children.push(districtNode)
    }
    options.push(cityNode)
  }
  return options
}

// 根据产业类型获取村庄列表（处理“其他”）
const getBaseVillagesByIndustry = (industry) => {
  if (industry === '其他') {
    return allVillages.value.filter(v => !predefinedIndustries.includes(v.industry_type))
  } else {
    return allVillages.value.filter(v => v.industry_type === industry)
  }
}

// 计算产业占比（基于该省所有村庄）
const computeIndustryStats = () => {
  const stats = new Map()
  allVillages.value.forEach(v => {
    let ind = v.industry_type || '其他'
    if (!predefinedIndustries.includes(ind)) ind = '其他'
    stats.set(ind, (stats.get(ind) || 0) + 1)
  })
  industryStats.value = Array.from(stats.entries()).map(([name, value]) => ({ name, value }))
  renderPieChart()
}

// 计算 TOP10 产品（按点赞数）
const computeTopProducts = () => {
  const productMap = new Map() // key: product_name, value: total likes
  allVillages.value.forEach(v => {
    const prod = v.product_name
    if (prod && prod !== 'NaN') {
      const likes = v.likeCount || 0
      productMap.set(prod, (productMap.get(prod) || 0) + likes)
    }
  })
  const sorted = Array.from(productMap.entries())
    .map(([product, totalLikes]) => ({ product, totalLikes }))
    .sort((a, b) => b.totalLikes - a.totalLikes)
    .slice(0, 10)
  topProducts.value = sorted
}

// 渲染饼图
const renderPieChart = () => {
  if (!pieChartRef.value) return
  if (pieChart) pieChart.dispose()
  pieChart = echarts.init(pieChartRef.value)

  const total = industryStats.value.reduce((sum, item) => sum + item.value, 0)

  const option = {
    tooltip: { trigger: 'item' },
    legend: { show: false },
    series: [{
      type: 'pie',
      radius: '55%',
      center: ['70%', '50%'],        // 关键：饼图水平右移（70% 处），垂直居中
      data: industryStats.value,
      label: {
        show: true,
        position: 'outside',
        formatter: (params) => {
          const percent = ((params.value / total) * 100).toFixed(1)
          return `${params.name} (${percent}%)`
        },
        lineHeight: 20,
        fontSize: 12,
        fontWeight: 'normal',
        color: '#333',
        lineLength: 20,
        lineLength2: 15,
        bleedMargin: 10
      },
      labelLine: {
        show: true,
        length: 20,
        length2: 15,
        smooth: false,
        lineStyle: { color: '#aaa', width: 1 }
      },
      avoidLabelOverlap: true,
      emphasis: { scale: true },
      itemStyle: {
        borderRadius: 8,
        borderColor: '#fff',
        borderWidth: 2
      }
    }]
  }
  pieChart.setOption(option)
}
// 加载该省所有村庄1
const loadVillages = async () => {
  try {
    const res = await axios.get(`/api/villages?province=${provinceName}`)
    allVillages.value = res.data
    if (!isIndustryMode) {
      computeIndustryStats()
      computeTopProducts()
      areaOptions.value = buildAreaOptions()
    }
  } catch (error) {
    console.error('加载村庄数据失败', error)
    allVillages.value = []
  }
}

// 显示某个产品下的所有村庄
const showProductVillages = (productName) => {
  currentProduct.value = productName
  productVillages.value = allVillages.value.filter(v => v.product_name === productName)
  dialogVisible.value = true
}

// 一级产业列表（该省实际存在的产业类型，将非预设产业统一显示为“其他”）
const industryTypeList = computed(() => {
  const types = new Set()
  allVillages.value.forEach(v => {
    let ind = v.industry_type || '其他'
    if (!predefinedIndustries.includes(ind)) ind = '其他'
    types.add(ind)
  })
  return Array.from(types).sort()
})

// 二级产品列表（根据当前选中的产业）
const subCategoryList = computed(() => {
  let base = null
  if (isIndustryMode) {
    base = getBaseVillagesByIndustry(industryTypeFromMap)
  } else if (selectedIndustryType.value) {
    base = getBaseVillagesByIndustry(selectedIndustryType.value)
  } else {
    return []
  }
  const cats = new Set()
  base.forEach(v => {
    if (v.sub_category && v.sub_category !== 'NaN') cats.add(v.sub_category)
  })
  return Array.from(cats).sort()
})

// 一级产业变化时重置二级筛选
const onIndustryTypeChange = () => {
  selectedSubCategory.value = ''
}

// 最终筛选后的村庄列表
const filteredVillages = computed(() => {
  let result = allVillages.value

  // 1. 产业地图入口：只显示该产业（处理“其他”）
  if (isIndustryMode && industryTypeFromMap) {
    result = getBaseVillagesByIndustry(industryTypeFromMap)
    if (selectedSubCategory.value) {
      result = result.filter(v => v.sub_category === selectedSubCategory.value)
    }
    return result
  }

  // 2. 非产业模式：应用一级产业、二级产品、区域筛选
  if (selectedIndustryType.value) {
    result = getBaseVillagesByIndustry(selectedIndustryType.value)
  }
  if (selectedSubCategory.value) {
    result = result.filter(v => v.sub_category === selectedSubCategory.value)
  }
  if (selectedArea.value.length) {
    const [selectedCity, selectedDistrict, selectedTown] = selectedArea.value
    result = result.filter(v => {
      if (v.city !== selectedCity) return false
      const { district, town } = parseDistrictTown(v.name)
      if (selectedTown) {
        return district === selectedDistrict && town === selectedTown
      } else if (selectedDistrict) {
        return district === selectedDistrict
      } else {
        return true
      }
    })
  }
  return result
})

const goDetail = (id) => router.push(`/village/${id}`)

onMounted(() => {
  loadVillages()
  window.addEventListener('resize', () => {
    pieChart?.resize()
  })
})

// 监听数据变化重新渲染饼图和TOP10（仅在区域模式）
watch(allVillages, () => {
  if (!isIndustryMode) {
    computeIndustryStats()
    computeTopProducts()
  }
})
</script>

<style scoped>
.province-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.header {
  display: flex;
  align-items: baseline;
  gap: 20px;
  flex-wrap: wrap;
  margin-bottom: 24px;
  border-left: 5px solid #e67e22;
  padding-left: 20px;
}
.header h1 {
  font-size: 1.8rem;
  font-weight: 600;
  color: #2b5e2b;
}
.mode-tag {
  background: #f0e7db;
  padding: 4px 12px;
  border-radius: 40px;
  font-size: 14px;
  color: #5a3e2b;
}

.stats-row {
  margin-bottom: 24px;
}
.pie-chart {
  width: 100%;
  height: 300px;
}
.top-card .no-data {
  text-align: center;
  padding: 40px 0;
  color: #999;
}

.filter-row {
  margin: 20px 0;
  text-align: center;
}

.village-card {
  cursor: pointer;
  transition: all 0.25s ease;
  border-radius: 24px;
  overflow: hidden;
  background: rgba(255, 255, 245, 0.8);
  backdrop-filter: blur(4px);
}
.village-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 20px 30px -12px rgba(43, 94, 43, 0.15);
}
.card-content {
  display: flex;
  gap: 16px;
  padding: 12px;
}
.village-img {
  width: 100px;
  height: 100px;
  object-fit: cover;
  border-radius: 16px;
}
.info h3 {
  margin: 0 0 5px;
  font-size: 1.2rem;
  color: #2b5e2b;
}
.product {
  color: #e67e22;
  font-weight: bold;
  margin: 5px 0;
}
.location {
  font-size: 12px;
  color: #888;
}
.empty {
  text-align: center;
  padding: 50px;
  color: #999;
}

@media (max-width: 768px) {
  .header h1 { font-size: 1.4rem; }
  .village-img { width: 70px; height: 70px; }
  .pie-chart { height: 200px; }
}
</style>