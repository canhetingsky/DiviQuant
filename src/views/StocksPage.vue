<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { fetchStockDividendSummary, formatPrice } from '../utils/data.js'
import StockRankingTable from '../components/StockRankingTable.vue'

const router = useRouter()

const data = ref(null)
const loading = ref(true)
const error = ref(null)
const searchQuery = ref('')
const sortBy = ref('total_dividend')
const sortOrder = ref('desc')
const yearFilter = ref('all')
const currentPage = ref(1)
const pageSize = ref(50)

const sortOptions = [
  { value: 'total_dividend', label: '累计分红' },
  { value: 'avg_annual', label: '年均分红' },
  { value: 'consecutive_years', label: '连续年限' },
  { value: 'symbol', label: '股票代码' },
]

const yearFilterOptions = [
  { value: 'all', label: '全部分红', count: 0 },
  { value: '5', label: '5年以上', count: 0 },
  { value: '10', label: '10年以上', count: 0 },
  { value: '20', label: '20年以上', count: 0 },
  { value: '30', label: '30年以上', count: 0 },
]

onMounted(async () => {
  try {
    data.value = await fetchStockDividendSummary()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

const statistics = computed(() => {
  if (!data.value) return null
  return {
    totalStocks: data.value.stock_count,
    dividendPaying: data.value.statistics.dividend_paying_stocks,
    nonDividend: data.value.statistics.non_dividend_stocks,
    dividendRate: ((data.value.statistics.dividend_paying_stocks / data.value.stock_count) * 100).toFixed(1)
  }
})

const filteredStocks = computed(() => {
  if (!data.value?.top_dividend_stocks) return []
  
  let result = [...data.value.top_dividend_stocks]
  
  // 搜索筛选
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(s => 
      s.symbol.includes(q) || 
      s.stock_name.toLowerCase().includes(q)
    )
  }
  
  // 年限筛选
  if (yearFilter.value !== 'all') {
    const minYears = parseInt(yearFilter.value)
    result = result.filter(s => s.consecutive_years >= minYears)
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

const yearFilterCounts = computed(() => {
  if (!data.value?.top_dividend_stocks) return yearFilterOptions
  
  const stocks = data.value.top_dividend_stocks
  return yearFilterOptions.map(opt => {
    if (opt.value === 'all') {
      return { ...opt, count: stocks.length }
    }
    const minYears = parseInt(opt.value)
    return { ...opt, count: stocks.filter(s => s.consecutive_years >= minYears).length }
  })
})

const updateSort = (value) => {
  if (sortBy.value === value) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = value
    sortOrder.value = 'desc'
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
      <h1 class="text-3xl font-display font-bold text-slate-800 mb-2">全市场股票股息率排行榜</h1>
      <p class="text-slate-500">基于历史累计分红数据的全 A 股排名</p>
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
      <div v-if="statistics" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <p class="text-sm text-slate-500 mb-1">总股票数</p>
          <p class="text-2xl font-bold text-slate-800">{{ statistics.totalStocks }}</p>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <p class="text-sm text-slate-500 mb-1">有分红股票</p>
          <p class="text-2xl font-bold text-emerald-600">{{ statistics.dividendPaying }}</p>
          <p class="text-xs text-slate-400">占比 {{ statistics.dividendRate }}%</p>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <p class="text-sm text-slate-500 mb-1">无分红股票</p>
          <p class="text-2xl font-bold text-slate-600">{{ statistics.nonDividend }}</p>
        </div>
        <div class="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
          <p class="text-sm text-slate-500 mb-1">数据更新时间</p>
          <p class="text-lg font-semibold text-slate-800">{{ data.generated_at?.split(' ')[0] }}</p>
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
          
          <!-- 年限筛选 -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-slate-500 whitespace-nowrap">分红年限:</span>
            <select 
              v-model="yearFilter"
              class="px-3 py-2 border border-slate-300 rounded-lg focus:ring-2 focus:ring-slate-500 focus:border-transparent"
            >
              <option 
                v-for="opt in yearFilterCounts" 
                :key="opt.value" 
                :value="opt.value"
              >
                {{ opt.label }} ({{ opt.count }})
              </option>
            </select>
          </div>
          
          <!-- 排序方式 -->
          <div class="flex items-center gap-2">
            <span class="text-sm text-slate-500 whitespace-nowrap">排序:</span>
            <div class="flex gap-1">
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
        <span>显示 {{ paginatedStocks.length }} 条</span>
      </div>

      <!-- 股票排名表格 -->
      <StockRankingTable 
        :stocks="paginatedStocks" 
        :start-rank="(currentPage - 1) * pageSize + 1"
      />

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
            v-for="page in Math.min(5, totalPages)"
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
          <span v-if="totalPages > 5" class="px-2 text-slate-400">...</span>
          <button
            v-if="totalPages > 5"
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
