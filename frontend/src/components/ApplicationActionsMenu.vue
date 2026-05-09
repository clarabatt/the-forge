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
import IconDotsVertical from "@/components/icons/IconDotsVertical.vue";
import IconDocument from "@/components/icons/IconDocument.vue";
import IconEnvelope from "@/components/icons/IconEnvelope.vue";
import IconPlus from "@/components/icons/IconPlus.vue";
import IconRefresh from "@/components/icons/IconRefresh.vue";
import IconRetry from "@/components/icons/IconRetry.vue";
import IconTrash from "@/components/icons/IconTrash.vue";

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
  reanalyze: [];
  delete: [];
}>();
</script>

<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger class="menu-trigger" aria-label="Application actions">
      <IconDotsVertical width="16" height="16" />
    </DropdownMenuTrigger>
    <DropdownMenuPortal>
      <DropdownMenuContent class="menu-content" :side-offset="4" align="end">
        <DropdownMenuItem class="menu-item" @select="$emit('view-jd')">
          <IconDocument />
          Job description
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
          <IconEnvelope />
          Cover letter
        </DropdownMenuItem>
        <DropdownMenuItem
          v-else
          class="menu-item"
          :disabled="!hasFeedback"
          @select="$emit('generate-cover-letter')"
        >
          <IconPlus />
          Generate cover letter
        </DropdownMenuItem>
        <DropdownMenuSeparator class="menu-separator" />
        <DropdownMenuItem class="menu-item" @select="$emit('reanalyze')">
          <IconRefresh />
          Re-analyze with resume
        </DropdownMenuItem>
        <DropdownMenuItem
          class="menu-item"
          :disabled="status !== PipelineStatus.FAILED || isRetrying"
          @select="$emit('retry')"
        >
          <IconRetry />
          Retry analysis
        </DropdownMenuItem>
        <DropdownMenuItem
          class="menu-item menu-item--danger"
          :disabled="isDeleting"
          @select="$emit('delete')"
        >
          <IconTrash />
          Delete application
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
