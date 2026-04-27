<script setup lang="ts">
import { computed, ref, useTemplateRef } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  SelectContent,
  SelectItem,
  SelectItemText,
  SelectPortal,
  SelectRoot,
  SelectTrigger,
  SelectValue,
  SelectViewport,
} from "radix-vue";
import { PipelineStatus, useApplicationsStore } from "@/stores/applications";
import { useResumesStore } from "@/stores/resumes";
import { useAuthStore } from "@/stores/auth";
import { getAppTitle } from "@/utils/application";

const emit = defineEmits<{ "new-application": [] }>();

const route = useRoute();
const router = useRouter();
const appsStore = useApplicationsStore();
const resumesStore = useResumesStore();
const authStore = useAuthStore();

const collapsed = ref(false);

const activeId = computed(() => route.params.id as string | undefined);

const hasNoBaseResumes = computed(() => !resumesStore.baseResumes?.length);

const selectedResumeId = computed({
  get: () => resumesStore.selectedResumeId ?? "",
  set: (v: string) => {
    resumesStore.selectedResumeId = v || null;
  },
});

const initials = computed(() => {
  const name = authStore.user?.full_name ?? "";
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((w) => w[0]!.toUpperCase())
    .join("");
});

const costDisplay = computed(() => {
  const u = authStore.usage;
  if (!u) return null;
  return {
    current: u.cost_usd.toFixed(2),
    cap: u.monthly_cap_usd.toFixed(2),
    pct: Math.min(100, (u.cost_usd / u.monthly_cap_usd) * 100),
  };
});

function selectApp(id: string) {
  router.push({ name: "application", params: { id } });
}

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
    const res = await fetch("/api/resumes/", {
      method: "POST",
      credentials: "include",
      body: form,
    });

    const body = await res.json().catch(() => ({}));

    if (!res.ok) {
      uploadError.value = body.detail ?? "Upload failed";
      return;
    }

    await resumesStore.fetchAll();
    if (body?.id) resumesStore.selectedResumeId = body.id;
  } catch {
    uploadError.value = "Network error — try again";
  } finally {
    isUploading.value = false;
    // reset so the same file can be re-selected if needed
    if (fileInput.value) fileInput.value.value = "";
  }
}

const statusColor: Record<PipelineStatus, string> = {
  [PipelineStatus.READY]: "var(--color-success)",
  [PipelineStatus.PENDING_APPROVAL]: "var(--color-warning)",
  [PipelineStatus.ANALYZING]: "var(--color-primary)",
  [PipelineStatus.TAILORING]: "var(--color-primary)",
  [PipelineStatus.VALIDATING]: "var(--color-primary)",
  [PipelineStatus.PENDING_RETRY]: "var(--color-warning)",
  [PipelineStatus.UPLOADED]: "var(--color-text-muted)",
  [PipelineStatus.FAILED]: "var(--color-danger)",
};
</script>

