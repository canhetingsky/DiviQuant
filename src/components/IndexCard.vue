<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { formatYield, formatDate, getYieldClass } from '../utils/data.js'

const props = defineProps({
  index: {
    type: Object,
    required: true,
  },
})

const router = useRouter()

const navigateToDetail = () => {
  router.push(`/index/${props.index.index_code}`)
}

const yieldClass = computed(() => getYieldClass(props.index.avg_yield))
</script>

<template>
  <div 
    class="card p-6 cursor-pointer group" 
    @click="navigateToDetail"
  >
    <div class="flex items-start justify-between mb-4">
      <div>
        <h3 class="text-lg font-display font-semibold text-slate-800 group-hover:text-blue-600 transition-colors">
          {{ index.index_name }}
        </h3>
        <p class="text-sm text-slate-500 font-mono">{{ index.index_code }}</p>
      </div>
      <span class="px-2 py-1 text-xs font-medium bg-slate-100 text-slate-600 rounded">
        {{ index.stock_count }}只
      </span>
    </div>
    
    <div class="space-y-3">
      <div class="flex justify-between items-center">
        <span class="text-sm text-slate-500">平均股息率</span>
        <span :class="yieldClass" class="text-xl font-semibold">
          {{ formatYield(index.avg_yield) }}
        </span>
      </div>
      
      <div class="grid grid-cols-2 gap-3 pt-3 border-t border-slate-100">
        <div>
          <p class="text-xs text-slate-400">中位数</p>
          <p class="text-sm font-medium text-slate-700">{{ formatYield(index.median_yield) }}</p>
        </div>
        <div>
          <p class="text-xs text-slate-400">最高</p>
          <p class="text-sm font-medium text-emerald-600">{{ formatYield(index.max_yield) }}</p>
        </div>
      </div>
    </div>
    
    <div class="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
      <span class="text-xs text-slate-400">更新于 {{ formatDate(index.updated_at) }}</span>
      <svg class="w-5 h-5 text-slate-400 group-hover:text-blue-500 group-hover:translate-x-1 transition-all" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7" />
      </svg>
    </div>
  </div>
</template>