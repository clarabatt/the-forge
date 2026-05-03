<script setup lang="ts">
defineProps<{ status: string }>()
</script>

<template>
  <span class="badge" :class="`badge--${status.toLowerCase()}`">
    {{ status.replace(/_/g, ' ') }}
  </span>
</template>

<style lang="scss" scoped>
.badge {
  font-size: 11px;
  font-weight: 500;
  padding: 3px 8px;
  border-radius: 99px;
  background: var(--color-bg-subtle);
  color: var(--color-text-muted);
  border: 1px solid var(--color-border);
  white-space: nowrap;

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
  &--validating,
  &--uploaded {
    color: var(--color-primary);
    border-color: var(--color-primary);
  }
}
</style>
