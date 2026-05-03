<script setup lang="ts">
import { onMounted, ref, watch } from "vue";
import { useApplicationsStore } from "@/stores/applications";
import Spinner from "@/components/ui/Spinner.vue";

const props = defineProps<{ applicationId: string }>();

const store = useApplicationsStore();
const html = ref("");
const isLoading = ref(false);
const error = ref(false);

async function load(id: string) {
  isLoading.value = true;
  html.value = "";
  error.value = false;
  try {
    const result = await store.fetchResumeHtml(id);
    if (!result) {
      error.value = true;
    } else {
      html.value = result;
    }
  } catch {
    error.value = true;
  } finally {
    isLoading.value = false;
  }
}

onMounted(() => load(props.applicationId));
watch(
  () => props.applicationId,
  (id) => load(id),
);
</script>

<template>
  <div class="resume-paper">
    <div v-if="isLoading" class="resume-loading">
      <Spinner :size="32" />
    </div>
    <div v-else-if="error" class="resume-error">Could not load resume.</div>
    <!-- eslint-disable-next-line vue/no-v-html -->
    <div v-else class="resume-body" v-html="html" />
  </div>
</template>

<style lang="scss" scoped>
.resume-paper {
  background: #fff;
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
  padding: 44px 52px;
  color: #111;
  font-family: "Georgia", "Times New Roman", serif;
  display: flex;
  flex: 1;
  flex-direction: column;
  align-self: stretch;
  height: 100%;
  min-height: 842px;
  width: 100%;
  max-width: 900px;
}

.resume-loading {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100%;
}

.resume-error {
  color: var(--color-text-muted);
  font-size: 13px;
  font-family: inherit;
}

// mammoth HTML output styles
.resume-body {
  :deep(p) {
    margin: 0 0 4px;
    font-size: 11pt;
    line-height: 1.5;
  }

  // name — first bold paragraph
  :deep(p:first-child strong) {
    font-size: 20pt;
    font-weight: 700;
    letter-spacing: -0.01em;
  }

  // title — second paragraph
  :deep(p:nth-child(2) strong) {
    font-size: 12pt;
    font-weight: 400;
    color: #444;
  }

  // contact line
  :deep(p:nth-child(3)) {
    font-size: 10pt;
    color: #555;
    margin-bottom: 18px;
  }

  // section headings (ALL-CAPS bold paragraphs like SUMMARY, SKILLS, WORK EXPERIENCE)
  :deep(p > strong:only-child) {
    display: block;
    font-size: 10pt;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    border-bottom: 1.5px solid #111;
    padding-bottom: 2px;
    margin-top: 16px;
    margin-bottom: 6px;
  }

  // job title + location line (bold p with mixed content)
  :deep(p strong) {
    font-weight: 600;
  }

  // company name + date range (mammoth maps to h3)
  :deep(h3) {
    font-size: 10pt;
    font-weight: 400;
    font-style: italic;
    color: #555;
    margin: 0 0 4px;
  }

  // some job titles mapped to h1 by Word styles
  :deep(h1) {
    font-size: 11pt;
    font-weight: 600;
    margin: 12px 0 0;
  }

  // skills paragraph (mapped to h2 by Word styles)
  :deep(h2) {
    font-size: 10.5pt;
    font-weight: 400;
    margin: 0 0 8px;
  }

  :deep(ul) {
    margin: 4px 0 10px 0;
    padding-left: 18px;
  }

  :deep(li) {
    font-size: 10.5pt;
    line-height: 1.55;
    margin-bottom: 3px;
  }
}
</style>
