import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../components/LandingPage.vue'
import Dashboard from '../components/Dashboard.vue'
import CreateCV from '../components/CreateCV.vue'
import Login from '../components/Login.vue'
import RequestJoin from '../components/RequestJoin.vue'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: LandingPage
  },
  {
    path: '/login',
    name: 'Login',
    component: Login
  },
  {
    path: '/request-join',
    name: 'RequestJoin',
    component: RequestJoin
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: Dashboard
  },
  {
    path: '/create-cv',
    name: 'CreateCV',
    component: CreateCV
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
