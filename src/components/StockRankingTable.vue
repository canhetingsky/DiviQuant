<script setup>
import { computed } from 'vue'
import { formatPrice } from '../utils/data.js'

const props = defineProps({
  stocks: {
    type: Array,
    required: true,
  },
  startRank: {
    type: Number,
    default: 1,
  },
})

const getRankClass = (rank) => {
  if (rank === 1) return 'bg-yellow-400 text-yellow-900'
  if (rank === 2) return 'bg-slate-300 text-slate-800'
  if (rank === 3) return 'bg-amber-600 text-white'
  return 'bg-slate-100 text-slate-600'
}

const getDividendClass = (value) => {
  if (value >= 100) return 'text-amber-600 font-bold'
  if (value >= 50) return 'text-emerald-600 font-semibold'
  if (value >= 20) return 'text-blue-600'
  return 'text-slate-700'
}

const getYearBadgeClass = (years) => {
  if (years >= 30) return 'bg-purple-100 text-purple-700 border-purple-200'
  if (years >= 20) return 'bg-blue-100 text-blue-700 border-blue-200'
  if (years >= 10) return 'bg-emerald-100 text-emerald-700 border-emerald-200'
  return 'bg-slate-100 text-slate-600 border-slate-200'
}

const getProgressWidth = (value, max = 300) => {
  const percentage = Math.min((value / max) * 100, 100)
  return `${percentage}%`
}
</script>

<template>
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
              累计分红
            </th>
            <th class="px-4 py-3 text-right text-xs font-semibold text-slate-500 uppercase tracking-wider">
              年均分红
            </th>
            <th class="px-4 py-3 text-center text-xs font-semibold text-slate-500 uppercase tracking-wider">
              连续年限
            </th>
            <th class="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider">
              分红趋势
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr 
            v-for="(stock, index) in stocks" 
            :key="stock.symbol"
            class="hover:bg-slate-50 transition-colors"
          >
            <!-- 排名 -->
            <td class="px-4 py-3">
              <span 
                :class="[
                  'inline-flex items-center justify-center w-8 h-8 rounded-full text-sm font-bold',
                  getRankClass(startRank + index)
                ]"
              >
                {{ startRank + index }}
              </span>
            </td>
            
            <!-- 代码 -->
            <td class="px-4 py-3">
              <span class="font-mono text-sm text-slate-600">{{ stock.symbol }}</span>
            </td>
            
            <!-- 名称 -->
            <td class="px-4 py-3">
              <span class="font-medium text-slate-800">{{ stock.stock_name }}</span>
            </td>
            
            <!-- 累计分红 -->
            <td class="px-4 py-3 text-right">
              <span :class="['text-sm', getDividendClass(stock.total_dividend)]">
                {{ formatPrice(stock.total_dividend) }}元
              </span>
              <div class="mt-1 h-1 bg-slate-100 rounded-full overflow-hidden">
                <div 
                  class="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full"
                  :style="{ width: getProgressWidth(stock.total_dividend) }"
                ></div>
              </div>
            </td>
            
            <!-- 年均分红 -->
            <td class="px-4 py-3 text-right">
              <span class="text-sm text-slate-700">
                {{ formatPrice(stock.avg_annual) }}元
              </span>
            </td>
            
            <!-- 连续年限 -->
            <td class="px-4 py-3 text-center">
              <span 
                :class="[
                  'inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border',
                  getYearBadgeClass(stock.consecutive_years)
                ]"
              >
                {{ stock.consecutive_years }}年
              </span>
            </td>
            
            <!-- 分红趋势 -->
            <td class="px-4 py-3">
              <div class="flex items-center gap-1">
                <svg 
                  v-for="n in Math.min(5, Math.ceil(stock.consecutive_years / 5))" 
                  :key="n"
                  class="w-4 h-4 text-emerald-500" 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                </svg>
                <span v-if="stock.consecutive_years > 25" class="text-xs text-slate-400 ml-1">
                  长期稳定
                </span>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 移动端卡片列表 -->
    <div class="md:hidden divide-y divide-slate-100">
      <div 
        v-for="(stock, index) in stocks" 
        :key="stock.symbol"
        class="p-4 hover:bg-slate-50 transition-colors"
      >
        <div class="flex items-start justify-between mb-3">
          <div class="flex items-center gap-3">
            <span 
              :class="[
                'inline-flex items-center justify-center w-7 h-7 rounded-full text-xs font-bold',
                getRankClass(startRank + index)
              ]"
            >
              {{ startRank + index }}
            </span>
            <div>
              <h3 class="font-semibold text-slate-800">{{ stock.stock_name }}</h3>
              <p class="font-mono text-xs text-slate-500">{{ stock.symbol }}</p>
            </div>
          </div>
          <span 
            :class="[
              'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium border',
              getYearBadgeClass(stock.consecutive_years)
            ]"
          >
            {{ stock.consecutive_years }}年
          </span>
        </div>
        
        <div class="grid grid-cols-2 gap-4 mt-3">
          <div class="bg-slate-50 rounded-lg p-3">
            <p class="text-xs text-slate-500 mb-1">累计分红</p>
            <p :class="['text-lg font-bold', getDividendClass(stock.total_dividend)]">
              {{ formatPrice(stock.total_dividend) }}元
            </p>
          </div>
          <div class="bg-slate-50 rounded-lg p-3">
            <p class="text-xs text-slate-500 mb-1">年均分红</p>
            <p class="text-lg font-bold text-slate-700">
              {{ formatPrice(stock.avg_annual) }}元
            </p>
          </div>
        </div>
        
        <!-- 进度条 -->
        <div class="mt-3">
          <div class="h-1.5 bg-slate-100 rounded-full overflow-hidden">
            <div 
              class="h-full bg-gradient-to-r from-emerald-400 to-emerald-500 rounded-full"
              :style="{ width: getProgressWidth(stock.total_dividend) }"
            ></div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-if="stocks.length === 0" class="text-center py-12">
      <svg class="w-12 h-12 text-slate-300 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
      </svg>
      <p class="text-slate-500">没有找到符合条件的股票</p>
    </div>
  </div>
</template>
