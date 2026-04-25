import { createRouter, createWebHistory } from 'vue-router'
import HomePage from '../views/HomePage.vue'

const routes = [
  {
    path: '/',
    name: 'home',
    component: HomePage
  },
  {
    path: '/province/:name',
    name: 'province',
    component: () => import('../views/ProvincePage.vue')
  },
  {
    path: '/village/:id',
    name: 'villageDetail',
    component: () => import('../views/VillageDetail.vue')
  },
  {
    path: '/favorites',
    name: 'favorites',
    component: () => import('../views/Favorites.vue')
  },
  {
    path: '/products',
    name: 'products',
    component: () => import('../views/ProductsPage.vue')
  },
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginPage.vue')
  },
  {
    path: '/ranking',
    name: 'ranking',
    component: () => import('../views/RankingPage.vue')
  },
  {
  path: '/person',
  name: 'person',
  component: () => import('../views/PersonPage.vue')
}
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router