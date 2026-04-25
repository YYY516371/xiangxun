<template>
  <div class="home">
    <div class="hero">
      <img src="https://picsum.photos/id/15/1200/400" alt="乡村封面" class="hero-img" />
      <div class="hero-text">
        <h1>一村一品 · 特色乡村数字地图</h1>
        <p>探索全国示范村，发现乡土好物</p>
      </div>
    </div>

    <!-- 产业选择器（仅产业分布图显示） -->
    <div v-if="activeMap === 'industry'" class="industry-selector">
      <el-button-group>
        <el-button
          v-for="ind in industries"
          :key="ind"
          :type="selectedIndustry === ind ? 'primary' : ''"
          @click="selectedIndustry = ind"
        >
          {{ ind }}
        </el-button>
      </el-button-group>
    </div>

    <!-- 地图切换按钮 -->
    <div class="map-switch">
      <el-button :type="activeMap === 'industry' ? 'primary' : ''" @click="activeMap = 'industry'">
        产业分布图
      </el-button>
      <el-button :type="activeMap === 'count' ? 'primary' : ''" @click="activeMap = 'count'">
        村庄数量图
      </el-button>
    </div>

    <!-- 地图容器（相对定位，用于放置图例） -->
    <div class="map-wrapper">
      <div id="mapContainer" class="map-container"></div>

      <!-- 动态图例 -->
      <div class="map-legend" v-if="activeMap === 'industry'">
        <div class="legend-title">产业数量</div>
        <div class="legend-gradient" style="background: linear-gradient(to right, #f9f7c1, #c7e9c0, #74c476, #31a354, #238b45, #005a32)"></div>
        <div class="legend-labels">
          <span>少</span><span>多</span>
        </div>
      </div>
      <div class="map-legend" v-else>
        <div class="legend-title">村庄数量</div>
        <div class="legend-gradient" style="background: linear-gradient(to right, #fff7ec, #fee8c8, #fdd49e, #fdbb84, #fc8d59, #d7301f)"></div>
        <div class="legend-labels">
          <span>少</span><span>多</span>
        </div>
      </div>
    </div>

    <!-- 审图号标注 -->
    <div class="map-attribution">
      地图数据：天地图 GS(2024)0650 号 | 数据仅供参考
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'

const router = useRouter()
const activeMap = ref('industry')
const selectedIndustry = ref('茶')
const industries = ['茶', '果', '药', '渔', '蔬', '花', '畜', '粮', '其他']

let map = null
let currentGeoJsonLayer = null

const provinceIndustryStats = ref([])   // [{ province: '北京市', 茶:2, ... }]
const provinceCountStats = ref([])      // [{ province: '北京市', count: 46 }]
const predefinedIndustries = ['茶', '果', '药', '渔', '蔬', '花', '畜', '粮']

// ==================== 天地图配置 ====================
// 请替换为你的天地图 API Key
const TDT_KEY = '0a47fcf36bd777049f0bce6c8ea8356e'   // ← 必须替换为真实 Key
const tileLayer = L.tileLayer(
  `https://t{s}.tianditu.gov.cn/DataServer?T=vec_w&x={x}&y={y}&l={z}&tk=${TDT_KEY}`,
  {
    subdomains: ['0', '1', '2', '3', '4', '5', '6', '7'],
    attribution: '天地图',
  }
)

// ==================== 颜色映射（大师级配色） ====================
const getIndustryColor = (value, maxValue) => {
  if (maxValue === 0) return '#e0e0e0'
  const ratio = value / maxValue
  if (ratio < 0.1) return '#f9f7c1'   // 嫩黄
  if (ratio < 0.3) return '#c7e9c0'   // 浅草绿
  if (ratio < 0.5) return '#74c476'   // 翠绿
  if (ratio < 0.7) return '#31a354'   // 森林绿
  if (ratio < 0.9) return '#238b45'   // 深苔绿
  return '#005a32'                     // 墨绿
}

const getCountColor = (value, maxValue) => {
  if (maxValue === 0) return '#f0f0f0'
  const ratio = value / maxValue
  if (ratio < 0.1) return '#fff7ec'   // 浅米
  if (ratio < 0.3) return '#fee8c8'   // 淡橙
  if (ratio < 0.5) return '#fdd49e'   // 杏色
  if (ratio < 0.7) return '#fdbb84'   // 橘黄
  if (ratio < 0.9) return '#fc8d59'   // 橙红
  return '#d7301f'                     // 深红
}

