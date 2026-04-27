<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { marked } from "marked";
import { useApplicationsStore, type AnalysisFeedback, type Skill } from "@/stores/applications";

function md(text: string): string {
  return marked.parse(text, { async: false }) as string;
}

function mdInline(text: string): string {
  return marked.parseInline(text, { async: false }) as string;
}

const props = defineProps<{ applicationId: string }>();

const store = useApplicationsStore();
const skills = ref<Skill[]>([]);
const isLoading = ref(false);
const error = ref(false);

type SortKey = "skill_name" | "category" | "match_status";
const sortKey = ref<SortKey>("match_status");
const sortDir = ref<1 | -1>(1);

function toggleSort(key: SortKey) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 1 ? -1 : 1;
  } else {
    sortKey.value = key;
    sortDir.value = 1;
  }
}

const matchOrder = (s: Skill) => (s.match_status === "found_in_resume" ? 0 : 1);

const sortedSkills = computed(() =>
  [...skills.value].sort((a, b) => {
    let cmp = 0;
    if (sortKey.value === "match_status") {
      cmp = matchOrder(a) - matchOrder(b);
    } else if (sortKey.value === "skill_name") {
      cmp = a.skill_name.localeCompare(b.skill_name);
    } else {
      cmp = a.category.localeCompare(b.category);
    }
    return cmp * sortDir.value;
  }),
);

const feedback = computed(() => {
  if (!skills.value.length) return null;

  const total = skills.value.length;
  const found = skills.value.filter((s) => s.match_status === "found_in_resume").length;
  const missing = skills.value.filter((s) => s.match_status === "missing");
  const matchPct = Math.round((found / total) * 100);

  // top missing skills ordered by rank (lower rank = more critical)
  const topGaps = [...missing].sort((a, b) => a.rank - b.rank).slice(0, 3);

  // missing count per category
  const byCategory = missing.reduce<Record<string, number>>((acc, s) => {
    acc[s.category] = (acc[s.category] ?? 0) + 1;
    return acc;
  }, {});

  return { found, total, matchPct, topGaps, byCategory };
});

const feedbackOpen = ref(true);

const aiFeedback = computed((): AnalysisFeedback | null => {
  const raw = store.current?.analysis_feedback;
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
});

