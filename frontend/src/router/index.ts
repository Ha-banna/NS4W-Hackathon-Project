import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../components/LandingPage.vue'
import Dashboard from '../components/Dashboard.vue'
import CreateCV from '../components/CreateCV.vue'
import CVResults from '../components/CVResults.vue'

const routes = [
  {
    path: '/',
    name: 'Landing',
    component: LandingPage
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
  },
  {
    path: '/cv/:id',
    name: 'CVResults',
    component: CVResults
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router
