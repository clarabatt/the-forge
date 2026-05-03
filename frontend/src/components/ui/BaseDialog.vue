<script setup lang="ts">
import { DialogContent, DialogOverlay, DialogPortal, DialogRoot } from 'radix-vue'

defineProps<{
  open: boolean
  width?: string
  maxHeight?: string
  padding?: string
  gap?: string
}>()
defineEmits<{ 'update:open': [value: boolean] }>()
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
        <slot />
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

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes slideIn {
  from { opacity: 0; transform: translate(-50%, -48%); }
  to { opacity: 1; transform: translate(-50%, -50%); }
}
</style>
