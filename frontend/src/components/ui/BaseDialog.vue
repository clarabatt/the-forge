<script setup lang="ts">
import {
  DialogClose,
  DialogContent,
  DialogOverlay,
  DialogPortal,
  DialogRoot,
  DialogTitle,
} from "radix-vue";

defineProps<{
  open: boolean;
  title?: string;
  width?: string;
  maxHeight?: string;
  padding?: string;
  gap?: string;
  closeLabel?: string;
  closeDisabled?: boolean;
  actionLabel?: string;
  actionVariant?: "primary" | "danger";
  actionDisabled?: boolean;
}>();
defineEmits<{ "update:open": [value: boolean]; action: [] }>();
</script>

<template>
  <DialogRoot :open="open" @update:open="$emit('update:open', $event)">
    <DialogPortal>
      <DialogOverlay class="dialog-overlay" />
      <DialogContent
        class="dialog-content"
        :style="{
          width: width ?? '320px',
          maxHeight: maxHeight,
          padding: padding ?? '24px',
          gap: gap ?? '8px',
        }"
      >
        <div class="dialog-header">
          <DialogTitle class="dialog-title">{{ title }}</DialogTitle>
          <DialogClose class="dialog-close" aria-label="Close">✕</DialogClose>
        </div>

        <slot />

        <div class="dialog-actions">
          <DialogClose as-child>
            <button class="btn btn-secondary" :disabled="closeDisabled">
              {{ closeLabel ?? "Close" }}
            </button>
          </DialogClose>
          <button
            v-if="actionLabel"
            class="btn"
            :class="actionVariant === 'danger' ? 'btn-danger' : 'btn-primary'"
            :disabled="actionDisabled"
            @click="$emit('action')"
          >
            {{ actionLabel }}
          </button>
        </div>
      </DialogContent>
    </DialogPortal>
  </DialogRoot>
</template>

<style lang="scss" scoped>
.dialog-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  z-index: 300;
  animation: fadeIn 0.15s ease;
}

.dialog-content {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 301;
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 16px 48px rgba(0, 0, 0, 0.16);
  display: flex;
  flex-direction: column;
  animation: slideIn 0.15s ease;
}

.dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}

.dialog-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.dialog-close {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  background: none;
  cursor: pointer;
  color: var(--color-text-muted);
  font-size: 14px;
  border-radius: var(--radius-sm);
  line-height: 1;

  &:hover {
    background: var(--color-bg-subtle);
    color: var(--color-text);
  }
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 4px;
}

.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 14px;
  height: 32px;
  font-size: 13px;
  font-weight: 500;
  border-radius: var(--radius-sm);
  border: 1px solid transparent;
  cursor: pointer;
  white-space: nowrap;
  transition:
    background 0.1s,
    border-color 0.1s,
    color 0.1s;

  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
}

.btn-secondary {
  background: var(--color-surface);
  border-color: var(--color-border);
  color: var(--color-text);

  &:hover:not(:disabled) {
    background: var(--color-bg-subtle);
  }
}

.btn-primary {
  background: var(--color-primary);
  color: #fff;

  &:hover:not(:disabled) {
    background: var(--color-primary-hover);
  }
}

.btn-danger {
  background: var(--color-danger);
  color: #fff;

  &:hover:not(:disabled) {
    opacity: 0.9;
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translate(-50%, -48%);
  }
  to {
    opacity: 1;
    transform: translate(-50%, -50%);
  }
}
</style>
