<script setup lang="ts">
import Spinner from "@/components/ui/Spinner.vue";

const props = defineProps<{
  status: "pending" | "analyzing" | "done" | "failed";
  compact?: boolean;
}>();

const label = {
  analyzing: "Analyzing…",
  done: "Ready",
  failed: props.compact ? "Failed" : "Analysis failed",
  pending: "Pending",
};
</script>

<template>
  <span class="insights-chip" :class="`insights-chip--${status}`">
    <Spinner v-if="status === 'analyzing'" :size="compact ? 10 : 11" />
    {{ label[status] }}
  </span>
</template>

<style lang="scss" scoped>
.insights-chip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: 99px;
  border: 1px solid var(--color-border);
  color: var(--color-text-muted);
  white-space: nowrap;

  &--analyzing {
    color: var(--color-primary);
    border-color: var(--color-primary);
  }

  &--done {
    color: var(--color-success);
    border-color: var(--color-success);
  }

  &--failed {
    color: var(--color-danger);
    border-color: var(--color-danger);
  }
}
</style>
