<script setup lang="ts">
import { ref, useTemplateRef, watch } from "vue";
import { useResumesStore, type Resume } from "@/stores/resumes";

const resumesStore = useResumesStore();

// --- Upload ---
const fileInput = useTemplateRef<HTMLInputElement>("fileInput");
const isUploading = ref(false);
const uploadError = ref<string | null>(null);

function triggerUpload() {
  uploadError.value = null;
  fileInput.value?.click();
}

async function onFileSelected(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0];
  if (!file) return;
  isUploading.value = true;
  uploadError.value = null;
  const form = new FormData();
  form.append("file", file);
  try {
    const res = await fetch("/api/resumes/", { method: "POST", credentials: "include", body: form });
    const body = await res.json().catch(() => ({}));
    if (!res.ok) { uploadError.value = body.detail ?? "Upload failed"; return; }
    await resumesStore.fetchAll();
    if (body?.id) resumesStore.selectedResumeId = body.id;
  } catch {
    uploadError.value = "Network error — try again";
  } finally {
    isUploading.value = false;
    if (fileInput.value) fileInput.value.value = "";
  }
}

// --- 3-dot menu ---
const openMenuId = ref<string | null>(null);

function toggleMenu(id: string) {
  openMenuId.value = openMenuId.value === id ? null : id;
}

function onClickOutside(e: MouseEvent) {
  const target = e.target as HTMLElement;
  if (!target.closest(".row-menu")) openMenuId.value = null;
}

watch(openMenuId, (id) => {
  if (id) document.addEventListener("mousedown", onClickOutside);
  else document.removeEventListener("mousedown", onClickOutside);
});

// --- Delete ---
const deletingId = ref<string | null>(null);
const deleteError = ref<string | null>(null);

