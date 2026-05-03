<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { DialogClose, DialogTitle } from 'radix-vue'
import { useApplicationsStore } from '@/stores/applications'
import { useResumesStore } from '@/stores/resumes'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseDialog from '@/components/ui/BaseDialog.vue'

const emit = defineEmits<{ close: [] }>()

const router = useRouter()
const appsStore = useApplicationsStore()
const resumesStore = useResumesStore()

const jobDescription = ref('')
const isSubmitting = ref(false)
const error = ref<string | null>(null)

async function submit() {
  if (!jobDescription.value.trim()) return

  const resumeId = resumesStore.selectedResumeId
  if (!resumeId) {
    error.value = 'Select a base resume in the sidebar first.'
    return
  }

  isSubmitting.value = true
  error.value = null

  try {
    const app = await appsStore.create(jobDescription.value.trim(), resumeId)
    emit('close')
    router.push({ name: 'application', params: { id: app.id } })
  } catch (e) {
    error.value = e instanceof Error ? e.message : 'Something went wrong'
  } finally {
    isSubmitting.value = false
  }
}
</script>

<template>
  <BaseDialog
    :open="true"
    width="min(640px, calc(100vw - 48px))"
    padding="28px 32px"
    gap="16px"
    @update:open="(v) => !v && emit('close')"
  >
    <DialogTitle class="modal-title">New Application</DialogTitle>

    <p class="modal-description">
      Paste the job description from LinkedIn or any job board. The AI will extract
      the company, role, and required skills automatically.
    </p>

    <textarea
      v-model="jobDescription"
      class="jd-textarea"
      placeholder="Paste the full job description here…"
      rows="12"
      :disabled="isSubmitting"
      autofocus
    />

    <p v-if="error" class="modal-error">{{ error }}</p>

    <div class="modal-actions">
      <DialogClose as-child>
        <BaseButton variant="secondary" :disabled="isSubmitting">Cancel</BaseButton>
      </DialogClose>
      <BaseButton
        variant="primary"
        :disabled="isSubmitting || !jobDescription.trim()"
        @click="submit"
      >
        {{ isSubmitting ? 'Creating…' : 'Analyze & Create' }}
      </BaseButton>
    </div>
  </BaseDialog>
</template>

<style lang="scss" scoped>

.modal-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--color-text);
}

.modal-description {
  font-size: 13px;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.jd-textarea {
  width: 100%;
  resize: vertical;
  padding: 10px 12px;
  font-family: var(--font-sans);
  font-size: 13px;
  line-height: 1.6;
  color: var(--color-text);
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  outline: none;

  &:focus {
    border-color: var(--color-primary);
    background: var(--color-surface);
  }

  &:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
}

.modal-error {
  font-size: 12px;
  color: var(--color-danger);
}

.modal-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
}


</style>
