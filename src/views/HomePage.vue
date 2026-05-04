<script setup>
import { ref, computed, onMounted } from 'vue'
import { fetchIndexes, sortIndexes, searchIndexes, formatDate } from '../utils/data.js'
import IndexCard from '../components/IndexCard.vue'

const indexes = ref([])
const loading = ref(true)
const error = ref(null)
const searchQuery = ref('')
const sortBy = ref('avg_yield')
const sortOrder = ref('desc')

const filteredIndexes = computed(() => {
  let result = indexes.value
  result = searchIndexes(result, searchQuery.value)
  result = sortIndexes(result, sortBy.value, sortOrder.value)
  return result
})

const sortOptions = [
  { value: 'avg_yield', label: '平均股息率' },
  { value: 'median_yield', label: '中位数' },
  { value: 'max_yield', label: '最高股息率' },
  { value: 'stock_count', label: '成分股数量' },
]

onMounted(async () => {
  try {
    indexes.value = await fetchIndexes()
  } catch (e) {
    error.value = e.message
  } finally {
    loading.value = false
  }
})

const updateSort = (value) => {
  if (sortBy.value === value) {
    sortOrder.value = sortOrder.value === 'asc' ? 'desc' : 'asc'
  } else {
    sortBy.value = value
    sortOrder.value = 'desc'
  }
}

const lastUpdated = computed(() => {
  if (!indexes.value.length) return ''
  return formatDate(indexes.value[0].updated_at)
})
</script>

<template>
  <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <div class="mb-8">
      <h1 class="text-3xl font-display font-bold text-slate-800 mb-2">指数股息率看板</h1>
      <p class="text-slate-500">比较不同红利指数的整体股息率表现</p>
    </div>
    
    <div class="flex flex-col sm:flex-row gap-4 mb-6">
      <div class="flex-1">
        <input
          v-model="searchQuery"
          type="text"
          placeholder="搜索指数名称或代码..."
          class="input"
        >
      </div>
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
              {{ sortOrder === 'asc' ? '↑' : '↓' }}
            </span>
          </button>
        </div>
      </div>
    </div>
    
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-slate-800"></div>
    </div>
    
    <div v-else-if="error" class="text-center py-20">
      <p class="text-red-500">{{ error }}</p>
    </div>
    
    <div v-else>
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <IndexCard
          v-for="index in filteredIndexes"
          :key="index.index_code"
          :index="index"
        />
      </div>
      
      <div v-if="filteredIndexes.length === 0" class="text-center py-20">
        <p class="text-slate-400">没有找到匹配的指数</p>
      </div>
      
      <div class="mt-8 pt-6 border-t border-slate-200 flex items-center justify-between text-sm text-slate-400">
        <span>共 {{ indexes.length }} 个指数</span>
        <span>数据更新于 {{ lastUpdated }}</span>
      </div>
    </div>
  </div>
</template>