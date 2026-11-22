import { ref, onMounted } from 'vue'

export type Theme = 'light' | 'dark'

const currentTheme = ref<Theme>('dark')

export const useTheme = () => {
  const applyTheme = (theme: Theme) => {
    currentTheme.value = theme
    if (typeof window !== 'undefined') {
      const root = document.documentElement
      if (theme === 'dark') {
        root.classList.add('dark')
      } else {
        root.classList.remove('dark')
      }
      try {
        localStorage.setItem('priya-theme', theme)
      } catch (err) {
        console.warn('Could not persist theme to localStorage:', err)
      }
    }
  }

  const toggleTheme = () => {
    const next = currentTheme.value === 'dark' ? 'light' : 'dark'
    applyTheme(next)
  }

  const initTheme = () => {
    if (typeof window !== 'undefined') {
      try {
        const saved = localStorage.getItem('priya-theme') as Theme | null
        if (saved === 'light' || saved === 'dark') {
          applyTheme(saved)
          return
        }
      } catch {}

      // Check system preference
      if (window.matchMedia && window.matchMedia('(prefers-color-scheme: light)').matches) {
        applyTheme('light')
      } else {
        applyTheme('dark')
      }
    }
  }

  return {
    theme: currentTheme,
    toggleTheme,
    setTheme: applyTheme,
    initTheme
  }
}
