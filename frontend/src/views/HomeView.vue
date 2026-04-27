<script setup lang="ts">
import { onMounted } from "vue";
import { useRoute } from "vue-router";
import { useApplicationsStore } from "@/stores/applications";
import { useResumesStore } from "@/stores/resumes";
import { useAuthStore } from "@/stores/auth";
import AppSidebar from "@/components/AppSidebar.vue";

const route = useRoute();
const appsStore = useApplicationsStore();
const resumesStore = useResumesStore();
const authStore = useAuthStore();

onMounted(() => {
  appsStore.fetchAll();
  resumesStore.fetchAll();
  authStore.fetchUsage();
});
</script>

<template>
  <div class="workspace">
    <AppSidebar />
    <main class="detail-area">
      <div v-if="!route.params.id" class="detail-placeholder">
        <p>Select an application from the sidebar to view its details.</p>
      </div>
      <RouterView v-else key="detail" />
    </main>
  </div>
  <button class="fab" aria-label="New application">+</button>
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
}
</style>
