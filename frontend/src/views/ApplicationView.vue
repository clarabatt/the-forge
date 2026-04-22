<script setup lang="ts">
import { onMounted, onUnmounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useApplicationsStore } from '@/stores/applications'

const route = useRoute()
const store = useApplicationsStore()
const id = route.params.id as string
let eventSource: EventSource | null = null

onMounted(async () => {
  await store.fetchOne(id)
  eventSource = store.subscribeToStatus(id, (event) => {
    const data = JSON.parse(event.data)
    if (store.current) store.current.status = data.status
  })
})

onUnmounted(() => eventSource?.close())
</script>

<template>
  <main class="application-detail">
    <div v-if="!store.current" class="state-empty">Loading...</div>
    <template v-else>
      <header class="detail-header">
        <h1>{{ store.current.company_name }}: {{ store.current.job_title }}</h1>
        <span class="badge">{{ store.current.status }}</span>
      </header>
    </template>
  </main>
</template>

<style lang="scss" scoped>
.application-detail {
  max-width: 860px;
  margin: 0 auto;
  padding: 40px 24px;
}

.state-empty {
  color: var(--color-text-muted);
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 32px;

  h1 {
    font-size: 20px;
    font-weight: 600;
  }
}

.badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: 99px;
  background: var(--color-bg-subtle);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
}
</style>