async function load(id: string) {
  isLoading.value = true;
  error.value = false;
  try {
    skills.value = await store.fetchSkills(id);
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
  <div class="skills-section">
    <h2 class="skills-heading">Skills Analysis</h2>

    <div v-if="isLoading" class="skills-loading">
      <div v-for="n in 6" :key="n" class="skills-loading-row" />
    </div>

    <div v-else-if="error" class="skills-empty">Could not load skills.</div>

    <div v-else-if="skills.length === 0" class="skills-empty">No skills recorded.</div>

    <template v-else>
      <table class="skills-table">
        <thead>
          <tr>
            <th class="col-skill">
              <button class="th-btn" @click="toggleSort('skill_name')">
                Skill
                <SortIcon :active="sortKey === 'skill_name'" :dir="sortDir" />
              </button>
            </th>
            <th class="col-category">
              <button class="th-btn" @click="toggleSort('category')">
                Category
                <SortIcon :active="sortKey === 'category'" :dir="sortDir" />
              </button>
            </th>
            <th class="col-match">
              <button class="th-btn" @click="toggleSort('match_status')">
                In resume
                <SortIcon :active="sortKey === 'match_status'" :dir="sortDir" />
              </button>
            </th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="skill in sortedSkills"
            :key="skill.id"
            :class="{ 'row--missing': skill.match_status === 'missing' }"
          >
            <td class="col-skill">{{ skill.skill_name }}</td>
            <td class="col-category">{{ skill.category }}</td>
            <td class="col-match">
              <span v-if="skill.match_status === 'found_in_resume'" class="badge-found">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
                  <path
                    d="M2 5l2.5 2.5L8 3"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                    stroke-linejoin="round"
                  />
                </svg>
                Yes
              </span>
              <span v-else class="badge-missing">
                <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
                  <path
                    d="M2.5 2.5l5 5M7.5 2.5l-5 5"
                    stroke="currentColor"
                    stroke-width="1.5"
                    stroke-linecap="round"
                  />
                </svg>
                No
              </span>
            </td>
          </tr>
        </tbody>
      </table>

      <!-- Feedback panel -->
      <div v-if="feedback" class="feedback">
        <button class="feedback-toggle" @click="feedbackOpen = !feedbackOpen">
          <span class="feedback-heading">What to improve</span>
          <svg
            width="12"
            height="12"
            viewBox="0 0 12 12"
            fill="none"
            aria-hidden="true"
            :style="{
              transform: feedbackOpen ? 'rotate(180deg)' : 'rotate(0deg)',
              transition: 'transform 0.2s ease',
            }"
          >
            <path
              d="M2 4l4 4 4-4"
              stroke="currentColor"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
        </button>

        <template v-if="feedbackOpen">
          <!-- match bar -->
          <div class="match-bar-row">
            <span class="match-label"
              >{{ feedback.found }} / {{ feedback.total }} skills matched</span
            >
            <span
              class="match-pct"
              :class="
                feedback.matchPct >= 70
                  ? 'match-pct--good'
                  : feedback.matchPct >= 40
                    ? 'match-pct--mid'
                    : 'match-pct--low'
              "
            >
              {{ feedback.matchPct }}%
            </span>
          </div>
          <div class="match-bar">
            <div
              class="match-bar-fill"
              :class="
                feedback.matchPct >= 70
                  ? 'fill--good'
                  : feedback.matchPct >= 40
                    ? 'fill--mid'
                    : 'fill--low'
              "
              :style="{ width: feedback.matchPct + '%' }"
            />
          </div>

          <!-- top gaps -->
          <template v-if="feedback.topGaps.length">
            <p class="feedback-label">Top gaps to address</p>
            <ul class="gap-list">
              <li v-for="s in feedback.topGaps" :key="s.id" class="gap-item">
                <span class="gap-name">{{ s.skill_name }}</span>
                <span class="gap-cat">{{ s.category }}</span>
              </li>
            </ul>
          </template>

          <!-- category breakdown -->
          <template v-if="Object.keys(feedback.byCategory).length">
            <p class="feedback-label">Missing by category</p>
            <ul class="category-list">
              <li v-for="(count, cat) in feedback.byCategory" :key="cat" class="category-item">
                <span class="category-name">{{ cat }}</span>
                <span class="category-count">{{ count }}</span>
              </li>
            </ul>
          </template>

          <p v-if="feedback.matchPct === 100" class="feedback-all-good">
            All required skills are present in your resume.
          </p>
        </template>
      </div>

      <!-- AI recruiter feedback -->
      <div v-if="aiFeedback" class="ai-feedback">
        <h2 class="ai-heading">Recruiter Assessment</h2>

        <!-- eslint-disable-next-line vue/no-v-html -->
        <div class="ai-overall" v-html="md(aiFeedback.overall_assessment)" />

        <template v-if="aiFeedback.strong_points.length">
          <p class="feedback-label">Strong points</p>
          <ul class="ai-list ai-list--good">
            <!-- eslint-disable-next-line vue/no-v-html -->
            <li v-for="(pt, i) in aiFeedback.strong_points" :key="i" v-html="mdInline(pt)" />
          </ul>
        </template>

        <template v-if="aiFeedback.weak_points.length">
          <p class="feedback-label">Weak points</p>
          <ul class="ai-list ai-list--bad">
            <!-- eslint-disable-next-line vue/no-v-html -->
            <li v-for="(pt, i) in aiFeedback.weak_points" :key="i" v-html="mdInline(pt)" />
          </ul>
        </template>

        <template v-if="aiFeedback.recommended_changes.length">
          <p class="feedback-label">Recommended changes</p>
          <ul class="ai-list">
            <!-- eslint-disable-next-line vue/no-v-html -->
            <li v-for="(pt, i) in aiFeedback.recommended_changes" :key="i" v-html="mdInline(pt)" />
          </ul>
        </template>
      </div>
    </template>
  </div>
</template>

<!-- inline sub-component for the sort arrow -->
<script lang="ts">
import { defineComponent, h } from "vue";

const SortIcon = defineComponent({
  props: {
    active: Boolean,
    dir: Number,
  },
  render() {
    const up = this.active && this.dir === -1;
    const color = this.active ? "currentColor" : "var(--color-border)";
    return h(
      "svg",
      {
        width: 10,
        height: 10,
        viewBox: "0 0 10 10",
        fill: "none",
        "aria-hidden": "true",
        style: "flex-shrink:0",
      },
      [
        h("path", {
          d: up ? "M2 6.5l3-3 3 3" : "M2 3.5l3 3 3-3",
          stroke: color,
          "stroke-width": 1.5,
          "stroke-linecap": "round",
          "stroke-linejoin": "round",
        }),
      ],
    );
  },
});

export { SortIcon };
</script>

<style lang="scss" scoped>
.skills-section {
  margin-bottom: 32px;
}

.skills-heading {
  margin-bottom: 12px;
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
}

.skills-loading {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.skills-loading-row {
  height: 32px;
  background: var(--color-border);
  border-radius: var(--radius);
  animation: shimmer 1.4s ease infinite;

  @keyframes shimmer {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0.4;
    }
  }
}

.skills-empty {
  font-size: 13px;
  color: var(--color-text-muted);
}

.skills-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  margin-bottom: 24px;

  thead tr {
    border-bottom: 1px solid var(--color-border);
  }

  th {
    text-align: left;
    padding: 0 12px 8px 0;
  }

  td {
    padding: 7px 12px 7px 0;
    color: var(--color-text);
    border-bottom: 1px solid var(--color-border);
  }

  tbody tr:last-child td {
    border-bottom: none;
  }

  .row--missing td {
    color: var(--color-text-muted);
  }
}

