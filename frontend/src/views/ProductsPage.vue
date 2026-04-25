<template>
  <div class="products-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>产品浏览</h1>
    </div>

    <!-- 一级产业筛选 -->
    <div class="filter-row">
      <el-radio-group v-model="selectedIndustry" size="small" @change="onIndustryChange">
        <el-radio-button label="">全部产业</el-radio-button>
        <el-radio-button v-for="ind in industryList" :key="ind" :label="ind">{{ ind }}</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 二级产品筛选（动态） -->
    <div v-if="subCategoryList.length" class="filter-row">
      <el-radio-group v-model="selectedSubCategory" size="small">
        <el-radio-button label="">全部产品</el-radio-button>
        <el-radio-button v-for="cat in subCategoryList" :key="cat" :label="cat">{{ cat }}</el-radio-button>
      </el-radio-group>
    </div>

    <!-- 地区筛选：省 → 市 → 区/镇 级联 -->
    <div class="filter-row">
      <el-cascader
        v-model="selectedRegion"
        :options="regionOptions"
        :props="{ expandTrigger: 'hover', label: 'name', value: 'name', children: 'children', checkStrictly: true }"
        placeholder="请选择省/市/区/镇"
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
              <p class="location">{{ v.province }} · {{ v.city }} · {{ v.county || '' }}</p>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <!-- 分页组件 -->
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

    <div v-if="searchedVillages.length === 0" class="empty">暂无村庄数据</div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

const router = useRouter()

// 预设产业列表（用于“其他”归类）
const predefinedIndustries = ['茶', '果', '药', '渔', '蔬', '花', '畜', '粮']

const allVillages = ref([])
const usingMockData = ref(false)

// 筛选状态
const selectedIndustry = ref('')
const selectedSubCategory = ref('')
const selectedRegion = ref([])
const regionOptions = ref([])

// 搜索和分页
const searchKeyword = ref('')
const currentPage = ref(1)
const pageSize = ref(6)

// 从村庄 name 中提取区、镇
const parseDistrictTown = (fullName) => {
  let district = null, town = null
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

// 构建全国地区级联选项（省 → 市 → 区/镇）
const buildRegionOptions = () => {
  const provinceMap = new Map()
  allVillages.value.forEach(v => {
    const province = v.province || '未知'
    const city = v.city || '未知'
    const { district, town } = parseDistrictTown(v.name)
    if (!provinceMap.has(province)) provinceMap.set(province, new Map())
    const cityMap = provinceMap.get(province)
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
  for (let [province, cityMap] of provinceMap.entries()) {
    const provinceNode = { name: province, children: [] }
    for (let [city, districtMap] of cityMap.entries()) {
      const cityNode = { name: city, children: [] }
      for (let [district, towns] of districtMap.entries()) {
        const districtNode = { name: district || '直接镇', children: [] }
        for (let town of towns) {
          districtNode.children.push({ name: town })
        }
        cityNode.children.push(districtNode)
      }
      provinceNode.children.push(cityNode)
    }
    options.push(provinceNode)
  }
  return options
}

// 加载全国村庄数据
const loadVillages = async () => {
  try {
    const res = await axios.get('/api/villages')
    allVillages.value = res.data
    usingMockData.value = false
    regionOptions.value = buildRegionOptions()
  } catch (error) {
    console.error('加载村庄数据失败，使用模拟数据', error)
    usingMockData.value = true
    allVillages.value = []
    regionOptions.value = []
  }
}

// 一级产业列表（基于全国数据，将非预设产业归为“其他”）
const industryList = computed(() => {
  const types = new Set()
  allVillages.value.forEach(v => {
    let ind = v.industry_type || '其他'
    if (!predefinedIndustries.includes(ind)) ind = '其他'
    types.add(ind)
  })
  return Array.from(types).sort()
})

// 根据选中的一级产业获取基础村庄列表（处理“其他”）
const getBaseVillagesByIndustry = (industry) => {
  if (industry === '其他') {
    return allVillages.value.filter(v => !predefinedIndustries.includes(v.industry_type))
  } else {
    return allVillages.value.filter(v => v.industry_type === industry)
  }
}

// 二级产品列表（基于选中的一级产业）
const subCategoryList = computed(() => {
  if (!selectedIndustry.value) return []
  const base = getBaseVillagesByIndustry(selectedIndustry.value)
  const cats = new Set()
  base.forEach(v => {
    if (v.sub_category && v.sub_category !== 'NaN') cats.add(v.sub_category)
  })
  return Array.from(cats).sort()
})

// 一级产业变化时重置二级筛选
const onIndustryChange = () => {
  selectedSubCategory.value = ''
}

// 地区筛选辅助：根据级联值筛选村庄
const filterByRegion = (villages, regionPath) => {
  if (!regionPath.length) return villages
  const [selectedProvince, selectedCity, selectedDistrict, selectedTown] = regionPath
  return villages.filter(v => {
    if (v.province !== selectedProvince) return false
    if (selectedCity && v.city !== selectedCity) return false
    if (selectedDistrict) {
      const { district } = parseDistrictTown(v.name)
      if (district !== selectedDistrict) return false
    }
    if (selectedTown) {
      const { town } = parseDistrictTown(v.name)
      if (town !== selectedTown) return false
    }
    return true
  })
}

// 基础筛选（产业、产品、地区）后的村庄
const filteredVillages = computed(() => {
  let result = allVillages.value
  if (selectedIndustry.value) {
    result = getBaseVillagesByIndustry(selectedIndustry.value)
  }
  if (selectedSubCategory.value) {
    result = result.filter(v => v.sub_category === selectedSubCategory.value)
  }
  if (selectedRegion.value.length) {
    result = filterByRegion(result, selectedRegion.value)
  }
  return result
})

// 搜索过滤后的村庄
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

// 分页后的村庄
const paginatedVillages = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return searchedVillages.value.slice(start, end)
})

// 监听筛选、搜索变化，重置页码
watch([selectedIndustry, selectedSubCategory, selectedRegion, searchKeyword], () => {
  currentPage.value = 1
})

const handleSizeChange = (val) => {
  pageSize.value = val
  currentPage.value = 1
}
const handleCurrentChange = (val) => {
  currentPage.value = val
}

const goDetail = (id) => router.push(`/village/${id}`)

onMounted(() => {
  loadVillages()
})
</script>

<style scoped>
/* 原有样式保持不变，新增如下 */
.search-row {
  text-align: center;
  margin-bottom: 12px;
}
.pagination-row {
  display: flex;
  justify-content: center;
  margin-top: 20px;
}
/* 其余原有样式保持 */
</style>