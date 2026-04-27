<script setup lang="ts">
import { onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuTrigger,
} from "radix-vue";
import { PipelineStatus, useApplicationsStore } from "@/stores/applications";
import ResumeViewer from "@/components/ResumeViewer.vue";
import { getAppTitle } from "@/utils/application";

const route = useRoute();
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

  eventSource = store.subscribeToStatus(id, (event: MessageEvent) => {
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
    if (terminal.has(data.status)) closeSSE();
  });
}

const isRetrying = ref(false);

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
              ? "Analyzing job description and résumé…"
              : "Starting…"
          }}
        </p>
      </div>

      <div v-else-if="store.current.status === PipelineStatus.FAILED" class="pipeline-error">
        <p>Pipeline failed. Please try again.</p>
      </div>

      <template v-else>
        <div class="detail-actions">
          <button class="btn-download">Download Resume</button>
        </div>
        <ResumeViewer :application-id="store.current.id" />
      </template>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.application-detail {
  padding: 32px 40px;
  max-width: 800px;
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

.btn-download {
  padding: 7px 14px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  color: var(--color-text);

  &:hover {
    background: var(--color-bg-subtle);
  }
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
