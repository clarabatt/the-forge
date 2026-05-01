<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  DialogClose,
  DialogContent,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "radix-vue";
import { PipelineStatus, useApplicationsStore } from "@/stores/applications";
import ResumeViewer from "@/components/ResumeViewer.vue";
import SkillsTable from "@/components/SkillsTable.vue";
import { getAppTitle } from "@/utils/application";

const route = useRoute();
const router = useRouter();
const store = useApplicationsStore();

let eventSource: EventSource | null = null;

function closeSSE() {
  eventSource?.close();
  eventSource = null;
}

async function load(id: string) {
  closeSSE();
  await store.fetchOne(id);

  if (!store.current) return;

  const terminal = new Set([
    PipelineStatus.READY,
    PipelineStatus.FAILED,
    PipelineStatus.PENDING_APPROVAL,
  ]);
  if (terminal.has(store.current.status)) return;

  eventSource = store.subscribeToStatus(id, async (event: MessageEvent) => {
    const data = JSON.parse(event.data);
    if (store.current?.id === id) {
      store.current.status = data.status;
      if (data.company_name) store.current.company_name = data.company_name;
      if (data.job_title) store.current.job_title = data.job_title;
    }
    const inList = store.applications.find((a) => a.id === id);
    if (inList) {
      inList.status = data.status;
      if (data.company_name) inList.company_name = data.company_name;
      if (data.job_title) inList.job_title = data.job_title;
    }
    if (terminal.has(data.status)) {
      closeSSE();
      await store.fetchOne(id);
    }
  });
}

const isRetrying = ref(false);
const isDeleting = ref(false);
const isDownloading = ref(false);
const showDeleteConfirm = ref(false);
const showJdModal = ref(false);

async function download(format: "docx" | "pdf") {
  const id = route.params.id as string;
  isDownloading.value = true;
  try {
    await store.downloadResume(id, format);
  } finally {
    isDownloading.value = false;
  }
}

async function retry() {
  const id = route.params.id as string;
  isRetrying.value = true;
  try {
    await store.retry(id);
    await load(id);
  } finally {
    isRetrying.value = false;
  }
}

async function deleteApp() {
  const id = route.params.id as string;
  const next = store.applications.find((a) => a.id !== id);
  isDeleting.value = true;
  showDeleteConfirm.value = false;
  try {
    await store.deleteApplication(id);
    if (next) {
      await router.push({ name: "application", params: { id: next.id } });
    } else {
      await router.push("/");
    }
  } finally {
    isDeleting.value = false;
  }
}

onMounted(() => load(route.params.id as string));
watch(
  () => route.params.id,
  (id) => id && load(id as string),
);
onUnmounted(closeSSE);
</script>

