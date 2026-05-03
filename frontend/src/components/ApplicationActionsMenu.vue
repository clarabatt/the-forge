<script setup lang="ts">
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "radix-vue";
import { type CoverLetter, PipelineStatus } from "@/stores/applications";
import Spinner from "@/components/ui/Spinner.vue";

defineProps<{
  status: PipelineStatus;
  hasFeedback: boolean;
  coverLetter: CoverLetter | null;
  isRetrying: boolean;
  isDeleting: boolean;
  isGeneratingCL: boolean;
}>();

defineEmits<{
  "view-jd": [];
  "view-cover-letter": [];
  "generate-cover-letter": [];
  retry: [];
  delete: [];
}>();
</script>

<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger class="menu-trigger" aria-label="Application actions">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="currentColor" aria-hidden="true">
        <circle cx="8" cy="3" r="1.25" />
        <circle cx="8" cy="8" r="1.25" />
        <circle cx="8" cy="13" r="1.25" />
      </svg>
    </DropdownMenuTrigger>
    <DropdownMenuPortal>
      <DropdownMenuContent class="menu-content" :side-offset="4" align="end">
        <DropdownMenuItem class="menu-item" @select="$emit('view-jd')">
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <rect x="2" y="1" width="8" height="10" rx="1" stroke="currentColor" stroke-width="1.5" />
            <path d="M4 4h4M4 6.5h4M4 9h2.5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" />
          </svg>
          View job description
        </DropdownMenuItem>
        <DropdownMenuSeparator class="menu-separator" />
        <DropdownMenuItem v-if="isGeneratingCL" class="menu-item menu-item--loading" disabled>
          <Spinner :size="12" />
          Generating…
        </DropdownMenuItem>
        <DropdownMenuItem
          v-else-if="coverLetter"
          class="menu-item"
          @select="$emit('view-cover-letter')"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <rect x="1" y="2.5" width="10" height="7" rx="1" stroke="currentColor" stroke-width="1.5" />
            <path d="M1 4l5 3.5L11 4" stroke="currentColor" stroke-width="1.3" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          View cover letter
        </DropdownMenuItem>
        <DropdownMenuItem
          v-else
          class="menu-item"
          :disabled="!hasFeedback"
          @select="$emit('generate-cover-letter')"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path d="M6 1v10M1 6h10" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
          </svg>
          Generate cover letter
        </DropdownMenuItem>
        <DropdownMenuSeparator class="menu-separator" />
        <DropdownMenuItem
          class="menu-item"
          :disabled="status !== PipelineStatus.FAILED || isRetrying"
          @select="$emit('retry')"
        >
          <svg width="12" height="12" viewBox="-2 -2 14 14" fill="none" aria-hidden="true">
            <path d="M10.5 2A5.5 5.5 0 1 0 11 6.5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" />
            <path d="M8.5 2H10.5V0" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" />
          </svg>
          Retry
        </DropdownMenuItem>
        <DropdownMenuSeparator class="menu-separator" />
        <DropdownMenuItem
          class="menu-item menu-item--danger"
          :disabled="isDeleting"
          @select="$emit('delete')"
        >
          <svg width="12" height="12" viewBox="0 0 12 12" fill="none" aria-hidden="true">
            <path
              d="M1.5 3h9M4.5 3V1.5h3V3M5 5.5v3M7 5.5v3M2.5 3l.5 7h6l.5-7"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          Delete
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenuPortal>
  </DropdownMenuRoot>
</template>

<style lang="scss" scoped>
.menu-trigger {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 26px;
  height: 26px;
  border-radius: var(--radius);
  border: none;
  background: transparent;
  color: var(--color-text-muted);
  cursor: pointer;

  &:hover {
    background: var(--color-border);
    color: var(--color-text);
  }

  &[data-state="open"] {
    background: var(--color-border);
    color: var(--color-text);
  }
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 10px;
  font-size: 13px;
  border-radius: var(--radius);
  cursor: pointer;
  outline: none;
  color: var(--color-text);
  user-select: none;

  &[data-highlighted] {
    background: var(--color-bg-subtle);
  }

  &[data-disabled] {
    opacity: 0.4;
    cursor: default;
    pointer-events: none;
  }

  &--loading {
    opacity: 0.6;
    cursor: default;
    pointer-events: none;
  }

  &--danger {
    color: var(--color-danger);

    &[data-highlighted] {
      background: color-mix(in srgb, var(--color-danger) 10%, transparent);
    }
  }
}
</style>

<style lang="scss">
/* DropdownMenuPortal teleports content outside the component DOM,
   so these rules must be global to apply. */
.menu-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  padding: 4px;
  min-width: 180px;
  z-index: 200;
}

.menu-separator {
  height: 1px;
  background: var(--color-border);
  margin: 4px 0;
}
</style>
