import { ref, computed, onMounted } from 'vue'
import { theme } from 'ant-design-vue'
import type { ThemeConfig } from 'ant-design-vue/es/config-provider'

type Theme = 'light' | 'dark'

const THEME_STORAGE_KEY = 'app-theme'

const isDarkMode = ref<boolean>(true) // Default to dark theme
let initialized = false

// Initialize theme from localStorage or system preference
const initTheme = () => {
  if (typeof window === 'undefined') return
  
  const savedTheme = localStorage.getItem(THEME_STORAGE_KEY) as Theme | null
  if (savedTheme) {
    isDarkMode.value = savedTheme === 'dark'
  } else {
    // Default to dark theme
    isDarkMode.value = true
  }
  applyTheme()
  initialized = true
}

// Apply theme to document
const applyTheme = () => {
  if (typeof document === 'undefined') return
  
  if (isDarkMode.value) {
    document.documentElement.classList.add('dark')
    document.documentElement.setAttribute('data-theme', 'dark')
  } else {
    document.documentElement.classList.remove('dark')
    document.documentElement.setAttribute('data-theme', 'light')
  }
}

export function useTheme() {
  // Initialize immediately if in browser
  if (typeof window !== 'undefined' && !initialized) {
    initTheme()
    
    // Listen for system theme changes
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)')
    const handleChange = (e: MediaQueryListEvent) => {
      if (!localStorage.getItem(THEME_STORAGE_KEY)) {
        isDarkMode.value = e.matches
        applyTheme()
      }
    }
    mediaQuery.addEventListener('change', handleChange)
  }
  
  // Apply theme immediately if not initialized yet
  if (typeof document !== 'undefined' && !initialized) {
    applyTheme()
  }

  // Toggle theme
  const toggleTheme = () => {
    isDarkMode.value = !isDarkMode.value
    localStorage.setItem(THEME_STORAGE_KEY, isDarkMode.value ? 'dark' : 'light')
    applyTheme()
  }

  // Set theme explicitly
  const setTheme = (themeValue: Theme) => {
    isDarkMode.value = themeValue === 'dark'
    localStorage.setItem(THEME_STORAGE_KEY, themeValue)
    applyTheme()
  }

  // Get Ant Design Vue theme config
  const getThemeConfig = computed((): ThemeConfig => {
    return {
      algorithm: isDarkMode.value ? theme.darkAlgorithm : theme.defaultAlgorithm,
    }
  })

  return {
    isDarkMode,
    toggleTheme,
    setTheme,
    getThemeConfig,
  }
}
