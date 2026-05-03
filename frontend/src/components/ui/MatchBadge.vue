<script setup lang="ts">
defineProps<{ found: boolean }>()
</script>

<template>
  <span :class="found ? 'badge-found' : 'badge-missing'">
    <svg v-if="found" width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
      <path
        d="M2 5l2.5 2.5L8 3"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </svg>
    <svg v-else width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
      <path
        d="M2.5 2.5l5 5M7.5 2.5l-5 5"
        stroke="currentColor"
        stroke-width="1.5"
        stroke-linecap="round"
      />
    </svg>
    {{ found ? 'Yes' : 'No' }}
  </span>
</template>

<style lang="scss" scoped>
.badge-found,
.badge-missing {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.badge-found {
  color: var(--color-success);
}

.badge-missing {
  color: var(--color-text-muted);
}
</style>
