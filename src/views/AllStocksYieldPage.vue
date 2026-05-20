<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchAllStocksYield, formatYield, formatPrice } from '../utils/data.js'

const router = useRouter()

const data = ref(null)
const loading = ref(true)
const error = ref(null)
const searchQuery = ref('')
const sortBy = ref('ttm_yield')
const sortOrder = ref('desc')
const yieldFilter = ref('all')
const currentPage = ref(1)
const pageSize = ref(100)

const sortOptions = [
  { value: 'ttm_yield', label: '股息率' },
  { value: 'ttm_dividend', label: 'TTM分红' },
  { value: 'current_price', label: '当前价格' },
  { value: 'symbol', label: '股票代码' },
]

const yieldFilterOptions = [
  { value: 'all', label: '全部股票' },
  { value: 'high', label: '高股息(≥5%)' },
  { value: 'mid', label: '中股息(3-5%)' },
  { value: 'low', label: '低股息(1-3%)' },
  { value: 'none', label: '无股息(0%)' },
]

onMounted(async () => {
  try {
    data.value = await fetchAllStocksYield()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

const statistics = computed(() => {
  if (!data.value) return null
  return {
    totalStocks: data.value.total_stocks,
    dividendPaying: data.value.dividend_paying_stocks,
    nonDividend: data.value.non_dividend_stocks,
    avgYield: data.value.statistics.avg_yield,
    medianYield: data.value.statistics.median_yield,
    maxYield: data.value.statistics.max_yield,
    minYield: data.value.statistics.min_yield,
  }
})

const filteredStocks = computed(() => {
  if (!data.value?.stocks) return []
  
  let result = [...data.value.stocks]
  
  // 搜索筛选
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(s => 
      s.symbol.includes(q) || 
      s.stock_name.toLowerCase().includes(q)
    )
  }
  
  // 股息率筛选
  if (yieldFilter.value !== 'all') {
    result = result.filter(s => {
      const y = s.ttm_yield || 0
      if (yieldFilter.value === 'high') return y >= 5
      if (yieldFilter.value === 'mid') return y >= 3 && y < 5
      if (yieldFilter.value === 'low') return y >= 1 && y < 3
      if (yieldFilter.value === 'none') return y === 0
      return true
    })
  }
  
  // 排序
  result.sort((a, b) => {
    let valA = a[sortBy.value]
    let valB = b[sortBy.value]
    
    if (typeof valA === 'string') {
      valA = valA.toLowerCase()
      valB = valB.toLowerCase()
    }
    
    if (sortOrder.value === 'asc') {
      return valA > valB ? 1 : -1
    }
    return valA < valB ? 1 : -1
  })
  
  return result
})

const paginatedStocks = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredStocks.value.slice(start, end)
})

const totalPages = computed(() => {
  return Math.ceil(filteredStocks.value.length / pageSize.value)
})

const updateSort = (value) => {
  if (sortBy.value === value) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = value
    sortOrder.value = value === 'ttm_yield' ? 'desc' : 'asc'
  }
  currentPage.value = 1
}

const goBack = () => {
  router.push('/')
}

const goToPage = (page) => {
  if (page >= 1 && page <= totalPages.value) {
    currentPage.value = page
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }
}

const getYieldClass = (value) => {
  if (value >= 5) return 'text-emerald-600 font-bold'
  if (value >= 3) return 'text-emerald-500 font-semibold'
  if (value >= 1) return 'text-slate-700'
  return 'text-slate-400'
}

