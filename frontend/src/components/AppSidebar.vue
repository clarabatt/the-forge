<script setup lang="ts">
import { computed, ref, useTemplateRef, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { PipelineStatus, useApplicationsStore } from "@/stores/applications";
import { useResumesStore } from "@/stores/resumes";
import { useAuthStore } from "@/stores/auth";
import { getAppTitle } from "@/utils/application";
import AppSelect from "@/components/ui/AppSelect.vue";
import BaseButton from "@/components/ui/BaseButton.vue";
import ProgressBar from "@/components/ui/ProgressBar.vue";
import Avatar from "@/components/ui/Avatar.vue";
import IconHamburger from "@/components/icons/IconHamburger.vue";
import IconSettings from "@/components/icons/IconSettings.vue";
import IconDotsVertical from "@/components/icons/IconDotsVertical.vue";
import IconLogout from "@/components/icons/IconLogout.vue";

const props = defineProps<{ mobileOpen?: boolean }>();
const emit = defineEmits<{ "new-application": []; close: [] }>();

const route = useRoute();
const router = useRouter();

async function logout() {
  menuOpen.value = false;
  await authStore.logout();
  router.push({ name: "login" });
}
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
  emit("close");
}

const menuOpen = ref(false);
const menuRef = useTemplateRef<HTMLDivElement>("menuRef");

function toggleMenu() {
  menuOpen.value = !menuOpen.value;
}

function onClickOutside(e: MouseEvent) {
  if (menuRef.value && !menuRef.value.contains(e.target as Node)) {
    menuOpen.value = false;
  }
}

watch(menuOpen, (open) => {
  if (open) document.addEventListener("mousedown", onClickOutside);
  else document.removeEventListener("mousedown", onClickOutside);
});

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
  [PipelineStatus.ANALYZING]: "var(--color-primary)",
  [PipelineStatus.UPLOADED]: "var(--color-text-muted)",
  [PipelineStatus.FAILED]: "var(--color-danger)",
};
</script>

<template>
  <div v-if="props.mobileOpen" class="mobile-backdrop" @click="emit('close')" />
  <aside
    class="sidebar"
    :class="{ 'sidebar--collapsed': collapsed, 'sidebar--mobile-open': props.mobileOpen }"
  >
    <!-- Header -->
    <div class="sidebar-header">
      <span v-if="!collapsed" class="sidebar-title">The Forge</span>
      <button
        class="sidebar-toggle"
        :aria-label="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        :title="collapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        @click="props.mobileOpen ? emit('close') : (collapsed = !collapsed)"
      >
        <IconHamburger />
      </button>
    </div>

    <!-- Scrollable body -->
    <div class="sidebar-body">
      <template v-if="!collapsed">
        <div class="sidebar-section">
          <div class="sidebar-label-row">
            <p class="sidebar-label">Base Resume</p>
            <button
              class="sidebar-label-action"
              aria-label="Manage resumes"
              data-tooltip="Manage resumes"
              @click="
                router.push({ name: 'resumes' });
                emit('close');
              "
            >
              <IconSettings />
            </button>
          </div>
          <AppSelect
            v-model="selectedResumeId"
            :options="resumesStore.baseResumes.map((r) => ({ value: r.id, label: r.file_name }))"
            placeholder="No resume"
          />

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
          <BaseButton
            variant="primary"
            block
            :disabled="hasNoBaseResumes"
            :aria-label="
              hasNoBaseResumes ? 'Upload a resume to create an application' : 'New application'
            "
            :title="
              hasNoBaseResumes ? 'Upload a resume to create an application' : 'New application'
            "
            @click="emit('new-application')"
          >
            New Application
          </BaseButton>
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
      <Avatar
        v-if="!collapsed"
        :src="authStore.user?.picture_url"
        :name="authStore.user?.full_name ?? ''"
      />

      <div v-if="!collapsed && costDisplay" class="footer-cost">
        <span class="cost-label">This month</span>
        <span class="cost-value">${{ costDisplay.current }} / ${{ costDisplay.cap }}</span>
        <ProgressBar :pct="costDisplay.pct" color="primary" :height="3" />
      </div>

      <div ref="menuRef" class="footer-menu">
        <button class="menu-trigger" title="More options" @click="toggleMenu">
          <IconDotsVertical />
        </button>
        <div v-if="menuOpen" class="menu-dropdown">
          <button class="menu-item menu-item--danger" @click="logout">
            <IconLogout />
            Log out
          </button>
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

  @media (max-width: 640px) {
    position: fixed;
    left: 0;
    top: 0;
    height: 100%;
    width: 280px;
    z-index: 200;
    transform: translateX(-100%);
    transition: transform 0.25s ease;
    box-shadow: none;

    &--collapsed {
      width: 280px; // no icon-mode on mobile
    }

    &--mobile-open {
      transform: translateX(0);
      box-shadow: 4px 0 24px rgba(0, 0, 0, 0.12);
    }
  }
}

.mobile-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  z-index: 199;
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

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
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

.sidebar-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
}

.sidebar-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  margin-bottom: 0;
}

.sidebar-label-action {
  position: relative;
  background: none;
  border: none;
  padding: 2px;
  cursor: pointer;
  color: var(--color-text-muted);
  display: flex;
  align-items: center;
  border-radius: var(--radius);

  &:hover {
    color: var(--color-text);
    background: var(--color-border);
  }

  &::after {
    content: attr(data-tooltip);
    position: absolute;
    top: calc(100% + 6px);
    right: 0;
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius);
    padding: 4px 8px;
    font-size: 11px;
    white-space: nowrap;
    color: var(--color-text);
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    pointer-events: none;
    opacity: 0;
    transition: opacity 0.15s ease;
  }

  &:hover::after {
    opacity: 1;
  }
}

.sidebar-empty {
  font-size: 13px;
  color: var(--color-text-muted);
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

.footer-menu {
  position: relative;
  flex-shrink: 0;
}

.menu-trigger {
  background: none;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 4px 6px;
  border-radius: var(--radius);
  color: var(--color-text-muted);

  &:hover {
    background: var(--color-border);
    color: var(--color-text);
  }
}

.menu-dropdown {
  position: absolute;
  bottom: calc(100% + 6px);
  right: 0;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  padding: 4px;
  min-width: 140px;
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

  &:hover {
    background: var(--color-bg-subtle);
  }

  &--danger {
    color: var(--color-danger);

    &:hover {
      background: color-mix(in srgb, var(--color-danger) 10%, transparent);
    }
  }
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
</style>
