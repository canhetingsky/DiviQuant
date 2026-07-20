<script setup>
import { ref, onMounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { fetchIndexDetail, fetchStockDividendSummary, formatPrice } from '../utils/data.js'
import IndexSummary from '../components/IndexSummary.vue'
import YieldChart from '../components/YieldChart.vue'
import StockTable from '../components/StockTable.vue'
import IndexStockDetailModal from '../components/IndexStockDetailModal.vue'

const route = useRoute()
const router = useRouter()

const loading = ref(true)
const error = ref(null)
const data = ref(null)
const dividendSummary = ref(null)
const selectedStock = ref(null)

const indexCode = computed(() => route.params.indexCode)
const filter = computed(() => route.query.filter || 'all')

const filteredStocks = computed(() => {
  if (!data.value?.stocks) return []
  const stocks = data.value.stocks
  if (filter.value === 'all') return stocks
  return stocks.filter(s => {
    const y = s.ttm_yield || 0
    if (filter.value === 'high') return y >= 5
    if (filter.value === 'mid') return y >= 3 && y < 5
    if (filter.value === 'low') return y < 3
    return true
  })
})

onMounted(async () => {
  try {
    const filename = `index_${indexCode.value}_dividend_yield.json`
    const [indexData, summaryData] = await Promise.all([
      fetchIndexDetail(filename),
      fetchStockDividendSummary()
    ])
    data.value = indexData
    dividendSummary.value = summaryData
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

watch(filter, () => {
  window.scrollTo({ top: 400, behavior: 'smooth' })
})

const goBack = () => {
  router.push('/')
}

const getStockSummary = (symbol) => {
  if (!dividendSummary.value?.top_dividend_stocks) return null
  return dividendSummary.value.top_dividend_stocks.find(s => s.symbol === symbol)
}

const handleStockSelect = (stock) => {
  const summary = getStockSummary(stock.symbol)
  const indexInfo = data.value?.index_info || {}
  const stocks = data.value?.stocks || []
  const rank = stocks.findIndex(s => s.symbol === stock.symbol) + 1
  
  selectedStock.value = {
    ...stock,
    total_dividend: summary?.total_dividend || 0,
    avg_annual: summary?.avg_annual || 0,
    consecutive_years: summary?.consecutive_years || 0,
    rank,
    index_name: indexInfo.index_name || '',
    index_code: indexInfo.index_code || '',
    index_avg_yield: indexInfo.avg_yield || 0
  }
}

const closeModal = () => {
  selectedStock.value = null
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <button 
      @click="goBack"
      class="flex items-center gap-2 text-slate-600 hover:text-slate-800 mb-6 transition-colors"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      <span>返回首页</span>
    </button>
    
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-800"></div>
    </div>
    
    <div v-else-if="error" class="text-center py-20">
      <p class="text-red-500 mb-4">{{ error }}</p>
      <button @click="goBack" class="btn btn-primary">返回首页</button>
    </div>
    
    <div v-else-if="data" class="space-y-6">
      <IndexSummary :info="data.index_info" />
      
      <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <YieldChart :stocks="data.stocks" />
        
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <h2 class="text-lg font-semibold text-slate-800 mb-4">快速筛选</h2>
          <div class="space-y-3">
            <router-link 
              :to="`/index/${indexCode}?filter=high`"
              :class="[
                'block p-3 rounded-lg border transition-colors',
                filter === 'high' ? 'border-emerald-500 bg-emerald-50' : 'border-slate-200 hover:border-emerald-400 hover:bg-emerald-50'
              ]"
            >
              <div class="flex items-center justify-between">
                <span class="font-medium text-slate-700">高股息 (&gt;5%)</span>
                <span class="text-emerald-600 font-semibold">
                  {{ data.stocks.filter(s => (s.ttm_yield || 0) >= 5).length }}只
                </span>
              </div>
            </router-link>
            
            <router-link 
              :to="`/index/${indexCode}?filter=mid`"
              :class="[
                'block p-3 rounded-lg border transition-colors',
                filter === 'mid' ? 'border-slate-500 bg-slate-50' : 'border-slate-200 hover:border-slate-400 hover:bg-slate-50'
              ]"
            >
              <div class="flex items-center justify-between">
                <span class="font-medium text-slate-700">中等股息 (3%-5%)</span>
                <span class="text-slate-600 font-semibold">
                  {{ data.stocks.filter(s => { const y = s.ttm_yield || 0; return y >= 3 && y < 5; }).length }}只
                </span>
              </div>
            </router-link>
            
            <router-link 
              :to="`/index/${indexCode}?filter=low`"
              :class="[
                'block p-3 rounded-lg border transition-colors',
                filter === 'low' ? 'border-rose-500 bg-rose-50' : 'border-slate-200 hover:border-rose-400 hover:bg-rose-50'
              ]"
            >
              <div class="flex items-center justify-between">
                <span class="font-medium text-slate-700">低股息 (&lt;3%)</span>
                <span class="text-rose-600 font-semibold">
                  {{ data.stocks.filter(s => (s.ttm_yield || 0) < 3).length }}只
                </span>
              </div>
            </router-link>

            <router-link 
              v-if="filter !== 'all'"
              :to="`/index/${indexCode}`"
              class="block p-3 rounded-lg border border-slate-200 text-center text-slate-500 hover:text-slate-700"
            >
              显示全部
            </router-link>
          </div>
        </div>
      </div>
      
      <StockTable :stocks="filteredStocks" @select="handleStockSelect" />
    </div>

    <IndexStockDetailModal 
      v-if="selectedStock" 
      :stock="selectedStock" 
      @close="closeModal" 
    />
  </div>
</template>