<template>
  <aside class="sidebar" :class="{ 'sidebar--collapsed': collapsed }">
    <!-- Header -->
    <div class="sidebar-header">
      <img v-if="!collapsed" src="/logo.png" alt="The Forge" class="sidebar-logo" />
      <button
        class="sidebar-toggle"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="collapsed = !collapsed"
      >
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="1" y="3" width="14" height="1.5" rx="0.75" fill="currentColor" />
          <rect x="1" y="7.25" width="14" height="1.5" rx="0.75" fill="currentColor" />
          <rect x="1" y="11.5" width="14" height="1.5" rx="0.75" fill="currentColor" />
        </svg>
      </button>
    </div>

    <!-- Scrollable body -->
    <div class="sidebar-body">
      <template v-if="!collapsed">
        <div class="sidebar-section">
          <p class="sidebar-label">Base Resume</p>
          <SelectRoot v-model="selectedResumeId">
            <SelectTrigger class="select-trigger" aria-label="Select base resume">
              <SelectValue placeholder="No resume" />
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
                <path
                  d="M3 4.5L6 7.5L9 4.5"
                  stroke="currentColor"
                  stroke-width="1.5"
                  stroke-linecap="round"
                  stroke-linejoin="round"
                />
              </svg>
            </SelectTrigger>
            <SelectPortal>
              <SelectContent class="select-content" position="popper" :side-offset="4">
                <SelectViewport>
                  <SelectItem
                    v-for="resume in resumesStore.baseResumes"
                    :key="resume.id"
                    :value="resume.id"
                    class="select-item"
                  >
                    <SelectItemText>{{ resume.file_name }}</SelectItemText>
                  </SelectItem>
                  <div v-if="hasNoBaseResumes" class="select-empty">No resumes found</div>
                </SelectViewport>
              </SelectContent>
            </SelectPortal>
          </SelectRoot>

          <input
            ref="fileInput"
            type="file"
            accept=".docx"
            class="file-input-hidden"
            @change="onFileSelected"
          />
          <button
            class="upload-link"
            :disabled="isUploading"
            :title="isUploading ? 'Uploading resume...' : 'Upload new resume'"
            @click="triggerUpload"
          >
            {{ isUploading ? "Uploading…" : "+ Upload new resume" }}
          </button>
          <p v-if="uploadError" class="upload-error">{{ uploadError }}</p>
        </div>

        <div class="sidebar-section">
          <button
            class="btn-new-app"
            :disabled="hasNoBaseResumes"
            :aria-label="
              hasNoBaseResumes ? 'Upload a resume to create an application' : 'New application'
            "
            :title="
              hasNoBaseResumes ? 'Upload a resume to create an application' : 'New application'
            "
            @click="emit('new-application')"
          >
            + New Application
          </button>
        </div>

        <div class="sidebar-section sidebar-section--apps">
          <p class="sidebar-label">Applications</p>
          <div v-if="appsStore.isLoading" class="sidebar-empty">Loading…</div>
          <div v-else-if="appsStore.applications.length === 0" class="sidebar-empty">
            No applications yet.
          </div>
          <ul v-else class="app-list">
            <li
              v-for="app in appsStore.applications"
              :key="app.id"
              class="app-item"
              :class="{ 'app-item--active': app.id === activeId }"
              @click="selectApp(app.id)"
            >
              <span
                class="app-dot"
                :style="{ background: statusColor[app.status] ?? 'var(--color-text-muted)' }"
              />
              <span class="app-label">
                <span class="app-company">{{ getAppTitle(app) }}</span>
                <span class="app-role">{{ app.job_title }}</span>
              </span>
            </li>
          </ul>
        </div>
      </template>

      <template v-else>
        <ul class="app-list app-list--icons">
          <li
            v-for="app in appsStore.applications"
            :key="app.id"
            class="app-item app-item--icon"
            :class="{ 'app-item--active': app.id === activeId }"
            :title="`${getAppTitle(app)}: ${app.job_title}`"
            @click="selectApp(app.id)"
          >
            <span
              class="app-dot app-dot--lg"
              :style="{ background: statusColor[app.status] ?? 'var(--color-text-muted)' }"
            />
          </li>
        </ul>
      </template>
    </div>

    <!-- Fixed footer -->
    <div class="sidebar-footer" :class="{ 'sidebar-footer--collapsed': collapsed }">
      <div class="avatar">
        <img
          v-if="authStore.user?.picture_url"
          :src="authStore.user.picture_url"
          :alt="authStore.user.full_name"
          class="avatar-img"
        />
        <span v-else class="avatar-initials">{{ initials }}</span>
      </div>

      <div v-if="!collapsed && costDisplay" class="footer-cost">
        <span class="cost-label">This month</span>
        <span class="cost-value">${{ costDisplay.current }} / ${{ costDisplay.cap }}</span>
        <div class="cost-bar">
          <div class="cost-bar-fill" :style="{ width: costDisplay.pct + '%' }" />
        </div>
      </div>
    </div>
  </aside>
</template>

<style lang="scss" scoped>
.sidebar {
  width: 240px;
  height: 100vh;
  background: var(--color-bg-subtle);
  border-right: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  transition: width 0.2s ease;

  &--collapsed {
    width: 56px;
  }
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 12px;
  min-height: 70px;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.sidebar-logo {
  height: 50px;
  width: auto;
  object-fit: contain;
  object-position: left center;
}

.sidebar-toggle {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-text-muted);
  padding: 6px;
  border-radius: var(--radius);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &:hover {
    background: var(--color-border);
    color: var(--color-text);
  }
}