const getYieldBadgeClass = (value) => {
  if (value >= 5) return 'bg-emerald-100 text-emerald-700 border-emerald-200'
  if (value >= 3) return 'bg-blue-100 text-blue-700 border-blue-200'
  if (value >= 1) return 'bg-slate-100 text-slate-600 border-slate-200'
  return 'bg-gray-100 text-gray-400 border-gray-200'
}
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- 返回按钮 -->
    <button 
      @click="goBack"
      class="flex items-center gap-2 text-slate-600 hover:text-slate-800 mb-6 transition-colors"
    >
      <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
      </svg>
      <span>返回首页</span>
    </button>

    <!-- 页面标题 -->
    <div class="mb-8">
      <h1 class="text-3xl font-display font-bold text-slate-800 mb-2">全市场股票股息率</h1>
      <p class="text-slate-500">基于 TTM 分红数据的全 A 股股息率排名</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-800"></div>
    </div>

    <!-- 错误状态 -->
    <div v-else-if="error" class="text-center py-20">
      <p class="text-red-500 mb-4">{{ error }}</p>
      <button @click="goBack" class="btn btn-primary">返回首页</button>
    </div>

    <!-- 数据展示 -->
    <div v-else-if="data" class="space-y-6">
      <!-- 统计概览卡片 -->
      <div v-if="statistics" class="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 lg:p-6">
          <p class="text-xs lg:text-sm text-slate-500 mb-1">总股票数</p>
          <p class="text-xl lg:text-2xl font-bold text-slate-800">{{ statistics.totalStocks }}</p>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 lg:p-6">
          <p class="text-xs lg:text-sm text-slate-500 mb-1">有股息股票</p>
          <p class="text-xl lg:text-2xl font-bold text-emerald-600">{{ statistics.dividendPaying }}</p>
          <p class="text-xs text-slate-400">{{ ((statistics.dividendPaying / statistics.totalStocks) * 100).toFixed(1) }}%</p>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 lg:p-6">
          <p class="text-xs lg:text-sm text-slate-500 mb-1">平均股息率</p>
          <p class="text-xl lg:text-2xl font-bold text-blue-600">{{ formatYield(statistics.avgYield) }}</p>
          <p class="text-xs text-slate-400">中位数 {{ formatYield(statistics.medianYield) }}</p>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4 lg:p-6">
          <p class="text-xs lg:text-sm text-slate-500 mb-1">最高/最低</p>
          <p class="text-lg lg:text-xl font-bold text-slate-800">
            <span class="text-emerald-600">{{ formatYield(statistics.maxYield) }}</span>
            <span class="text-slate-400 mx-1">/</span>
            <span class="text-slate-500">{{ formatYield(statistics.minYield) }}</span>
          </p>
        </div>
      </div>

      <!-- 搜索和筛选工具栏 -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
        <div class="flex flex-col lg:flex-row gap-4">
          <!-- 搜索框 -->
          <div class="flex-1">
            <input
              v-model="searchQuery"
              type="text"
              placeholder="搜索股票代码或名称..."
              class="w-full px-4 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-500 focus:border-transparent"
            >
          </div>
          
          <!-- 股息率筛选 -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-slate-500 whitespace-nowrap">股息率:</span>
            <select 
              v-model="yieldFilter"
              class="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-500 focus:border-transparent"
            >
              <option v-for="opt in yieldFilterOptions" :key="opt.value" :value="opt.value">
                {{ opt.label }}
              </option>
            </select>
          </div>
          
          <!-- 排序方式 -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-slate-500 whitespace-nowrap">排序:</span>
            <div class="flex gap-1 flex-wrap">
              <button
                v-for="option in sortOptions"
                :key="option.value"
                @click="updateSort(option.value)"
                :class="[
                  'px-3 py-2 text-sm rounded-lg transition-all',
                  sortBy === option.value 
                    ? 'bg-slate-800 text-white' 
                    : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
                ]"
              >
                {{ option.label }}
                <span v-if="sortBy === option.value" class="ml-1">
                  {{ sortOrder === 'desc' ? '↓' : '↑' }}
                </span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 结果统计 -->
      <div class="flex items-center justify-between text-sm text-slate-500">
        <span>共 {{ filteredStocks.length }} 只股票</span>
        <span>显示 {{ (currentPage - 1) * pageSize + 1 }}-{{ Math.min(currentPage * pageSize, filteredStocks.length) }} 条</span>
      </div>

      <!-- 股票表格 -->
      <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
        <!-- 桌面端表格 -->
        <div class="hidden md:block overflow-x-auto">
          <table class="w-full">
            <thead class="bg-slate-50 border-b border-slate-200">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider w-16">
                  排名
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider w-24">
                  代码
                </th>
                <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  名称
                </th>
                <th class="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  当前价格
                </th>
                <th class="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  TTM分红
                </th>
                <th class="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
                  股息率
                </th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-100">
              <tr 
                v-for="stock in paginatedStocks" 
                :key="stock.symbol"
                class="hover:bg-slate-50 transition-colors"
              >
                <td class="px-4 py-3">
                  <span class="text-sm font-medium text-slate-500">{{ stock.rank }}</span>
                </td>
                <td class="px-4 py-3">
                  <span class="font-mono text-sm text-slate-600">{{ stock.symbol }}</span>
                </td>
                <td class="px-4 py-3">
                  <span class="font-medium text-slate-800">{{ stock.stock_name }}</span>
                </td>
                <td class="px-4 py-3 text-right">
                  <span class="text-sm text-slate-700">{{ formatPrice(stock.current_price) }}</span>
                </td>
                <td class="px-4 py-3 text-right">
                  <span class="text-sm text-slate-700">{{ formatPrice(stock.ttm_dividend) }}</span>
                </td>
                <td class="px-4 py-3 text-right">
                  <span :class="['text-sm font-semibold', getYieldClass(stock.ttm_yield)]">
                    {{ formatYield(stock.ttm_yield) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- 移动端卡片列表 -->
        <div class="md:hidden divide-y divide-slate-100">
          <div 
            v-for="stock in paginatedStocks" 
            :key="stock.symbol"
            class="p-4 hover:bg-slate-50 transition-colors"
          >
            <div class="flex items-center justify-between mb-2">
              <div class="flex items-center gap-3">
                <span class="text-sm font-medium text-slate-400 w-8">#{{ stock.rank }}</span>
                <div>
                  <h3 class="font-semibold text-slate-800">{{ stock.stock_name }}</h3>
                  <p class="font-mono text-xs text-slate-500">{{ stock.symbol }}</p>
                </div>
              </div>
              <span :class="['px-2 py-1 rounded-full text-xs font-medium border', getYieldBadgeClass(stock.ttm_yield)]">
                {{ formatYield(stock.ttm_yield) }}
              </span>
            </div>
            <div class="flex justify-between text-sm mt-2">
              <span class="text-slate-500">价格: <span class="text-slate-700">{{ formatPrice(stock.current_price) }}</span></span>
              <span class="text-slate-500">TTM分红: <span class="text-slate-700">{{ formatPrice(stock.ttm_dividend) }}</span></span>
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <div v-if="paginatedStocks.length === 0" class="text-center py-12">
          <svg class="w-12 h-12 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <p class="text-slate-500">没有找到符合条件的股票</p>
        </div>
      </div>

      <!-- 分页 -->
      <div v-if="totalPages > 1" class="flex items-center justify-center gap-2 pt-4">
        <button
          @click="goToPage(currentPage - 1)"
          :disabled="currentPage === 1"
          class="px-3 py-2 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          上一页
        </button>
        
        <div class="flex items-center gap-1">
          <button
            v-for="page in Math.min(7, totalPages)"
            :key="page"
            @click="goToPage(page)"
            :class="[
              'w-10 h-10 rounded-lg text-sm font-medium transition-all',
              currentPage === page
                ? 'bg-slate-800 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            ]"
          >
            {{ page }}
          </button>
          <span v-if="totalPages > 7" class="px-2 text-slate-400">...</span>
          <button
            v-if="totalPages > 7"
            @click="goToPage(totalPages)"
            :class="[
              'w-10 h-10 rounded-lg text-sm font-medium transition-all',
              currentPage === totalPages
                ? 'bg-slate-800 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100 border border-slate-200'
            ]"
          >
            {{ totalPages }}
          </button>
        </div>
        
        <button
          @click="goToPage(currentPage + 1)"
          :disabled="currentPage === totalPages"
          class="px-3 py-2 rounded-lg border border-slate-300 text-slate-600 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>
