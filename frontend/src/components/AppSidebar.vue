<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuTrigger,
} from "radix-vue";
import { PipelineStatus, useApplicationsStore } from "@/stores/applications";
import { useResumesStore } from "@/stores/resumes";
import { useAuthStore } from "@/stores/auth";
import { useFileUpload } from "@/composables/useFileUpload";
import { getAppTitle } from "@/utils/application";
import ProgressBar from "@/components/ui/ProgressBar.vue";
import Avatar from "@/components/ui/Avatar.vue";
import IconHamburger from "@/components/icons/IconHamburger.vue";
import IconFolder from "@/components/icons/IconFolder.vue";
import IconUpload from "@/components/icons/IconUpload.vue";
import IconPlus from "@/components/icons/IconPlus.vue";
import IconDotsVertical from "@/components/icons/IconDotsVertical.vue";
import IconLogout from "@/components/icons/IconLogout.vue";

const props = defineProps<{ mobileOpen?: boolean }>();
const emit = defineEmits<{ "new-application": []; close: [] }>();

const route = useRoute();
const router = useRouter();
const appsStore = useApplicationsStore();
const resumesStore = useResumesStore();
const authStore = useAuthStore();

const collapsed = ref(false);

const activeId = computed(() => route.params.id as string | undefined);
const hasNoBaseResumes = computed(() => !resumesStore.baseResumes?.length);

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

async function logout() {
  await authStore.logout();
  router.push({ name: "login" });
}

const { fileInput, isUploading, uploadError, triggerUpload, onFileSelected } = useFileUpload(
  (body) => {
    if (body?.id) resumesStore.selectedResumeId = body.id;
  },
);

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
      <RouterLink v-if="!collapsed" to="/" class="sidebar-title">The Forge</RouterLink>
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
          <p class="sidebar-section-title">Pages</p>
          <RouterLink :to="{ name: 'resumes' }" class="sidebar-nav-item" @click="emit('close')">
            <IconFolder />
            Resumes
          </RouterLink>
        </div>

        <div class="sidebar-section">
          <p class="sidebar-section-title">Actions</p>

          <input
            :ref="(el) => (fileInput = el as HTMLInputElement | null)"
            type="file"
            accept=".docx"
            class="file-input-hidden"
            @change="onFileSelected"
          />
          <button
            class="sidebar-nav-item"
            :disabled="isUploading"
            :title="isUploading ? 'Uploading resume...' : 'Upload new resume'"
            @click="triggerUpload"
          >
            <IconUpload />
            {{ isUploading ? "Uploading…" : "Upload resume" }}
          </button>
          <p v-if="uploadError" class="upload-error">{{ uploadError }}</p>

          <button
            class="sidebar-nav-item"
            :disabled="hasNoBaseResumes"
            :title="
              hasNoBaseResumes ? 'Upload a resume to create an application' : 'New application'
            "
            @click="emit('new-application')"
          >
            <IconPlus />
            New application
          </button>
        </div>

        <div class="sidebar-section">
          <p class="sidebar-section-title">Applications</p>
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

      <DropdownMenuRoot>
        <DropdownMenuTrigger class="menu-trigger" title="More options">
          <IconDotsVertical />
        </DropdownMenuTrigger>
        <DropdownMenuPortal>
          <DropdownMenuContent class="menu-content" side="top" :side-offset="6" align="end">
            <DropdownMenuItem class="sidebar-menu-item sidebar-menu-item--danger" @select="logout">
              <IconLogout />
              Log out
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenuPortal>
      </DropdownMenuRoot>
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
  min-height: 3rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
  text-decoration: none;
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
  padding: 6px 12px;

  &:first-child {
    padding-top: 18px;
  }
}

.sidebar-section-title {
  font-size: 11px;
  font-weight: 400;
  letter-spacing: 0.06em;
  color: var(--color-primary-hover);
  margin-bottom: 0.3rem;
}

.sidebar-nav-item {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
  padding: 6px 8px;
  margin: 8px 0;
  font-size: 13px;
  color: var(--color-text);
  line-height: 0;
  background: none;
  border: none;
  cursor: pointer;

  &:hover:not(:disabled) {
    text-decoration: underline;
  }

  &.router-link-active {
    background: var(--color-border);
  }

  &:disabled {
    color: var(--color-text-muted);
    cursor: default;
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
  flex-shrink: 0;
  background: var(--color-bg-subtle);

  &--collapsed {
    justify-content: center;
    padding: 12px 8px;
  }
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
  flex-shrink: 0;

  &:hover,
  &[data-state="open"] {
    background: var(--color-border);
    color: var(--color-text);
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

<style lang="scss">
/* Sidebar logout dropdown — teleported outside component DOM via DropdownMenuPortal */
.sidebar-menu-item {
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

  &--danger {
    color: var(--color-danger);

    &[data-highlighted] {
      background: color-mix(in srgb, var(--color-danger) 10%, transparent);
    }
  }
}
</style>
