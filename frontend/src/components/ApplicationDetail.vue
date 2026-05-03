<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { type CoverLetter, PipelineStatus, useApplicationsStore } from "@/stores/applications";
import ApplicationActionsMenu from "@/components/ApplicationActionsMenu.vue";
import ResumeViewer from "@/components/ResumeViewer.vue";
import SkillsTable from "@/components/SkillsTable.vue";
import { getAppTitle } from "@/utils/application";
import StatusBadge from "@/components/ui/StatusBadge.vue";
import BaseDialog from "@/components/ui/BaseDialog.vue";
import Spinner from "@/components/ui/Spinner.vue";

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
  coverLetter.value = null;
  isGeneratingCL.value = false;
  await store.fetchOne(id);

  if (!store.current) return;

  const terminal = new Set([
    PipelineStatus.READY,
    PipelineStatus.FAILED,
    PipelineStatus.PENDING_APPROVAL,
  ]);
  store.fetchCoverLetter(id).then((cl) => { coverLetter.value = cl }).catch(() => {});

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
const isGeneratingCL = ref(false);
const clJustGenerated = ref(false);
const showDeleteConfirm = ref(false);
const showJdModal = ref(false);
const showCLModal = ref(false);
const coverLetter = ref<CoverLetter | null>(null);
const copied = ref(false);
const jobDescription = computed(
  () => store.current?.job_description.replace(/\n{3,}/g, "\n\n").trim() ?? "",
);

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

async function generateCoverLetter() {
  const id = route.params.id as string;
  isGeneratingCL.value = true;
  try {
    coverLetter.value = await store.generateCoverLetter(id);
    clJustGenerated.value = true;
    setTimeout(() => { clJustGenerated.value = false; }, 2500);
  } finally {
    isGeneratingCL.value = false;
  }
}

async function copyToClipboard() {
  if (!coverLetter.value) return;
  await navigator.clipboard.writeText(coverLetter.value.content);
  copied.value = true;
  setTimeout(() => { copied.value = false; }, 2000);
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
          <StatusBadge :status="store.current.status" />
          <Transition name="cl-indicator">
            <Spinner v-if="isGeneratingCL" :size="14" class="cl-indicator" />
            <svg
              v-else-if="clJustGenerated"
              class="cl-indicator cl-indicator--done"
              width="14"
              height="14"
              viewBox="0 0 14 14"
              fill="none"
              aria-hidden="true"
            >
              <circle cx="7" cy="7" r="6" stroke="currentColor" stroke-width="1.5" />
              <path d="M4.5 7l2 2 3-3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
            </svg>
          </Transition>
          <ApplicationActionsMenu
            :status="store.current.status"
            :has-feedback="!!store.current.analysis_feedback"
            :cover-letter="coverLetter"
            :is-retrying="isRetrying"
            :is-deleting="isDeleting"
            :is-generating-c-l="isGeneratingCL"
            @view-jd="showJdModal = true"
            @view-cover-letter="showCLModal = true"
            @generate-cover-letter="generateCoverLetter"
            @retry="retry"
            @delete="showDeleteConfirm = true"
          />
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

  <BaseDialog
    :open="showCLModal"
    title="Cover Letter"
    width="min(700px, calc(100vw - 32px))"
    max-height="80vh"
    :action-label="copied ? 'Copied!' : 'Copy'"
    @update:open="showCLModal = $event"
    @action="copyToClipboard"
  >
    <div class="jd-body">{{ coverLetter?.content }}</div>
    <div v-if="coverLetter?.questions?.length" class="cl-questions">
      <p class="cl-questions__label">To personalise further:</p>
      <ol class="cl-questions__list">
        <li v-for="(q, i) in coverLetter.questions" :key="i">{{ q }}</li>
      </ol>
    </div>
  </BaseDialog>

  <BaseDialog
    :open="showJdModal"
    title="Job Description"
    width="min(940px, calc(100vw - 32px))"
    max-height="80vh"
    @update:open="showJdModal = $event"
  >
    <div class="jd-body">{{ jobDescription }}</div>
  </BaseDialog>

  <BaseDialog
    title="Delete application?"
    :open="showDeleteConfirm"
    close-label="Cancel"
    :action-label="isDeleting ? 'Deleting…' : 'Delete'"
    action-variant="danger"
    :action-disabled="isDeleting"
    @update:open="showDeleteConfirm = $event"
    @action="deleteApp"
  >
    <p class="dialog-body">This cannot be undone.</p>
  </BaseDialog>
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
  flex: 1 1 60%;
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

.cl-indicator {
  color: var(--color-text-muted);
  flex-shrink: 0;

  &--done {
    color: var(--color-success, #22c55e);
  }
}

.cl-indicator-enter-active,
.cl-indicator-leave-active {
  transition: opacity 0.2s ease;
}

.cl-indicator-enter-from,
.cl-indicator-leave-to {
  opacity: 0;
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

.jd-body {
  font-size: 13px;
  color: var(--color-text);
  white-space: pre-wrap;
  line-height: 1.6;
  overflow-y: auto;
  flex: 1;
  min-height: 0;
  margin: 0 5px 0 0;
  padding: 12px 14px;
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-family: inherit;
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

.cl-questions {
  padding: 12px 14px;
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  font-size: 12px;

  &__label {
    font-weight: 600;
    color: var(--color-text-muted);
    margin: 0 0 8px;
    text-transform: uppercase;
    letter-spacing: 0.05em;
    font-size: 11px;
  }

  &__list {
    margin: 0;
    padding-left: 16px;
    display: flex;
    flex-direction: column;
    gap: 6px;
    color: var(--color-text);
    line-height: 1.5;
  }
}
</style>

