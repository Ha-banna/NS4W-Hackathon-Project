import { createRouter, createWebHistory } from 'vue-router'
import LandingPage from '../components/LandingPage.vue'
import Dashboard from '../components/Dashboard.vue'
import CreateCV from '../components/CreateCV.vue'
import Login from '../components/Login.vue'
import RequestJoin from '../components/RequestJoin.vue'
import AdminDashboard from '../components/AdminDashboard.vue'
import CVResults from '../components/CVResults.vue'

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
  },
  {
    path: '/admin',
    name: 'AdminDashboard',
    component: AdminDashboard
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
