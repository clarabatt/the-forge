import { defineStore } from 'pinia'
import { ref } from 'vue'

export enum PipelineStatus {
  UPLOADED = 'UPLOADED',
  ANALYZING = 'ANALYZING',
  PENDING_APPROVAL = 'PENDING_APPROVAL',
  TAILORING = 'TAILORING',
  VALIDATING = 'VALIDATING',
  PENDING_RETRY = 'PENDING_RETRY',
  READY = 'READY',
  FAILED = 'FAILED',
}

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

  function patch(id: string, changes: Partial<Application>) {
    if (current.value?.id === id) Object.assign(current.value, changes)
    const inList = applications.value.find((a) => a.id === id)
    if (inList) Object.assign(inList, changes)
  }

  async function create(jobDescription: string, baseResumeId: string): Promise<Application> {
    const res = await fetch('/api/applications/', {
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ job_description: jobDescription, base_resume_id: baseResumeId }),
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail ?? 'Failed to create application')
    }
    const app: Application = await res.json()
    applications.value.unshift(app)
    return app
  }

  async function fetchResumeHtml(id: string): Promise<string> {
    const res = await fetch(`/api/applications/${id}/resume-html`, { credentials: 'include' })
    if (!res.ok) throw new Error(`Failed to load resume (${res.status})`)
    const body = await res.json()
    return body.html ?? ''
  }

  async function retry(id: string): Promise<void> {
    const res = await fetch(`/api/applications/${id}/retry`, {
      method: 'POST',
      credentials: 'include',
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail ?? 'Retry failed')
    }
    const app: Application = await res.json()
    if (current.value?.id === id) Object.assign(current.value, app)
    const inList = applications.value.find((a) => a.id === id)
    if (inList) Object.assign(inList, app)
  }

  function subscribeToStatus(id: string, onUpdate: (event: MessageEvent) => void): EventSource {
    const es = new EventSource(`/api/applications/${id}/stream`)
    es.addEventListener('status_changed', onUpdate)
    return es
  }

  return { applications, current, isLoading, fetchAll, fetchOne, create, patch, retry, fetchResumeHtml, subscribeToStatus }
})
