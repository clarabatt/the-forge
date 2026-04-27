import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

interface User {
  id: string
  email: string
  full_name: string
  picture_url: string | null
}

interface Usage {
  cost_usd: number
  monthly_cap_usd: number
}

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const usage = ref<Usage | null>(null)
  const isLoading = ref(false)

  const isAuthenticated = computed(() => user.value !== null)

  async function fetchMe() {
    isLoading.value = true
    try {
      const res = await fetch('/api/users/me', { credentials: 'include' })
      if (res.ok) {
        const data = await res.json()
        user.value = data.user
      }
    } catch {
      // backend unreachable — treat as unauthenticated
    } finally {
      isLoading.value = false
    }
  }

  async function fetchUsage() {
    const res = await fetch('/api/users/me/usage', { credentials: 'include' })
    if (res.ok) usage.value = await res.json()
  }

  function logout() {
    user.value = null
    usage.value = null
  }

  return { user, usage, isLoading, isAuthenticated, fetchMe, fetchUsage, logout }
})
