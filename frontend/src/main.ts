import { createApp } from 'vue'
import Antd from 'ant-design-vue'
import 'ant-design-vue/dist/reset.css'
import './style.css'
import App from './App.vue'
import router from './router'

// Apply dark theme immediately
if (typeof document !== 'undefined') {
  document.documentElement.classList.add('dark')
  document.documentElement.setAttribute('data-theme', 'dark')
}

const app = createApp(App)
app.use(Antd)
app.use(router)
app.mount('#app')
