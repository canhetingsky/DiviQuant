import { createApp } from 'vue'
import { createRouter, createWebHistory } from 'vue-router'
import App from './App.vue'
import HomePage from './views/HomePage.vue'
import DetailPage from './views/DetailPage.vue'
import './style.css'

const routes = [
  { path: '/', name: 'home', component: HomePage },
  { path: '/index/:indexCode', name: 'detail', component: DetailPage },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

const app = createApp(App)
app.use(router)
app.mount('#app')