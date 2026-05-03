<script setup lang="ts">
defineProps<{
  variant?: 'primary' | 'secondary' | 'danger'
  block?: boolean
}>()
</script>

<template>
  <button
    class="base-btn"
    :class="[`base-btn--${variant ?? 'primary'}`, { 'base-btn--block': block }]"
  >
    <slot />
  </button>
</template>

<style lang="scss" scoped>
.base-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  padding: 7px 14px;
  font-size: 13px;
  font-weight: 500;
  border-radius: var(--radius);
  cursor: pointer;
  border: none;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  &--block {
    width: 100%;
  }

  &--primary {
    background: var(--color-primary);
    color: #fff;

    &:hover:not(:disabled) {
      background: var(--color-primary-hover);
    }
  }

  &--secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border: 1px solid var(--color-border);

    &:hover:not(:disabled) {
      background: var(--color-bg-subtle);
    }
  }

  &--danger {
    background: var(--color-danger);
    color: #fff;

    &:hover:not(:disabled) {
      opacity: 0.88;
    }
  }
}
</style>
