<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const props = defineProps({
  stocks: {
    type: Array,
    required: true,
  },
})

const chartRef = ref(null)
let chart = null

const initChart = () => {
  if (!chartRef.value) return
  
  chart = echarts.init(chartRef.value)
  
  const top10 = [...props.stocks]
    .sort((a, b) => b.ttm_yield - a.ttm_yield)
    .slice(0, 10)
  
  const names = top10.map(s => s.stock_name.length > 6 ? s.stock_name.slice(0, 6) + '...' : s.stock_name)
  const yields = top10.map(s => s.ttm_yield)
  
  const option = {
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      top: '10%',
      containLabel: true,
    },
    xAxis: {
      type: 'value',
      axisLabel: {
        formatter: '{value}%',
        color: '#64748b',
        fontSize: 11,
      },
      splitLine: {
        lineStyle: {
          color: '#e2e8f0',
          type: 'dashed',
        },
      },
    },
    yAxis: {
      type: 'category',
      data: names.reverse(),
      axisLabel: {
        color: '#475569',
        fontSize: 11,
        width: 80,
        overflow: 'truncate',
      },
    },
    series: [
      {
        name: '股息率',
        type: 'bar',
        data: yields.reverse(),
        barWidth: '60%',
        itemStyle: {
          borderRadius: [0, 4, 4, 0],
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#10B981' },
            { offset: 1, color: '#34D399' },
          ]),
        },
        label: {
          show: true,
          position: 'right',
          formatter: '{c}%',
          color: '#059669',
          fontSize: 11,
          fontWeight: 500,
        },
      },
    ],
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow',
      },
    },
  }
  
  chart.setOption(option)
}

onMounted(() => {
  initChart()
})

watch(() => props.stocks, () => {
  if (chart) {
    chart.dispose()
  }
  initChart()
}, { deep: true })
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
    <h2 class="text-lg font-semibold text-slate-800 mb-4">Top 10 高股息成分股</h2>
    <div ref="chartRef" class="w-full h-72"></div>
  </div>
</template>