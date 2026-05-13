<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { useResumesStore, type Resume } from "@/stores/resumes";
import ResumeCoachingPanel from "@/components/ResumeCoachingPanel.vue";
import CoachingStatusChip from "@/components/ui/CoachingStatusChip.vue";

const route = useRoute();
const router = useRouter();
const resumesStore = useResumesStore();

const resume = ref<Resume | null>(null);
const html = ref<string | null>(null);
const isLoadingHtml = ref(false);
const error = ref<string | null>(null);

let pollTimer: ReturnType<typeof setTimeout> | null = null;

function stopPolling() {
  if (pollTimer) {
    clearTimeout(pollTimer);
    pollTimer = null;
  }
}

async function poll(id: string) {
  const updated = await resumesStore.fetchOne(id);
  if (!updated) return;
  resume.value = updated;
  if (updated.coaching_status === "analyzing") {
    pollTimer = setTimeout(() => poll(id), 3000);
  }
}

async function loadHtml(id: string) {
  isLoadingHtml.value = true;
  const result = await resumesStore.fetchHtml(id);
  html.value = result;
  isLoadingHtml.value = false;
}

async function load(id: string) {
  stopPolling();
  error.value = null;
  const r = await resumesStore.fetchOne(id);
  if (!r) {
    error.value = "Resume not found.";
    return;
  }
  resume.value = r;
  loadHtml(id);
  if (r.coaching_status === "analyzing") {
    pollTimer = setTimeout(() => poll(id), 3000);
  }
}

const analysis = computed(() =>
  resume.value ? resumesStore.getCoachingAnalysis(resume.value) : null,
);

onMounted(() => load(route.params.id as string));
watch(
  () => route.params.id,
  (id) => id && load(id as string),
);
onUnmounted(stopPolling);
</script>

<template>
  <div class="resume-detail">
    <div v-if="error" class="state-message state-message--error">{{ error }}</div>
    <div v-else-if="!resume" class="state-message">Loading…</div>
    <template v-else>
      <header class="detail-header">
        <div class="detail-title">
          <h1>{{ resume.file_name }}</h1>
          <nav class="breadcrumbs">
            <RouterLink class="breadcrumb-link" :to="{ name: 'resumes' }">Resumes</RouterLink>
            <span class="breadcrumb-sep">/</span>
            <span class="breadcrumb-current">{{ resume.file_name }}</span>
          </nav>
        </div>
        <div class="header-right">
          <CoachingStatusChip :status="resume.coaching_status" />
        </div>
      </header>

      <!-- Analyzing state -->
      <div v-if="resume.coaching_status === 'analyzing'" class="analyzing-banner">
        <Spinner :size="16" />
        <p>Analyzing your resume against STAR and XYZ frameworks…</p>
      </div>

      <!-- Failed state -->
      <div v-else-if="resume.coaching_status === 'failed'" class="failed-banner">
        <p>The coaching analysis failed. You can still download your resume.</p>
      </div>

      <!-- Content grid: coaching left, resume right -->
      <div v-else-if="resume.coaching_status === 'done' && analysis" class="content-grid">
        <div class="content-main">
          <div class="resume-paper">
            <div v-if="isLoadingHtml" class="resume-loading">
              <Spinner :size="32" />
            </div>
            <div v-else-if="!html" class="resume-error">Could not load preview.</div>
            <!-- eslint-disable-next-line vue/no-v-html -->
            <div v-else class="resume-body" v-html="html" />
          </div>
        </div>
        <aside class="content-sidebar">
          <ResumeCoachingPanel :analysis="analysis" />
        </aside>
      </div>

      <!-- Pending — no analysis yet but also not analyzing -->
      <div v-else class="state-message">No coaching analysis available for this resume.</div>
    </template>
  </div>
</template>

<style lang="scss" scoped>
.resume-detail {
  padding: 32px 40px;

  @media (max-width: 640px) {
    padding: 20px 16px;
  }
}

.state-message {
  font-size: 13px;
  color: var(--color-text-muted);

  &--error {
    color: var(--color-danger);
  }
}

.detail-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 16px;

  @media (max-width: 640px) {
    flex-wrap: wrap;
    gap: 10px;
  }
}

.detail-title {
  display: flex;
  flex-direction: column;
  gap: 4px;

  h1 {
    font-size: 20px;
    font-weight: 600;
    color: var(--color-text);
    line-height: 1.2;
  }
}

.breadcrumbs {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
}

.breadcrumb-link {
  color: var(--color-text-muted);
  text-decoration: none;

  &:hover {
    color: var(--color-primary);
    text-decoration: underline;
  }
}

.breadcrumb-sep {
  color: var(--color-border);
  user-select: none;
}

.breadcrumb-current {
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 240px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-top: 3px;
}

.analyzing-banner {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 20px 0;
  color: var(--color-text-muted);
  font-size: 13px;
}

.failed-banner {
  padding: 16px 0;
  font-size: 13px;
  color: var(--color-danger);
}

.content-grid {
  display: flex;
  flex-direction: row;
  gap: 40px;
  align-items: start;

  @media (max-width: 1024px) {
    flex-direction: column;

    .content-sidebar {
      width: 100%;
      order: 1;
    }

    .content-main {
      width: 100%;
      order: 2;
    }
  }
}

.content-sidebar {
  flex: 1;
  min-width: 0;
}

.content-main {
  width: 480px;
  flex-shrink: 0;
}

// Resume paper preview
.resume-paper {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  padding: 28px 32px;
  color: #111;
  font-family: "Georgia", "Times New Roman", serif;
  min-height: 400px;
}

.resume-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.resume-error {
  font-size: 13px;
  color: var(--color-text-muted);
  font-family: inherit;
}

.resume-body {
  :deep(p) {
    margin: 0 0 4px;
    font-size: 11pt;
    line-height: 1.5;
  }

  :deep(p:first-child strong) {
    font-size: 20pt;
    font-weight: 700;
    letter-spacing: -0.01em;
  }

  :deep(p:nth-child(2) strong) {
    font-size: 12pt;
    font-weight: 400;
    color: #444;
  }

  :deep(p:nth-child(3)) {
    font-size: 10pt;
    color: #555;
    margin-bottom: 18px;
  }

  :deep(p > strong:only-child) {
    display: block;
    font-size: 10pt;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-bottom: 1.5px solid #111;
    padding-bottom: 2px;
    margin-top: 16px;
    margin-bottom: 6px;
  }

  :deep(p strong) {
    font-weight: 600;
  }

  :deep(h3) {
    font-size: 10pt;
    font-weight: 400;
    font-style: italic;
    color: #555;
    margin: 0 0 4px;
  }

  :deep(h1) {
    font-size: 11pt;
    font-weight: 600;
    margin: 12px 0 0;
  }

  :deep(h2) {
    font-size: 10.5pt;
    font-weight: 400;
    margin: 0 0 8px;
  }

  :deep(ul) {
    margin: 4px 0 10px;
    padding-left: 18px;
  }

  :deep(li) {
    font-size: 10.5pt;
    line-height: 1.55;
    margin-bottom: 3px;
  }
}
</style>