.th-btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);

  &:hover {
    color: var(--color-text);
  }
}

.col-skill {
  width: 45%;
  font-weight: 500;
}
.col-category {
  width: 35%;
}
.col-match {
  width: 20%;
}

.badge-found,
.badge-missing {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.badge-found {
  color: var(--color-success);
}
.badge-missing {
  color: var(--color-text-muted);
}

// Feedback panel
.feedback {
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.feedback-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  background: none;
  border: none;
  padding: 0;
  cursor: pointer;
  color: var(--color-text);

  &:hover .feedback-heading {
    color: var(--color-text-muted);
  }
}

.feedback-heading {
  font-size: 12px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

.match-bar-row {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  font-size: 12px;
}

.match-label {
  color: var(--color-text-muted);
}

.match-pct {
  font-size: 13px;
  font-weight: 600;

  &--good {
    color: var(--color-success);
  }
  &--mid {
    color: var(--color-warning);
  }
  &--low {
    color: var(--color-danger);
  }
}

.match-bar {
  height: 4px;
  background: var(--color-border);
  border-radius: 99px;
  overflow: hidden;
  margin-top: -6px;
}

.match-bar-fill {
  height: 100%;
  border-radius: 99px;
  transition: width 0.4s ease;

  &.fill--good {
    background: var(--color-success);
  }
  &.fill--mid {
    background: var(--color-warning);
  }
  &.fill--low {
    background: var(--color-danger);
  }
}

.feedback-label {
  font-size: 11px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  margin: 0;
}

.gap-list,
.category-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.gap-item {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.gap-name {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text);
}

.gap-cat {
  font-size: 11px;
  color: var(--color-text-muted);
}

.category-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 12px;
}

.category-name {
  color: var(--color-text);
}

.category-count {
  font-weight: 600;
  color: var(--color-text-muted);
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: 99px;
  padding: 0px 7px;
  font-size: 11px;
}

.feedback-all-good {
  font-size: 12px;
  color: var(--color-success);
  margin: 0;
}

.ai-heading {
  font-size: 15px;
  font-weight: 600;
  color: var(--color-text);
  margin: 0;
}

// AI recruiter feedback
.ai-feedback {
  padding-top: 20px;
  border-top: 1px solid var(--color-border);
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.ai-overall {
  font-size: 12px;
  line-height: 1.6;
  color: var(--color-text);

  :deep(p) { margin: 0 0 6px; }
  :deep(p:last-child) { margin-bottom: 0; }
  :deep(strong) { font-weight: 600; }
  :deep(em) { font-style: italic; }
  :deep(code) { font-family: monospace; font-size: 11px; background: var(--color-bg-subtle); padding: 1px 4px; border-radius: 3px; }
}

.ai-list {
  margin: 0;
  padding-left: 16px;
  display: flex;
  flex-direction: column;
  gap: 5px;

  li {
    font-size: 12px;
    line-height: 1.5;
    color: var(--color-text);

    :deep(strong) { font-weight: 600; }
    :deep(em) { font-style: italic; }
    :deep(code) { font-family: monospace; font-size: 11px; background: var(--color-bg-subtle); padding: 1px 4px; border-radius: 3px; }
  }

  &--good li {
    color: var(--color-success);
  }
  &--bad li {
    color: var(--color-danger);
  }
}
</style>
