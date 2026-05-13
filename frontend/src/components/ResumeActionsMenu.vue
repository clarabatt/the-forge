<script setup lang="ts">
import {
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuPortal,
  DropdownMenuRoot,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "radix-vue";
import { useRouter } from "vue-router";
import type { Resume } from "@/stores/resumes";
import IconDotsVertical from "@/components/icons/IconDotsVertical.vue";
import IconDownload from "@/components/icons/IconDownload.vue";
import IconEdit from "@/components/icons/IconEdit.vue";
import IconLightbulb from "@/components/icons/IconLightbulb.vue";
import IconTrashBin from "@/components/icons/IconTrashBin.vue";

const props = defineProps<{ resume: Resume }>();
const emit = defineEmits<{
  download: [];
  rename: [];
  delete: [];
}>();

const router = useRouter();
</script>

<template>
  <DropdownMenuRoot>
    <DropdownMenuTrigger class="menu-trigger" :aria-label="`Actions for ${props.resume.file_name}`">
      <IconDotsVertical width="14" height="14" />
    </DropdownMenuTrigger>
    <DropdownMenuPortal>
      <DropdownMenuContent class="menu-content" :side-offset="4" align="end">
        <DropdownMenuItem
          class="menu-item"
          @select="router.push({ name: 'resume-detail', params: { id: props.resume.id } })"
        >
          <IconLightbulb />
          View coaching
        </DropdownMenuItem>
        <DropdownMenuSeparator class="menu-separator" />
        <DropdownMenuItem class="menu-item" @select="emit('download')">
          <IconDownload />
          Download
        </DropdownMenuItem>
        <DropdownMenuItem class="menu-item" @select="emit('rename')">
          <IconEdit />
          Rename
        </DropdownMenuItem>
        <DropdownMenuSeparator class="menu-separator" />
        <DropdownMenuItem class="menu-item menu-item--danger" @select="emit('delete')">
          <IconTrashBin />
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

  &--danger {
    color: var(--color-danger);

    &[data-highlighted] {
      background: color-mix(in srgb, var(--color-danger) 10%, transparent);
    }
  }
}
</style>

<style lang="scss">
.menu-content {
  background: var(--color-surface);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  padding: 4px;
  min-width: 160px;
  z-index: 200;
}

.menu-separator {
  height: 1px;
  background: var(--color-border);
  margin: 4px 0;
}
</style>
