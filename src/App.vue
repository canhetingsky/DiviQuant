<script setup>
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div class="min-h-screen flex flex-col">
    <header class="bg-white border-b border-slate-200 sticky top-0 z-50">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between h-16">
          <router-link to="/" class="flex items-center gap-3">
            <div class="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
              <span class="text-white font-bold text-sm">DQ</span>
            </div>
            <h1 class="text-xl font-display font-semibold text-slate-800">DiviQuant</h1>
          </router-link>
          <nav class="flex items-center gap-1 sm:gap-4">
            <router-link 
              to="/" 
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                route.path === '/' 
                  ? 'bg-slate-100 text-slate-800' 
                  : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
              ]"
            >
              <span class="hidden sm:inline">指数看板</span>
              <span class="sm:hidden">指数</span>
            </router-link>
            <router-link 
              to="/stocks" 
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                route.path === '/stocks' 
                  ? 'bg-slate-100 text-slate-800' 
                  : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
              ]"
            >
              <span class="hidden sm:inline">分红排行</span>
              <span class="sm:hidden">分红</span>
            </router-link>
            <router-link 
              to="/yield" 
              :class="[
                'px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                route.path === '/yield' 
                  ? 'bg-slate-100 text-slate-800' 
                  : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
              ]"
            >
              <span class="hidden sm:inline">股息率</span>
              <span class="sm:hidden">股息率</span>
            </router-link>
          </nav>
        </div>
      </div>
    </header>
    
    <main class="flex-1">
      <router-view v-slot="{ Component }">
        <transition name="fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
    
    <footer class="bg-white border-t border-slate-200 py-4">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        <p class="text-sm text-slate-400">数据来源于 AkShare，仅供参考不构成投资建议</p>
      </div>
    </footer>
  </div>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>