// ==================== 数据加载与聚合 ====================
const loadStatistics = async () => {
  try {
    const res = await axios.get('/api/villages')
    const allVillages = res.data
    console.log(`成功加载 ${allVillages.length} 条村庄数据`)

    // 1. 各省各产业数量
    const industryMap = new Map()
    for (const v of allVillages) {
      const province = v.province
      if (!province) continue
      if (!industryMap.has(province)) {
        industryMap.set(province, {
          province,
          茶: 0, 果: 0, 药: 0, 渔: 0, 蔬: 0, 花: 0, 畜: 0, 粮: 0, 其他: 0,
        })
      }
      const stats = industryMap.get(province)
      let ind = v.industry_type
      if (!ind || !predefinedIndustries.includes(ind)) {
        stats.其他 += 1
      } else {
        stats[ind] += 1
      }
    }
    provinceIndustryStats.value = Array.from(industryMap.values())

    // 2. 各省村庄总数
    const countMap = new Map()
    for (const v of allVillages) {
      const province = v.province
      if (province) {
        countMap.set(province, (countMap.get(province) || 0) + 1)
      }
    }
    provinceCountStats.value = Array.from(countMap.entries()).map(([province, count]) => ({
      province,
      count,
    }))

    refreshMapLayer()
  } catch (error) {
    console.error('加载村庄数据失败，使用模拟数据', error)
    // 模拟数据（示例）
    provinceIndustryStats.value = [
      { province: '北京市', 茶: 2, 果: 15, 药: 1, 渔: 0, 蔬: 8, 花: 3, 畜: 1, 粮: 2, 其他: 0 },
      { province: '天津市', 茶: 0, 果: 12, 药: 2, 渔: 1, 蔬: 10, 花: 2, 畜: 2, 粮: 1, 其他: 0 },
      { province: '上海市', 茶: 1, 果: 8, 药: 0, 渔: 2, 蔬: 5, 花: 4, 畜: 0, 粮: 0, 其他: 0 },
    ]
    provinceCountStats.value = provinceIndustryStats.value.map(p => ({
      province: p.province,
      count: Object.values(p).reduce((sum, val) => sum + (typeof val === 'number' ? val : 0), 0),
    }))
    refreshMapLayer()
  }
}

// ==================== 获取当前地图模式下的数值 ====================
const getCurrentProvinceValues = () => {
  if (activeMap.value === 'industry') {
    return provinceIndustryStats.value.map(item => ({
      name: item.province,
      value: item[selectedIndustry.value] || 0,
    }))
  } else {
    return provinceCountStats.value.map(item => ({
      name: item.province,
      value: item.count,
    }))
  }
}

// ==================== 刷新地图叠加图层 ====================
const refreshMapLayer = async () => {
  if (!map) return
  if (currentGeoJsonLayer) map.removeLayer(currentGeoJsonLayer)

  const provinceValues = getCurrentProvinceValues()
  const valueMap = new Map()
  let maxValue = 0
  for (const p of provinceValues) {
    valueMap.set(p.name, p.value)
    if (p.value > maxValue) maxValue = p.value
  }

  try {
    const geoJsonData = await fetch('/china.geojson').then(res => res.json())
    currentGeoJsonLayer = L.geoJSON(geoJsonData, {
      style: feature => {
        const provinceName = feature.properties.name
        const value = valueMap.get(provinceName) || 0
        const fillColor = activeMap.value === 'industry'
          ? getIndustryColor(value, maxValue)
          : getCountColor(value, maxValue)
        return {
          color: '#2c3e2f',
          weight: 0.8,
          fillColor: fillColor,
          fillOpacity: 0.65,
        }
      },
      onEachFeature: (feature, layer) => {
        const provinceName = feature.properties.name
        const value = valueMap.get(provinceName) || 0
        const label = activeMap.value === 'industry'
          ? `${provinceName}<br/>${selectedIndustry.value}产业数量：${value}`
          : `${provinceName}<br/>示范村总数：${value}`
        layer.bindTooltip(label, { sticky: true, direction: 'right' ,offset:[15,-10]})

        // 鼠标悬浮高亮
        layer.on('mouseover', () => {
          layer.setStyle({
            weight: 2.5,
            color: '#e67e22',
            fillOpacity: 0.85,
          })
        })
        layer.on('mouseout', () => {
          const fillColor = activeMap.value === 'industry'
            ? getIndustryColor(value, maxValue)
            : getCountColor(value, maxValue)
          layer.setStyle({
            weight: 0.8,
            color: '#2c3e2f',
            fillColor: fillColor,
            fillOpacity: 0.65,
          })
        })

        // 点击跳转
        layer.on('click', () => {
          const query = activeMap.value === 'industry' ? `?industry=${selectedIndustry.value}` : '?mode=region'
          router.push(`/province/${provinceName}${query}`)
        })
      },
    }).addTo(map)
  } catch (err) {
    console.error('加载 GeoJSON 失败', err)
  }
}

