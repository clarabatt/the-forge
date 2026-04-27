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

export type SkillMatchStatus = 'found_in_resume' | 'missing'
export type SkillCategory = 'Hard Skill' | 'Soft Skill' | 'Tool' | 'Domain Knowledge'

export interface Skill {
  id: string
  skill_name: string
  category: SkillCategory
  match_status: SkillMatchStatus
  ai_confidence: number
  rank: number
}

export interface AnalysisFeedback {
  overall_assessment: string
  strong_points: string[]
  weak_points: string[]
  recommended_changes: string[]
}

export interface Application {
  id: string
  company_name: string
  job_title: string
  status: PipelineStatus
  application_status: 'applied' | 'denied' | 'cancelled' | 'approved'
  analysis_feedback: string | null
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

  async function deleteApplication(id: string): Promise<void> {
    const res = await fetch(`/api/applications/${id}`, {
      method: 'DELETE',
      credentials: 'include',
    })
    if (!res.ok) {
      const body = await res.json().catch(() => ({}))
      throw new Error(body.detail ?? 'Delete failed')
    }
    applications.value = applications.value.filter((a) => a.id !== id)
    if (current.value?.id === id) current.value = null
  }

  async function fetchSkills(id: string): Promise<Skill[]> {
    const res = await fetch(`/api/applications/${id}/skills`, { credentials: 'include' })
    if (!res.ok) throw new Error(`Failed to load skills (${res.status})`)
    return res.json()
  }

  async function downloadResume(id: string, format: 'docx' | 'pdf'): Promise<void> {
    const res = await fetch(`/api/applications/${id}/download/${format}`, { credentials: 'include' })
    if (!res.ok) throw new Error(`Download failed (${res.status})`)
    const disposition = res.headers.get('content-disposition') ?? ''
    const match = disposition.match(/filename="([^"]+)"/)
    const filename = match?.[1] ?? `resume.${format}`
    const blob = await res.blob()
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(url)
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

  return { applications, current, isLoading, fetchAll, fetchOne, create, patch, retry, deleteApplication, downloadResume, fetchSkills, fetchResumeHtml, subscribeToStatus }
})
