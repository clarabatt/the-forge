import { defineStore } from 'pinia'
import { ref } from 'vue'

export type PipelineStatus =
  | 'UPLOADED'
  | 'ANALYZING'
  | 'PENDING_APPROVAL'
  | 'TAILORING'
  | 'VALIDATING'
  | 'PENDING_RETRY'
  | 'READY'
  | 'FAILED'

export interface Application {
  id: string
  company_name: string
  job_title: string
  status: PipelineStatus
  application_status: 'applied' | 'denied' | 'cancelled' | 'approved'
  created_at: string
}

export const useApplicationsStore = defineStore('applications', () => {
  const applications = ref<Application[]>([])
  const current = ref<Application | null>(null)
  const isLoading = ref(false)

  async function fetchAll() {
    isLoading.value = true
    try {
      const res = await fetch('/api/applications/', { credentials: 'include' })
      if (res.ok) applications.value = await res.json()
    } finally {
      isLoading.value = false
    }
  }

  async function fetchOne(id: string) {
    const res = await fetch(`/api/applications/${id}`, { credentials: 'include' })
    if (res.ok) current.value = await res.json()
  }

  function subscribeToStatus(id: string, onUpdate: (event: MessageEvent) => void): EventSource {
    const es = new EventSource(`/api/applications/${id}/stream`)
    es.addEventListener('status_changed', onUpdate)
    return es
  }

  return { applications, current, isLoading, fetchAll, fetchOne, subscribeToStatus }
})