// ==================== 初始化地图（禁用缩放、限制中国边界） ====================
const initMap = () => {
  const container = document.getElementById('mapContainer')
  if (!container) return

  // 中国边界框
  const chinaBounds = [
    [3.0, 73.0],
    [55.0, 135.0],
  ]

  map = L.map('mapContainer', {
    zoomControl: false,
    scrollWheelZoom: false,
    doubleClickZoom: false,
    touchZoom: false,
    boxZoom: false,
    keyboard: false,
  }).setView([34.0, 106.0], 4)

  map.setMaxBounds(chinaBounds)
  map.on('drag', () => {
    map.panInsideBounds(chinaBounds, { animate: false })
  })

  tileLayer.addTo(map)
  refreshMapLayer()
}

// ==================== 生命周期 ====================
onMounted(async () => {
  await loadStatistics()
  initMap()
  window.addEventListener('resize', () => {
    if (map) map.invalidateSize()
  })
})

onUnmounted(() => {
  if (map) {
    map.remove()
    map = null
  }
  window.removeEventListener('resize', () => {})
})

watch([activeMap, selectedIndustry], () => {
  refreshMapLayer()
})
</script>

<style scoped>
.home {
  padding: 0;
  position: relative;
}

.hero {
  position: relative;
  width: 100%;
  height: 300px;
  overflow: hidden;
  border-radius: 0 0 32px 32px;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.1);
}
.hero-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.hero-text {
  position: absolute;
  bottom: 30px;
  left: 30px;
  color: white;
  text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
  background: rgba(0, 0, 0, 0.3);
  backdrop-filter: blur(4px);
  padding: 12px 24px;
  border-radius: 60px;
}

.industry-selector {
  display: flex;
  justify-content: center;
  margin: 24px 0 16px;
}
.map-switch {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin: 8px 0 16px;
}

.map-wrapper {
  position: relative;
}

.map-container {
  width: 100%;
  height: 600px;
  border-radius: 32px;
  overflow: hidden;
  box-shadow: 0 15px 35px -12px rgba(0, 0, 0, 0.2), inset 0 1px 0 rgba(255, 255, 255, 0.2);
  z-index: 1;
}

/* 图例样式 */
.map-legend {
  position: absolute;
  bottom: 20px;
  right: 20px;
  background: rgba(255, 255, 245, 0.9);
  backdrop-filter: blur(8px);
  padding: 10px 14px;
  border-radius: 16px;
  font-size: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  pointer-events: none;
  font-family: 'Segoe UI', 'Roboto', sans-serif;
  border: 1px solid rgba(219, 203, 184, 0.5);
}
.legend-title {
  font-weight: 600;
  margin-bottom: 6px;
  color: #2b5e2b;
  font-size: 13px;
}
.legend-gradient {
  width: 180px;
  height: 12px;
  border-radius: 6px;
  margin: 6px 0;
}
.legend-labels {
  display: flex;
  justify-content: space-between;
  color: #5a5a4a;
  font-size: 11px;
}

.map-attribution {
  text-align: center;
  font-size: 12px;
  color: #888;
  margin-top: 8px;
}

@media (max-width: 768px) {
  .hero {
    height: 200px;
  }
  .map-container {
    height: 400px;
  }
  .map-legend {
    bottom: 10px;
    right: 10px;
    padding: 6px 10px;
  }
  .legend-gradient {
    width: 130px;
  }
}
</style>