async function confirmDelete(resume: Resume) {
  openMenuId.value = null;
  if (!confirm(`Delete "${resume.file_name}"? This cannot be undone.`)) return;
  deletingId.value = resume.id;
  deleteError.value = null;
  try {
    await resumesStore.deleteResume(resume.id);
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
const renameInput = ref<HTMLInputElement | null>(null);

function startRename(resume: Resume) {
  openMenuId.value = null;
  renamingId.value = resume.id;
  renameValue.value = resume.file_name;
  renameError.value = null;
  // focus input on next tick
  setTimeout(() => renameInput.value?.select(), 30);
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
    <header class="detail-header">
      <div class="detail-title">
        <h1>Manage Resumes</h1>
      </div>
      <button class="btn-upload" :disabled="isUploading" @click="triggerUpload">
        {{ isUploading ? "Uploading…" : "+ Upload resume" }}
      </button>
    </header>
    <input ref="fileInput" type="file" accept=".docx" class="file-input-hidden" @change="onFileSelected" />

    <p v-if="uploadError || deleteError" class="error-banner">{{ uploadError ?? deleteError }}</p>

    <div v-if="!resumesStore.baseResumes.length" class="empty-state">
      No resumes uploaded yet.
    </div>

    <table v-else class="resume-table">
      <thead>
        <tr>
          <th>File name</th>
          <th>Version</th>
          <th>Uploaded</th>
          <th></th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="resume in resumesStore.baseResumes"
          :key="resume.id"
          :class="{ 'row--deleting': deletingId === resume.id }"
        >
          <td class="cell-name">
            <template v-if="renamingId === resume.id">
              <form class="rename-form" @submit.prevent="submitRename(resume.id)">
                <input
                  ref="renameInput"
                  v-model="renameValue"
                  class="rename-input"
                  @keydown.esc="cancelRename"
                />
                <button type="submit" class="rename-btn rename-btn--save">Save</button>
                <button type="button" class="rename-btn rename-btn--cancel" @click="cancelRename">Cancel</button>
              </form>
              <p v-if="renameError" class="rename-error">{{ renameError }}</p>
            </template>
            <span v-else class="file-name">{{ resume.file_name }}</span>
          </td>
          <td class="cell-meta">v{{ resume.version_number }}</td>
          <td class="cell-meta">{{ new Date(resume.created_at).toLocaleDateString() }}</td>
          <td class="cell-actions">
            <div class="row-menu">
              <button
                class="menu-trigger"
                :aria-label="`Actions for ${resume.file_name}`"
                @click="toggleMenu(resume.id)"
              >
                <svg width="14" height="14" viewBox="0 0 15 15" fill="none" aria-hidden="true">
                  <circle cx="7.5" cy="2.5" r="1.25" fill="currentColor" />
                  <circle cx="7.5" cy="7.5" r="1.25" fill="currentColor" />
                  <circle cx="7.5" cy="12.5" r="1.25" fill="currentColor" />
                </svg>
              </button>
              <div v-if="openMenuId === resume.id" class="menu-dropdown">
                <button class="menu-item" @click="startRename(resume)">
                  <svg width="13" height="13" viewBox="0 0 15 15" fill="none" aria-hidden="true">
                    <path d="M11.854 2.146a.5.5 0 0 0-.707 0L4.5 8.793V10.5h1.707l6.647-6.646a.5.5 0 0 0 0-.708l-1-1ZM3.5 9.207 10.5 2.207l.293.293-7 7H3.5v-.293Z" fill="currentColor"/>
                  </svg>
                  Rename
                </button>
                <button class="menu-item menu-item--danger" @click="confirmDelete(resume)">
                  <svg width="13" height="13" viewBox="0 0 15 15" fill="none" aria-hidden="true">
                    <path d="M5.5 1a.5.5 0 0 0 0 1h4a.5.5 0 0 0 0-1h-4ZM3 3.5a.5.5 0 0 1 .5-.5h8a.5.5 0 0 1 0 1H11v8a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1v-8h-.5a.5.5 0 0 1-.5-.5ZM5 4v8h5V4H5Z" fill="currentColor"/>
                  </svg>
                  Delete
                </button>
              </div>
            </div>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style lang="scss" scoped>
.resumes-page {
  padding: 32px 40px;

  @media (max-width: 640px) {
    padding: 20px 16px;
  }
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;
}

.detail-title h1 {
  font-size: 20px;
  font-weight: 600;
  color: var(--color-text);
  line-height: 1.2;
}

.file-input-hidden { display: none; }

.btn-upload {
  padding: 7px 14px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  white-space: nowrap;
  flex-shrink: 0;

  &:hover:not(:disabled) { background: var(--color-primary-hover); }
  &:disabled { opacity: 0.6; cursor: not-allowed; }
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
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;

  th {
    text-align: left;
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    color: var(--color-text-muted);
    padding: 0 12px 8px;
    border-bottom: 1px solid var(--color-border);

    &:first-child { padding-left: 0; }
    &:last-child { padding-right: 0; }
  }

  td {
    padding: 10px 12px;
    border-bottom: 1px solid var(--color-border);
    vertical-align: middle;

    &:first-child { padding-left: 0; }
    &:last-child { padding-right: 0; }
  }

  tr:last-child td { border-bottom: none; }

  tr.row--deleting { opacity: 0.4; pointer-events: none; }
}

.cell-name { width: 100%; }

.file-name {
  color: var(--color-text);
  font-weight: 500;
}

.cell-meta {
  white-space: nowrap;
  color: var(--color-text-muted);
}

.cell-actions {
  white-space: nowrap;
}

// Rename inline form
.rename-form {
  display: flex;
  align-items: center;
  gap: 6px;
}

.rename-input {
  flex: 1;
  padding: 4px 8px;
  font-size: 13px;
  border: 1px solid var(--color-primary);
  border-radius: var(--radius);
  background: var(--color-surface);
  color: var(--color-text);
  outline: none;
}

.rename-btn {
  padding: 4px 8px;
  font-size: 12px;
  border-radius: var(--radius);
  border: none;
  cursor: pointer;

  &--save {
    background: var(--color-primary);
    color: #fff;
    &:hover { background: var(--color-primary-hover); }
  }

  &--cancel {
    background: var(--color-border);
    color: var(--color-text);
    &:hover { background: var(--color-text-muted); color: #fff; }
  }
}

.rename-error {
  font-size: 11px;
  color: var(--color-danger);
  margin-top: 3px;
}

// Row 3-dot menu
.row-menu {
  position: relative;
  display: flex;
  justify-content: flex-end;
}

.menu-trigger {
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px 6px;
  border-radius: var(--radius);
  color: var(--color-text-muted);
  display: flex;
  align-items: center;

  &:hover {
    background: var(--color-border);
    color: var(--color-text);
  }
}

.menu-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  padding: 4px;
  min-width: 130px;
  z-index: 100;
}

.menu-item {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  background: none;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text);
  text-align: left;

  &:hover { background: var(--color-bg-subtle); }

  &--danger {
    color: var(--color-danger);
    &:hover { background: color-mix(in srgb, var(--color-danger) 10%, transparent); }
  }
}
</style>
