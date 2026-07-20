<script setup>
import { formatPrice, formatYield, formatDateShort, getYieldClass } from '../utils/data.js'

const props = defineProps({
  stock: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close'])

const hasDividendHistory = () => {
  return props.stock.total_dividend > 0 || props.stock.consecutive_years > 0
}

const getYearBadgeClass = (years) => {
  if (years >= 30) return 'bg-purple-100 text-purple-700'
  if (years >= 20) return 'bg-blue-100 text-blue-700'
  if (years >= 10) return 'bg-emerald-100 text-emerald-700'
  return 'bg-slate-100 text-slate-600'
}

const getDividendClass = (value) => {
  if (value >= 100) return 'text-amber-600'
  if (value >= 50) return 'text-emerald-600'
  if (value >= 20) return 'text-blue-600'
  return 'text-slate-700'
}

const handleOverlayClick = (e) => {
  if (e.target === e.currentTarget) {
    emit('close')
  }
}

const getIncludedDuration = () => {
  const includedDate = props.stock.included_date
  if (!includedDate) return { text: '未知', years: 0, months: 0 }
  
  const date = new Date(includedDate)
  if (isNaN(date.getTime())) return { text: '未知', years: 0, months: 0 }
  
  const now = new Date()
  const diffTime = now - date
  const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24))
  const years = Math.floor(diffDays / 365)
  const months = Math.floor((diffDays % 365) / 30)
  
  if (years > 0 && months > 0) {
    return { text: `${years}年${months}个月`, years, months }
  } else if (years > 0) {
    return { text: `${years}年`, years, months }
  } else if (months > 0) {
    return { text: `${months}个月`, years, months }
  } else {
    return { text: `${diffDays}天`, years, months }
  }
}
</script>