<template>
  <div class="application-detail">
    <div v-if="!store.current" class="detail-empty">Loading…</div>
    <template v-else>
      <header class="detail-header">
        <div class="detail-title">
          <h1>{{ getAppTitle(store.current) }}</h1>
          <span class="detail-role">{{ store.current.job_title }}</span>
        </div>
        <div class="header-right">
          <span class="badge" :class="`badge--${store.current.status.toLowerCase()}`">
            {{ store.current.status.replace(/_/g, " ") }}
          </span>
          <DropdownMenuRoot>
            <DropdownMenuTrigger class="menu-trigger" aria-label="Application actions">
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="currentColor"
                aria-hidden="true"
              >
                <circle cx="8" cy="3" r="1.25" />
                <circle cx="8" cy="8" r="1.25" />
                <circle cx="8" cy="13" r="1.25" />
              </svg>
            </DropdownMenuTrigger>
            <DropdownMenuPortal>
              <DropdownMenuContent class="menu-content" :side-offset="4" align="end">
                <DropdownMenuItem class="menu-item" @select="showJdModal = true">
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                    <rect x="2" y="1" width="8" height="10" rx="1" stroke="currentColor" stroke-width="1.5" />
                    <path d="M4 4h4M4 6.5h4M4 9h2.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
                  </svg>
                  View job description
                </DropdownMenuItem>
                <DropdownMenuSeparator class="menu-separator" />
                <DropdownMenuItem
                  class="menu-item"
                  :disabled="store.current.status !== PipelineStatus.FAILED || isRetrying"
                  @select="retry"
                >
                  <svg width="12" height="12" viewBox="-2 -2 14 14" fill="none" aria-hidden="true">
                    <path
                      d="M10.5 2A5.5 5.5 0 1 0 11 6.5"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                    />
                    <path
                      d="M8.5 2H10.5V0"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  Retry
                </DropdownMenuItem>
                <DropdownMenuSeparator class="menu-separator" />
                <DropdownMenuItem
                  class="menu-item menu-item--danger"
                  :disabled="isDeleting"
                  @select="showDeleteConfirm = true"
                >
                  <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                    <path
                      d="M1.5 3h9M4.5 3V1.5h3V3M5 5.5v3M7 5.5v3M2.5 3l.5 7h6l.5-7"
                      stroke="currentColor"
                      stroke-width="1.5"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    />
                  </svg>
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenuPortal>
          </DropdownMenuRoot>
        </div>
      </header>

      <!-- pipeline in-progress state -->
      <div
        v-if="[PipelineStatus.UPLOADED, PipelineStatus.ANALYZING].includes(store.current.status)"
        class="pipeline-progress"
      >
        <div class="spinner" />
        <p>
          {{
            store.current.status === PipelineStatus.ANALYZING
              ? "Analyzing job description and resume…"
              : "Starting…"
          }}
        </p>
      </div>

      <div v-else-if="store.current.status === PipelineStatus.FAILED" class="pipeline-error">
        <p>Pipeline failed. Please try again.</p>
      </div>

      <template v-else>
        <div class="detail-actions">
          <div class="btn-group">
            <button class="btn-group__btn" :disabled="isDownloading" @click="download('docx')">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path
                  d="M6.5 1v8M3.5 6l3 3 3-3"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M1.5 10.5v1h10v-1"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              DOCX
            </button>
            <div class="btn-group__divider" />
            <button class="btn-group__btn" :disabled="isDownloading" @click="download('pdf')">
              <svg width="13" height="13" viewBox="0 0 13 13" fill="none" aria-hidden="true">
                <path
                  d="M6.5 1v8M3.5 6l3 3 3-3"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
                <path
                  d="M1.5 10.5v1h10v-1"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
              PDF
            </button>
          </div>
        </div>
        <div class="content-grid">
          <div class="content-main">
            <ResumeViewer :application-id="store.current.id" />
          </div>
          <aside class="content-sidebar">
            <SkillsTable :application-id="store.current.id" />
          </aside>
        </div>
      </template>
    </template>
  </div>

  <DialogRoot :open="showJdModal" @update:open="showJdModal = $event">
    <DialogPortal>
      <DialogOverlay class="dialog-overlay" />
      <DialogContent class="dialog-content jd-dialog-content">
        <DialogTitle class="dialog-title">Job Description</DialogTitle>
        <div class="jd-body">{{ store.current?.job_description }}</div>
        <div class="dialog-actions">
          <DialogClose class="btn-cancel">Close</DialogClose>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>

  <DialogRoot :open="showDeleteConfirm" @update:open="showDeleteConfirm = $event">
    <DialogPortal>
      <DialogOverlay class="dialog-overlay" />
      <DialogContent class="dialog-content">
        <DialogTitle class="dialog-title">Delete application?</DialogTitle>
        <p class="dialog-body">This cannot be undone.</p>
        <div class="dialog-actions">
          <DialogClose class="btn-cancel">Cancel</DialogClose>
          <button class="btn-delete" :disabled="isDeleting" @click="deleteApp">
            {{ isDeleting ? "Deleting…" : "Delete" }}
          </button>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style lang="scss" scoped>
.application-detail {
  padding: 32px 40px;

  @media (max-width: 640px) {
    padding: 20px 16px;
  }
}

.content-grid {
  display: flex;
  flex-direction: row;
  gap: 46px;
  align-items: start;
  justify-content: start;

  @media (max-width: 960px) {
    flex-direction: column;

    .content-sidebar {
      order: -1;
      width: 100%;
    }
  }
}

