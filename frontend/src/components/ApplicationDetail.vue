<script setup lang="ts">
import { onMounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useApplicationsStore } from '@/stores/applications'
import ResumeViewer from '@/components/ResumeViewer.vue'

const route = useRoute()
const store = useApplicationsStore()

async function load() {
  await store.fetchOne(route.params.id as string)
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <div class="application-detail">
    <div v-if="!store.current" class="detail-empty">Loading…</div>
    <template v-else>
      <header class="detail-header">
        <div class="detail-title">
          <h1>{{ store.current.company_name }}</h1>
          <span class="detail-role">{{ store.current.job_title }}</span>
        </div>
        <span class="badge" :class="`badge--${store.current.status.toLowerCase()}`">
          {{ store.current.status.replace(/_/g, ' ') }}
        </span>
      </header>

      <div class="detail-actions">
        <button class="btn-download">Download Resume</button>
      </div>

      <ResumeViewer />
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
  padding: 32px 40px;
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

.badge {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 99px;
  background: var(--color-bg-subtle);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  white-space: nowrap;
  flex-shrink: 0;
  margin-top: 3px;

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
  &--validating {
    color: var(--color-primary);
    border-color: var(--color-primary);
  }
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
</style>
