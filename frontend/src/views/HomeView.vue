<script setup lang="ts">
import { onMounted } from 'vue'
import { useApplicationsStore } from '@/stores/applications'

const store = useApplicationsStore()
onMounted(() => store.fetchAll())
</script>

<template>
  <main class="home">
    <header class="home-header">
      <h1>Applications</h1>
    </header>

    <div v-if="store.isLoading" class="state-empty">Loading...</div>
    <div v-else-if="store.applications.length === 0" class="state-empty">
      No applications yet.
    </div>
    <ul v-else class="application-list">
      <li v-for="app in store.applications" :key="app.id" class="application-row">
        <router-link :to="{ name: 'application', params: { id: app.id } }">
          {{ app.company_name }}: {{ app.job_title }}
        </router-link>
        <span class="badge">{{ app.status }}</span>
      </li>
    </ul>
  </main>
</template>

<style lang="scss" scoped>
.home {
  max-width: 860px;
  margin: 0 auto;
  padding: 40px 24px;
}

.home-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;

  h1 {
    font-size: 20px;
    font-weight: 600;
  }
}

.state-empty {
  color: var(--color-text-muted);
}

.application-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.application-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  background: var(--color-surface);
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
