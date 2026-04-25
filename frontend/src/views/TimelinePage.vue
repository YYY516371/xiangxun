<template>
  <div class="timeline-page">
    <div class="header">
      <el-button @click="$router.back()" type="primary" plain>← 返回</el-button>
      <h1>时序演进地图</h1>
    </div>

    <div class="year-slider">
      <span>年份：</span>
      <el-slider v-model="year" :min="2011" :max="2024" :step="1" show-stops />
      <span class="year-value">{{ year }} 年</span>
    </div>

    <div ref="mapChart" class="map-container"></div>
    <div class="legend">
      <span class="dot"></span> 该年入选的示范村
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const year = ref(2011)
let chart = null

// 模拟村庄数据（含经纬度和入选年份）
const mockVillages = [
  { name: '黄杜村', year: 2011, lng: 119.6, lat: 30.6 },
  { name: '鲁家村', year: 2015, lng: 119.7, lat: 30.6 },
  { name: '顾渚村', year: 2013, lng: 119.8, lat: 31.0 },
  { name: '东坡村', year: 2018, lng: 103.8, lat: 30.0 },
  { name: '石榴村', year: 2020, lng: 117.5, lat: 34.8 }
]

// 加载地图数据（使用 ECharts 自带地图）
const loadMap = () => {
  if (chart) {
    chart.dispose()
  }
  const dom = document.querySelector('.map-container')
  chart = echarts.init(dom)
  
  // 获取当前年份的村庄
  const points = mockVillages
    .filter(v => v.year === year.value)
    .map(v => ({ name: v.name, value: [v.lng, v.lat] }))

  const option = {
    title: {
      text: `${year.value}年入选村庄分布`,
      left: 'center'
    },
    tooltip: {
      trigger: 'item',
      formatter: '{b}'
    },
    series: [
      {
        type: 'scatter',
        coordinateSystem: 'geo',
        data: points.map(p => p.value),
        symbolSize: 12,
        itemStyle: { color: '#ff5722', borderColor: '#fff', borderWidth: 2 },
        label: {
          show: true,
          formatter: (params) => {
            const idx = params.dataIndex
            return points[idx]?.name || ''
          },
          position: 'right',
          offset: [5, 0]
        }
      },
      {
        type: 'map',
        map: 'china',
        roam: true,
        zoom: 1.2,
        itemStyle: {
          borderColor: '#ccc',
          areaColor: '#e0f3f8'
        },
        emphasis: { label: { show: true } }
      }
    ]
  }
  chart.setOption(option)
}

onMounted(() => {
  // 注册中国地图（ECharts 5+ 需要引入地图数据，这里简化使用内置）
  // 注意：ECharts 从 5.0 开始不再内置地图，需要额外注册。为了简化，可以使用 CDN 地图注册。
  // 如果报错“map china not exists”，请按以下方式注册：
  // 方案A：安装 echarts-map 包（较复杂），方案B：使用 geoJson 注册（推荐）
  // 为了快速演示，这里给出注册代码，你需要先安装 geojson 或使用在线资源。
  // 简便方法：直接使用 ECharts 官方示例中的地图注册代码。
  // 为了让你不卡住，我提供一个简化版：只显示散点图，不显示底图？
  // 更好的方式：使用百度地图或高德地图，但需要额外申请key。
  // 这里采用最稳妥的方式：安装 echarts 和 地图数据。
  // 请先运行 npm install echarts --save，然后按下面的代码注册。
  
  // 注册中国地图（使用 geo 资源）
  fetch('https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json')
    .then(response => response.json())
    .then(chinaJson => {
      echarts.registerMap('china', chinaJson)
      loadMap()
    })
    .catch(() => {
      // 如果网络失败，则使用简单提示
      const dom = document.querySelector('.map-container')
      dom.innerHTML = '<div style="text-align:center;padding:50px;">地图加载失败，请检查网络或使用代理</div>'
    })
})

watch(year, () => {
  if (chart) {
    const points = mockVillages
      .filter(v => v.year === year.value)
      .map(v => ({ name: v.name, value: [v.lng, v.lat] }))
    chart.setOption({
      series: [
        {
          data: points.map(p => p.value)
        }
      ]
    })
  }
})
</script>

<style scoped>
.timeline-page {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}
.header {
  margin-bottom: 20px;
}
.year-slider {
  display: flex;
  align-items: center;
  gap: 20px;
  margin-bottom: 20px;
  padding: 0 20px;
}
.year-slider .el-slider {
  flex: 1;
}
.year-value {
  font-weight: bold;
  font-size: 18px;
}
.map-container {
  width: 100%;
  height: 500px;
  background: #f5f5f5;
  border-radius: 12px;
}
.legend {
  margin-top: 10px;
  text-align: center;
  font-size: 12px;
  color: #666;
}
.legend .dot {
  display: inline-block;
  width: 12px;
  height: 12px;
  background-color: #ff5722;
  border-radius: 50%;
  margin-right: 5px;
}
</style>