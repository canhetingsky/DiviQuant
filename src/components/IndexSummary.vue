<script setup>
import { formatYield, formatDate } from '../utils/data.js'

defineProps({
  info: {
    type: Object,
    required: true,
  },
})

const stats = [
  { label: '成分股数量', key: 'stock_count', format: v => v },
  { label: '平均股息率', key: 'avg_yield', format: formatYield },
  { label: '中位数', key: 'median_yield', format: formatYield },
  { label: '最高股息率', key: 'max_yield', format: formatYield },
  { label: '最低股息率', key: 'min_yield', format: formatYield },
]
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
    <div class="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
      <div>
        <h1 class="text-2xl font-display font-bold text-slate-800">{{ info.index_name }}</h1>
        <p class="text-sm text-slate-500 font-mono">{{ info.index_code }}</p>
      </div>
      <p class="text-sm text-slate-400">更新于 {{ formatDate(info.updated_at) }}</p>
    </div>
    
    <div class="grid grid-cols-2 sm:grid-cols-5 gap-4">
      <div 
        v-for="stat in stats" 
        :key="stat.key"
        class="text-center p-3 bg-slate-50 rounded-lg"
      >
        <p class="text-xs text-slate-400 mb-1">{{ stat.label }}</p>
        <p class="text-lg font-semibold text-slate-800">
          {{ stat.format(info[stat.key]) }}
        </p>
      </div>
    </div>
  </div>
</template>