.sidebar-body {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
}

.sidebar-section {
  padding: 16px;
  border-bottom: 1px solid var(--color-border);

  &--apps {
    border-bottom: none;
  }
}

.sidebar-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  margin-bottom: 8px;
}

.sidebar-empty {
  font-size: 13px;
  color: var(--color-text-muted);
}

// Select
.select-trigger {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 6px 10px;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  font-size: 13px;
  cursor: pointer;
  color: var(--color-text);
  gap: 4px;

  &:focus-visible {
    outline: 2px solid var(--color-primary);
    outline-offset: 1px;
  }
}

// Upload
.file-input-hidden {
  display: none;
}

.upload-link {
  margin-top: 6px;
  background: none;
  border: none;
  padding: 0;
  font-size: 12px;
  color: var(--color-primary);
  cursor: pointer;
  text-align: left;

  &:hover:not(:disabled) {
    text-decoration: underline;
  }

  &:disabled {
    color: var(--color-text-muted);
    cursor: default;
  }
}

.upload-error {
  margin-top: 4px;
  font-size: 11px;
  color: var(--color-danger);
}

// New app button
.btn-new-app {
  width: 100%;
  padding: 7px 12px;
  background: var(--color-primary);
  color: #fff;
  border: none;
  border-radius: var(--radius);
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  text-align: left;

  &:hover:not(:disabled) {
    background: var(--color-primary-hover);
  }

  &:disabled {
    background: var(--color-text-muted);
    cursor: not-allowed;
    opacity: 0.6;
  }
}

// App list
.app-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 2px;

  &--icons {
    padding: 12px 8px;
    align-items: center;
  }
}

.app-item {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 7px 8px;
  border-radius: var(--radius);
  cursor: pointer;

  &:hover {
    background: var(--color-border);
  }

  &--active {
    background: var(--color-border);
  }

  &--icon {
    justify-content: center;
    padding: 10px 8px;
  }
}

.app-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;
  margin-top: 4px;

  &--lg {
    width: 10px;
    height: 10px;
    margin-top: 0;
  }
}

.app-label {
  display: flex;
  flex-direction: column;
  min-width: 0;
}

.app-company {
  font-size: 13px;
  font-weight: 500;
  color: var(--color-text);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.app-role {
  font-size: 12px;
  color: var(--color-text-muted);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

// Footer
.sidebar-footer {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 16px;
  border-top: 1px solid var(--color-border);
  flex-shrink: 0;
  background: var(--color-bg-subtle);

  &--collapsed {
    justify-content: center;
    padding: 12px 8px;
  }
}

.avatar {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--color-primary);
  display: flex;
  align-items: center;
  justify-content: center;
}

.avatar-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.avatar-initials {
  font-size: 12px;
  font-weight: 600;
  color: #fff;
  line-height: 1;
}

.footer-cost {
  display: flex;
  flex-direction: column;
  gap: 3px;
  min-width: 0;
  flex: 1;
}

.cost-label {
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  color: var(--color-text-muted);
}

.cost-value {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text);
}

.cost-bar {
  height: 3px;
  background: var(--color-border);
  border-radius: 99px;
  overflow: hidden;
}

.cost-bar-fill {
  height: 100%;
  background: var(--color-primary);
  border-radius: 99px;
  transition: width 0.4s ease;
}
</style>

<!-- Portal-rendered content can't receive scoped styles -->
<style lang="scss">
.select-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  z-index: 200;
  min-width: 180px;
  padding: 4px;
}

.select-item {
  padding: 7px 10px;
  font-size: 13px;
  border-radius: var(--radius);
  cursor: pointer;
  user-select: none;
  color: var(--color-text);
  outline: none;

  &[data-highlighted] {
    background: var(--color-bg-subtle);
  }
}

.select-empty {
  padding: 8px 10px;
  font-size: 13px;
  color: var(--color-text-muted);
}
</style>
