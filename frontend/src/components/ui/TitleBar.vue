<script setup lang="ts">
import BaseButton from "@/components/ui/BaseButton.vue";
import IconUpload from "@/components/icons/IconUpload.vue";

defineProps<{
  title: string;
  actionLabel?: string;
  actionDisabled?: boolean;
}>();

defineEmits<{ action: [] }>();
</script>

<template>
  <div class="title-bar">
    <h2 class="title-bar__title">{{ title }}</h2>
    <BaseButton v-if="actionLabel" :disabled="actionDisabled" @click="$emit('action')">
      <IconUpload />
      {{ actionLabel }}
    </BaseButton>
    <slot v-else name="action" />
  </div>
</template>

<style lang="scss" scoped>
.title-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0.5rem 1.5rem;
  min-height: 3rem;
  border-bottom: 1px solid var(--color-border);
  flex-shrink: 0;
}

.title-bar__title {
  font-size: 16px;
  font-weight: 700;
  color: var(--color-text);
}
</style>
