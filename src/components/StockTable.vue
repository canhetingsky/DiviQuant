<script setup>
import { ref, computed } from 'vue'
import { formatYield, formatPrice, formatDateShort, getYieldClass } from '../utils/data.js'

const props = defineProps({
  stocks: {
    type: Array,
    required: true,
  },
})

const searchQuery = ref('')
const sortBy = ref('ttm_yield')
const sortOrder = ref('desc')
const yieldFilter = ref('all')

const columns = [
  { key: 'rank', label: '排名', width: 'w-16' },
  { key: 'symbol', label: '代码', width: 'w-24' },
  { key: 'stock_name', label: '名称', width: 'w-32' },
  { key: 'included_date', label: '纳入日期', width: 'w-28' },
  { key: 'current_price', label: '现价', width: 'w-20' },
  { key: 'ttm_dividend', label: 'TTM分红', width: 'w-20' },
  { key: 'ttm_yield', label: '股息率', width: 'w-20' },
]

const filteredStocks = computed(() => {
  let result = [...props.stocks]
  
  if (searchQuery.value) {
    const q = searchQuery.value.toLowerCase()
    result = result.filter(s => 
      s.symbol.includes(q) || 
      s.stock_name.toLowerCase().includes(q)
    )
  }
  
  if (yieldFilter.value !== 'all') {
    const [min, max] = yieldFilter.value.split('-').map(Number)
    result = result.filter(s => {
      const y = s.ttm_yield || 0
      if (yieldFilter.value === 'high') return y >= 5
      if (yieldFilter.value === 'mid') return y >= 3 && y < 5
      return y < 3
    })
  }
  
  result.sort((a, b) => {
    const valA = a[sortBy.value] || 0
    const valB = b[sortBy.value] || 0
    return sortOrder.value === 'asc' ? valA - valB : valB - valA
  })
  
  return result
})

const toggleSort = (key) => {
  if (sortBy.value === key) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = key
    sortOrder.value = 'desc'
  }
}

const getYieldClassValue = (value) => getYieldClass(value)
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
    <div class="p-4 border-b border-slate-200 flex flex-col sm:flex-row gap-4">
      <input
        v-model="searchQuery"
        type="text"
        placeholder="搜索代码或名称..."
        class="input flex-1"
      >
      <select v-model="yieldFilter" class="input w-full sm:w-40">
        <option value="all">全部股息率</option>
        <option value="high">≥5%</option>
        <option value="mid">3%-5%</option>
        <option value="low">&lt;3%</option>
      </select>
    </div>
    
    <div class="overflow-x-auto scrollbar-thin">
      <table class="w-full">
        <thead class="bg-slate-50 text-left">
          <tr>
            <th 
              v-for="col in columns" 
              :key="col.key"
              @click="toggleSort(col.key)"
              :class="[col.width, 'px-4 py-3 text-xs font-medium text-slate-500 uppercase tracking-wider cursor-pointer hover:bg-slate-100 select-none']"
            >
              <div class="flex items-center gap-1">
                {{ col.label }}
                <span v-if="sortBy === col.key" class="text-slate-800">
                  {{ sortOrder === 'asc' ? '↑' : '↓' }}
                </span>
              </div>
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-slate-100">
          <tr 
            v-for="(stock, index) in filteredStocks" 
            :key="stock.symbol"
            class="hover:bg-slate-50 transition-colors"
          >
            <td class="px-4 py-3 text-sm text-slate-400">{{ index + 1 }}</td>
            <td class="px-4 py-3 font-mono text-sm text-slate-700">{{ stock.symbol }}</td>
            <td class="px-4 py-3 text-sm text-slate-700">{{ stock.stock_name }}</td>
            <td class="px-4 py-3 text-sm text-slate-500">{{ formatDateShort(stock.included_date) }}</td>
            <td class="px-4 py-3 text-sm text-slate-700 font-mono">{{ formatPrice(stock.current_price) }}</td>
            <td class="px-4 py-3 text-sm text-slate-700 font-mono">{{ formatPrice(stock.ttm_dividend) }}</td>
            <td class="px-4 py-3">
              <span :class="getYieldClassValue(stock.ttm_yield)" class="font-mono">
                {{ formatYield(stock.ttm_yield) }}
              </span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div class="p-4 border-t border-slate-200 text-sm text-slate-400">
      显示 {{ filteredStocks.length }} / {{ stocks.length }} 只股票
    </div>
  </div>
</template>