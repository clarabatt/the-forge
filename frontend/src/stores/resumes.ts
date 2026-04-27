import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

export interface Resume {
  id: string
  file_name: string
  bucket_key: string
  resume_type: 'BASE' | 'TAILORED'
  is_latest: boolean
  version_number: number
  raw_text: string | null
  user_id: string
  application_id: string | null
  created_at: string
}

export const useResumesStore = defineStore('resumes', () => {
  const resumes = ref<Resume[]>([])
  const selectedResumeId = ref<string | null>(null)

  const baseResumes = computed(() =>
    resumes.value.filter((r) => r.resume_type === 'BASE' && r.is_latest),
  )

  async function fetchAll() {
    const res = await fetch('/api/resumes/', { credentials: 'include' })
    if (!res.ok) return
    resumes.value = await res.json()
    if (!selectedResumeId.value) {
      selectedResumeId.value = baseResumes.value[0]?.id ?? null
    }
  }

  return { resumes, baseResumes, selectedResumeId, fetchAll }
})
