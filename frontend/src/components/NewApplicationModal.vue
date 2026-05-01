<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { DialogClose, DialogContent, DialogOverlay, DialogPortal, DialogRoot, DialogTitle } from 'radix-vue'
import { useApplicationsStore } from '@/stores/applications'
import { useResumesStore } from '@/stores/resumes'

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
  <DialogRoot :open="true" @update:open="(v) => !v && emit('close')">
    <DialogPortal>
      <DialogOverlay class="modal-overlay" />
      <DialogContent class="modal-content">
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
            <button class="btn-cancel" :disabled="isSubmitting">Cancel</button>
          </DialogClose>
          <button
            class="btn-submit"
            :disabled="isSubmitting || !jobDescription.trim()"
            @click="submit"
          >
            {{ isSubmitting ? 'Creating…' : 'Analyze & Create' }}
          </button>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style lang="scss" scoped>
.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 300;
  animation: fadeIn 0.15s ease;
}

.modal-content {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 310;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.15);
  padding: 28px 32px;
  width: min(640px, calc(100vw - 48px));
  display: flex;
  flex-direction: column;
  gap: 16px;
  animation: slideIn 0.15s ease;
}

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

.btn-cancel {
  padding: 8px 16px;
  background: none;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
  cursor: pointer;

  &:hover:not(:disabled) {
    background: var(--color-bg-subtle);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn-submit {
  padding: 8px 18px;
  background: var(--color-primary);
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  color: #fff;
  cursor: pointer;

  &:hover:not(:disabled) {
    background: var(--color-primary-hover);
  }

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

@keyframes fadeIn {
  from { opacity: 0 }
  to   { opacity: 1 }
}

@keyframes slideIn {
  from { opacity: 0; transform: translate(-50%, -48%) }
  to   { opacity: 1; transform: translate(-50%, -50%) }
}
</style>