.content-main {
  min-width: 0;
}

.content-sidebar {
  min-width: 0;
  width: 40%;
}

.detail-empty {
  color: var(--color-text-muted);
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 20px;
  gap: 16px;

  @media (max-width: 640px) {
    flex-wrap: wrap;
    gap: 10px;
  }
}

.detail-title {
  display: flex;
  flex-direction: column;
  gap: 3px;

  h1 {
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text);
    line-height: 1.2;
  }
}

.detail-role {
  font-size: 14px;
  color: var(--color-text-muted);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-top: 3px;
}

.badge {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 99px;
  background: var(--color-bg-subtle);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  white-space: nowrap;

  &--ready {
    color: var(--color-success);
    border-color: var(--color-success);
  }
  &--failed {
    color: var(--color-danger);
    border-color: var(--color-danger);
  }
  &--pending_approval,
  &--pending_retry {
    color: var(--color-warning);
    border-color: var(--color-warning);
  }
  &--analyzing,
  &--tailoring,
  &--validating,
  &--uploaded {
    color: var(--color-primary);
    border-color: var(--color-primary);
  }
}

.menu-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: var(--radius);
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;

  &:hover {
    background: var(--color-border);
    color: var(--color-text);
  }

  &[data-state="open"] {
    background: var(--color-border);
    color: var(--color-text);
  }
}

.menu-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  padding: 4px;
  min-width: 140px;
  z-index: 50;
}

.menu-separator {
  height: 1px;
  background: var(--color-border);
  margin: 4px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  font-size: 13px;
  border-radius: var(--radius);
  cursor: pointer;
  outline: none;
  color: var(--color-text);
  user-select: none;

  &[data-highlighted] {
    background: var(--color-bg-subtle);
  }

  &[data-disabled] {
    opacity: 0.4;
    cursor: default;
    pointer-events: none;
  }

  &--danger {
    color: var(--color-danger);

    &[data-highlighted] {
      background: color-mix(in srgb, var(--color-danger) 10%, transparent);
    }
  }
}

.pipeline-progress {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 0;
  color: var(--color-text-muted);
  font-size: 13px;
}

.spinner {
  width: 18px;
  height: 18px;
  border: 2px solid var(--color-border);
  border-top-color: var(--color-primary);
  border-radius: 50%;
  animation: spin 0.75s linear infinite;
  flex-shrink: 0;
}

.pipeline-error {
  padding: 20px 0;
  color: var(--color-danger);
  font-size: 13px;
}

.detail-actions {
  margin-bottom: 24px;
}

.btn-group {
  display: inline-flex;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  overflow: hidden;

  &__btn {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    padding: 6px 14px;
    background: var(--color-surface);
    border: none;
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    color: var(--color-text);
    letter-spacing: 0.03em;

    &:hover:not(:disabled) {
      background: var(--color-bg-subtle);
    }
    &:disabled {
      opacity: 0.5;
      cursor: default;
    }
  }

  &__divider {
    width: 1px;
    background: var(--color-border);
    flex-shrink: 0;
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.jd-dialog-content {
  width: min(640px, calc(100vw - 32px));
  max-height: 80vh;
}

.jd-body {
  font-size: 13px;
  color: var(--color-text);
  white-space: pre-wrap;
  line-height: 1.6;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  margin: 0;
}

.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 100;
}

.dialog-content {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 101;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.16);
  padding: 24px;
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.dialog-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.dialog-body {
  font-size: 13px;
  color: var(--color-text-muted);
  margin: 0;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 8px;
}

.btn-cancel {
  padding: 6px 14px;
  font-size: 13px;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text);
  cursor: pointer;

  &:hover {
    background: var(--color-bg-subtle);
  }
}

.btn-delete {
  padding: 6px 14px;
  font-size: 13px;
  border-radius: var(--radius);
  border: none;
  background: var(--color-danger);
  color: #fff;
  cursor: pointer;

  &:hover:not(:disabled) {
    opacity: 0.88;
  }

  &:disabled {
    opacity: 0.5;
    cursor: default;
  }
}
</style>
