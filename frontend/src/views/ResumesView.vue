<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { useResumesStore, type Resume } from "@/stores/resumes";
import { useFileUpload } from "@/composables/useFileUpload";
import BaseDialog from "@/components/ui/BaseDialog.vue";
import BaseTable from "@/components/ui/BaseTable.vue";
import CoachingStatusChip from "@/components/ui/CoachingStatusChip.vue";
import InlineEditForm from "@/components/ui/InlineEditForm.vue";
import TitleBar from "@/components/ui/TitleBar.vue";
import ResumeActionsMenu from "@/components/ResumeActionsMenu.vue";

const router = useRouter();
const resumesStore = useResumesStore();

// --- Upload ---
const { fileInput, isUploading, uploadError, triggerUpload, onFileSelected } = useFileUpload(
  async (body) => {
    if (body?.id) {
      resumesStore.selectedResumeId = body.id;
      router.push({ name: "resume-detail", params: { id: body.id } });
    }
  },
);

// --- Download ---
const downloadingId = ref<string | null>(null);
const deleteError = ref<string | null>(null);

async function downloadResume(resume: Resume) {
  downloadingId.value = resume.id;
  try {
    await resumesStore.downloadResume(resume.id, resume.file_name);
  } finally {
    downloadingId.value = null;
  }
}

// --- Delete ---
const deletingId = ref<string | null>(null);
const resumeToDelete = ref<Resume | null>(null);

function promptDelete(resume: Resume) {
  resumeToDelete.value = resume;
}

async function confirmDelete() {
  if (!resumeToDelete.value) return;
  const id = resumeToDelete.value.id;
  deletingId.value = id;
  deleteError.value = null;
  resumeToDelete.value = null;
  try {
    await resumesStore.deleteResume(id);
  } catch {
    deleteError.value = "Failed to delete. Please try again.";
  } finally {
    deletingId.value = null;
  }
}

// --- Rename ---
const renamingId = ref<string | null>(null);
const renameValue = ref("");
const renameError = ref<string | null>(null);

function startRename(resume: Resume) {
  renamingId.value = resume.id;
  renameValue.value = resume.file_name;
  renameError.value = null;
}

function cancelRename() {
  renamingId.value = null;
  renameError.value = null;
}

async function submitRename(id: string) {
  const name = renameValue.value.trim();
  if (!name) return;
  renameError.value = null;
  try {
    await resumesStore.renameResume(id, name);
    renamingId.value = null;
  } catch {
    renameError.value = "Failed to rename. Please try again.";
  }
}
</script>

<template>
  <div class="resumes-page">
    <TitleBar
      title="Resumes"
      :action-label="isUploading ? 'Uploading…' : 'Upload resume'"
      :action-disabled="isUploading"
      @action="triggerUpload"
    />

    <div class="resumes-content">
    <input
      :ref="(el) => (fileInput = el as HTMLInputElement | null)"
      type="file"
      accept=".docx"
      class="file-input-hidden"
      @change="onFileSelected"
    />

    <p v-if="uploadError || deleteError" class="error-banner">{{ uploadError ?? deleteError }}</p>

    <div v-if="!resumesStore.baseResumes.length" class="empty-state">No resumes uploaded yet.</div>

    <BaseTable v-else class="resume-table">
      <thead>
        <tr>
          <th>File name</th>
          <th>Version</th>
          <th>Uploaded</th>
          <th>Coaching</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="resume in resumesStore.baseResumes"
          :key="resume.id"
          :class="{ 'row--busy': deletingId === resume.id || downloadingId === resume.id }"
        >
          <td class="cell-name">
            <InlineEditForm
              v-if="renamingId === resume.id"
              v-model="renameValue"
              :error="renameError"
              @submit="submitRename(resume.id)"
              @cancel="cancelRename"
            />
            <RouterLink
              v-else
              class="file-name file-name--link"
              :to="{ name: 'resume-detail', params: { id: resume.id } }"
            >
              {{ resume.file_name }}
            </RouterLink>
          </td>
          <td class="cell-meta">v{{ resume.version_number }}</td>
          <td class="cell-meta">{{ new Date(resume.created_at).toLocaleDateString() }}</td>
          <td class="cell-coaching">
            <CoachingStatusChip :status="resume.coaching_status" compact />
          </td>
          <td class="cell-actions">
            <ResumeActionsMenu
              :resume="resume"
              @download="downloadResume(resume)"
              @rename="startRename(resume)"
              @delete="promptDelete(resume)"
            />
          </td>
        </tr>
      </tbody>
    </BaseTable>
    </div>
  </div>

  <BaseDialog
    :open="!!resumeToDelete"
    title="Delete resume"
    action-label="Delete"
    action-variant="danger"
    close-label="Cancel"
    @update:open="(v) => { if (!v) resumeToDelete = null; }"
    @action="confirmDelete"
  >
    <p class="dialog-body">
      Are you sure you want to delete <strong>{{ resumeToDelete?.file_name }}</strong>?
      <br />
      The underlying file will be kept to preserve any existing applications that depend on it.
    </p>
  </BaseDialog>
</template>

<style lang="scss" scoped>
.resumes-page {
  display: flex;
  flex-direction: column;
}

.resumes-content {
  padding: 32px 40px;

  @media (max-width: 640px) {
    padding: 20px 16px;
  }
}

.file-input-hidden {
  display: none;
}

.dialog-body {
  font-size: 14px;
  color: var(--color-text-muted);
  line-height: 1.5;

  strong {
    color: var(--color-text);
  }
}

.empty-state {
  font-size: 14px;
  color: var(--color-text-muted);
}

.error-banner {
  font-size: 13px;
  color: var(--color-danger);
  margin-bottom: 12px;
}

.resume-table {
  :deep(tr.row--busy) {
    opacity: 0.4;
    pointer-events: none;
  }
}

.cell-name {
  width: 100%;
}

.file-name {
  color: var(--color-text);
  font-weight: 500;

  &--link {
    color: var(--color-text);
    text-decoration: none;

    &:hover {
      color: var(--color-primary);
      text-decoration: underline;
    }
  }
}

.cell-coaching {
  white-space: nowrap;
}

.cell-meta {
  white-space: nowrap;
  color: var(--color-text-muted);
}

.cell-actions {
  white-space: nowrap;
}
</style>