<template>
  <div 
    class="fixed inset-0 z-50 flex items-center justify-center p-4"
    @click="handleOverlayClick"
  >
    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm"></div>
    
    <div class="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden animate-in fade-in zoom-in duration-200">
      <div class="bg-gradient-to-r from-slate-800 to-slate-700 px-6 py-5">
        <div class="flex items-center justify-between">
          <div>
            <div class="flex items-center gap-2 mb-1">
              <h3 class="text-xl font-bold text-white">{{ stock.stock_name }}</h3>
              <span class="bg-white/20 text-white text-xs px-2 py-0.5 rounded-full">
                #{{ stock.rank }}
              </span>
            </div>
            <p class="text-slate-300 font-mono">{{ stock.symbol }}</p>
          </div>
          <button 
            @click="emit('close')"
            class="text-slate-300 hover:text-white transition-colors"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <div class="p-6 space-y-6">
        <template v-if="hasDividendHistory()">
          <div class="grid grid-cols-2 gap-4">
            <div class="bg-slate-50 rounded-xl p-4">
              <p class="text-xs text-slate-500 mb-2">累计分红</p>
              <p :class="['text-2xl font-bold', getDividendClass(stock.total_dividend)]">
                {{ formatPrice(stock.total_dividend) }}
                <span class="text-sm font-normal text-slate-500">元/股</span>
              </p>
            </div>
            <div class="bg-slate-50 rounded-xl p-4">
              <p class="text-xs text-slate-500 mb-2">年均分红</p>
              <p class="text-2xl font-bold text-slate-800">
                {{ formatPrice(stock.avg_annual) }}
                <span class="text-sm font-normal text-slate-500">元/股</span>
              </p>
            </div>
          </div>

          <div class="flex items-center justify-between bg-slate-50 rounded-xl p-4">
            <div>
              <p class="text-sm text-slate-500">连续分红年限</p>
              <p class="text-xl font-bold text-slate-800">{{ stock.consecutive_years }} 年</p>
            </div>
            <span 
              :class="[
                'px-3 py-1 rounded-full text-sm font-medium',
                getYearBadgeClass(stock.consecutive_years)
              ]"
            >
              {{ stock.consecutive_years >= 30 ? '长期稳定' : stock.consecutive_years >= 20 ? '稳定分红' : stock.consecutive_years >= 10 ? '持续分红' : '分红中' }}
            </span>
          </div>

          <div>
            <p class="text-sm text-slate-500 mb-3">分红稳定性</p>
            <div class="flex items-center gap-1">
              <svg 
                v-for="n in Math.min(5, Math.ceil(stock.consecutive_years / 5))" 
                :key="n"
                class="w-6 h-6 text-emerald-500" 
                fill="currentColor" 
                viewBox="0 0 20 20"
              >
                <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
              </svg>
              <svg 
                v-for="n in Math.max(0, 5 - Math.min(5, Math.ceil(stock.consecutive_years / 5)))" 
                :key="'empty-' + n"
                class="w-6 h-6 text-slate-200" 
                fill="none" 
                stroke="currentColor" 
                viewBox="0 0 20 20"
              >
                <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM10 10l3 3m0-3l-3 3m3-3H7"/>
              </svg>
            </div>
            <p v-if="stock.consecutive_years > 25" class="text-xs text-slate-400 mt-2">
              🎖️ 连续25年以上分红，属于长期稳定分红标的
            </p>
          </div>

          <div>
            <p class="text-sm text-slate-500 mb-2">累计分红对比（基准：300元）</p>
            <div class="h-3 bg-slate-100 rounded-full overflow-hidden">
              <div 
                class="h-full bg-gradient-to-r from-emerald-400 to-emerald-600 rounded-full transition-all duration-500"
                :style="{ width: Math.min((stock.total_dividend / 300) * 100, 100) + '%' }"
              ></div>
            </div>
            <div class="flex justify-between text-xs text-slate-400 mt-1">
              <span>0元</span>
              <span>{{ formatPrice(stock.total_dividend) }}元</span>
              <span>300元</span>
            </div>
          </div>
        </template>

        <template v-else>
          <div class="bg-amber-50 border border-amber-200 rounded-xl p-4 text-center">
            <svg class="w-12 h-12 text-amber-400 mx-auto mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
            </svg>
            <p class="text-amber-700 font-medium">暂无历史分红数据</p>
            <p class="text-amber-600 text-sm mt-1">该股票未进入累计分红前100名</p>
          </div>
        </template>

        <div class="grid grid-cols-3 gap-3">
          <div class="bg-slate-50 rounded-xl p-3 text-center">
            <p class="text-xs text-slate-500 mb-1">TTM分红</p>
            <p class="text-lg font-bold text-slate-800">{{ formatPrice(stock.ttm_dividend) }}<span class="text-xs font-normal text-slate-500">元/股</span></p>
          </div>
          <div class="bg-slate-50 rounded-xl p-3 text-center">
            <p class="text-xs text-slate-500 mb-1">TTM股息率</p>
            <p :class="['text-lg font-bold', getYieldClass(stock.ttm_yield)]">{{ formatYield(stock.ttm_yield) }}</p>
          </div>
          <div class="bg-slate-50 rounded-xl p-3 text-center">
            <p class="text-xs text-slate-500 mb-1">当前价格</p>
            <p class="text-lg font-bold text-slate-800">{{ formatPrice(stock.current_price) }}<span class="text-xs font-normal text-slate-500">元</span></p>
          </div>
        </div>

        <div class="bg-slate-50 rounded-xl p-4">
          <div class="flex items-center justify-between mb-3">
            <span class="text-sm text-slate-500">纳入指数日期</span>
            <span class="text-lg font-medium text-slate-800">{{ stock.included_date || '-' }}</span>
          </div>
          <div class="flex items-center justify-between">
            <span class="text-sm text-slate-500">已纳入时长</span>
            <span class="text-lg font-medium text-slate-800">{{ getIncludedDuration().text }}</span>
          </div>
        </div>
      </div>

      <div class="px-6 py-4 bg-slate-50 border-t border-slate-100">
        <button 
          @click="emit('close')"
          class="w-full py-3 bg-slate-800 text-white rounded-xl font-medium hover:bg-slate-700 transition-colors"
        >
          关闭
        </button>
      </div>
    </div>
  </div>
</template>