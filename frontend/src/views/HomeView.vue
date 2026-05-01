<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { useApplicationsStore } from "@/stores/applications";
import { useResumesStore } from "@/stores/resumes";
import { useAuthStore } from "@/stores/auth";
import AppSidebar from "@/components/AppSidebar.vue";
import NewApplicationModal from "@/components/NewApplicationModal.vue";

const route = useRoute();
const appsStore = useApplicationsStore();
const resumesStore = useResumesStore();
const authStore = useAuthStore();

const showModal = ref(false);
const sidebarOpen = ref(false);

onMounted(() => {
  appsStore.fetchAll();
  resumesStore.fetchAll();
  authStore.fetchUsage();
});
</script>

<template>
  <div class="workspace">
    <AppSidebar
      :mobile-open="sidebarOpen"
      @close="sidebarOpen = false"
      @new-application="showModal = true"
    />
    <main class="detail-area">
      <div class="mobile-topbar">
        <button class="mobile-menu-btn" aria-label="Open menu" @click="sidebarOpen = true">
          <svg width="18" height="18" viewBox="0 0 16 16" fill="none" aria-hidden="true">
            <rect x="1" y="3" width="14" height="1.5" rx="0.75" fill="currentColor" />
            <rect x="1" y="7.25" width="14" height="1.5" rx="0.75" fill="currentColor" />
            <rect x="1" y="11.5" width="14" height="1.5" rx="0.75" fill="currentColor" />
          </svg>
        </button>
        <span class="mobile-topbar-title">The Forge</span>
      </div>
      <div v-if="!route.params.id" class="detail-placeholder">
        <p>Select an application from the sidebar to view its details.</p>
      </div>
      <RouterView v-else key="detail" />
    </main>
  </div>

  <button class="fab" v-if="resumesStore.baseResumes?.length > 0" @click="showModal = true">
    +
  </button>

  <NewApplicationModal v-if="showModal" @close="showModal = false" />
</template>

<style lang="scss" scoped>
.workspace {
  display: flex;
  height: 100vh;
  overflow: hidden;
}

.detail-area {
  flex: 1;
  overflow-y: auto;
  background: var(--color-bg);
  min-width: 0;
}

.mobile-topbar {
  display: none;

  @media (max-width: 640px) {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 0 12px;
    height: 52px;
    border-bottom: 1px solid var(--color-border);
    background: var(--color-bg-subtle);
    position: sticky;
    top: 0;
    z-index: 10;
    flex-shrink: 0;
  }
}

.mobile-menu-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 36px;
  height: 36px;
  border-radius: var(--radius);
  border: 1px solid var(--color-border);
  background: var(--color-surface);
  color: var(--color-text-muted);
  cursor: pointer;
  flex-shrink: 0;

  &:hover {
    color: var(--color-text);
    background: var(--color-border);
  }
}

.mobile-topbar-title {
  font-size: 15px;
  font-weight: 700;
  color: var(--color-text);
  letter-spacing: -0.01em;
}

.detail-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: var(--color-text-muted);
  font-size: 14px;
}

.fab {
  position: fixed;
  bottom: 24px;
  right: 24px;
  width: 52px;
  height: 52px;
  border-radius: 25%;
  background: var(--color-primary);
  color: #fff;
  font-size: 24px;
  line-height: 1;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  transition: background 0.15s;

  &:hover {
    background: var(--color-primary-hover);
  }

  @media (max-width: 640px) {
    bottom: 28px;
    width: 48px;
    height: 48px;
  }
}
</style>
