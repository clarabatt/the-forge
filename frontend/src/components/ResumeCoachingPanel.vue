<script setup lang="ts">
import { ref } from "vue";
import type { CoachingAnalysis } from "@/stores/resumes";

defineProps<{ analysis: CoachingAnalysis }>();

const frameworkOpen = ref(false);
</script>

<template>
  <div class="coaching-panel">
    <!-- Overall score -->
    <div class="panel-header">
      <span class="score-badge" :class="`score-badge--${analysis.overall_score}`">
        {{
          analysis.overall_score === "needs_work"
            ? "Needs work"
            : analysis.overall_score === "decent"
              ? "Decent"
              : "Strong"
        }}
      </span>
      <span class="panel-header-label">Overall coaching score</span>
    </div>

    <!-- Global issues -->
    <div v-if="analysis.global_issues?.length" class="section">
      <h3 class="section-title section-title--global">Global issues</h3>
      <ul class="issue-list">
        <li v-for="(issue, i) in analysis.global_issues" :key="i" class="issue-list__item">
          {{ issue }}
        </li>
      </ul>
    </div>

    <!-- STAR / XYZ explainer -->
    <div class="explainer">
      <button class="explainer-toggle" @click="frameworkOpen = !frameworkOpen">
        <span class="explainer-icon">ℹ</span>
        What are STAR and XYZ?
        <span class="explainer-chevron" :class="{ open: frameworkOpen }">›</span>
      </button>
      <div v-if="frameworkOpen" class="explainer-body">
        <div class="framework-block">
          <p class="framework-name">STAR — Situation · Task · Action · Result</p>
          <p class="framework-desc">
            Each bullet should tell a micro-story: what was the context, what was your specific
            responsibility, what did you do, and what was the measurable outcome.
          </p>
          <p class="framework-example framework-example--weak">
            Weak: "Worked on backend services."
          </p>
          <p class="framework-example framework-example--strong">
            Strong: "Reduced p99 API latency by 40% by migrating 3 high-traffic endpoints to async
            workers, eliminating timeouts for ~12k daily users."
          </p>
        </div>
        <div class="framework-block">
          <p class="framework-name">XYZ — Accomplished X, as measured by Y, by doing Z</p>
          <p class="framework-desc">
            A more concise format suited for single-line bullets.
          </p>
          <p class="framework-example framework-example--weak">
            Weak: "Improved deployment process."
          </p>
          <p class="framework-example framework-example--strong">
            Strong: "Reduced deployment time by 65% (from 23 min to 8 min) by introducing
            parallel CI/CD build stages and Docker layer caching."
          </p>
        </div>
      </div>
    </div>

    <!-- Summary -->
    <div class="section">
      <h3 class="section-title">Summary</h3>
      <div v-if="analysis.summary_feedback?.detected_text" class="detected-text">
        {{ analysis.summary_feedback.detected_text }}
      </div>
      <div
        v-if="!analysis.summary_feedback?.issues?.length && !analysis.summary_feedback?.detected_text"
        class="looks-good"
      >
        Looks good!
      </div>
      <template v-else>
        <ul v-if="analysis.summary_feedback?.issues?.length" class="issue-list">
          <li
            v-for="(issue, i) in analysis.summary_feedback.issues"
            :key="i"
            class="issue-list__item"
          >
            {{ issue }}
          </li>
        </ul>
        <div v-if="analysis.summary_feedback?.coaching_questions?.length" class="questions">
          <p class="questions-label">To guide your rewrite:</p>
          <ul class="questions-list">
            <li
              v-for="(q, i) in analysis.summary_feedback.coaching_questions"
              :key="i"
              class="questions-list__item"
            >
              {{ q }}
            </li>
          </ul>
        </div>
      </template>
    </div>

    <!-- Skills -->
    <div
      v-if="analysis.skills_feedback?.issues?.length || analysis.skills_feedback?.coaching_questions?.length"
      class="section"
    >
      <h3 class="section-title">Skills</h3>
      <ul v-if="analysis.skills_feedback.issues?.length" class="issue-list">
        <li v-for="(issue, i) in analysis.skills_feedback.issues" :key="i" class="issue-list__item">
          {{ issue }}
        </li>
      </ul>
      <div v-if="analysis.skills_feedback.coaching_questions?.length" class="questions">
        <p class="questions-label">To guide your update:</p>
        <ul class="questions-list">
          <li
            v-for="(q, i) in analysis.skills_feedback.coaching_questions"
            :key="i"
            class="questions-list__item"
          >
            {{ q }}
          </li>
        </ul>
      </div>
    </div>

    <!-- Experience blocks -->
    <div
      v-for="(block, bi) in analysis.experience_blocks"
      :key="bi"
      class="section"
    >
      <h3 class="section-title">
        {{ block.employer }}
        <span v-if="block.date_range" class="section-title-meta">{{ block.date_range }}</span>
      </h3>
      <div
        v-for="(bullet, li) in block.bullets"
        :key="li"
        class="bullet-card"
        :class="`bullet-card--${bullet.framework_score}`"
      >
        <div class="bullet-text">"{{ bullet.text }}"</div>
        <div class="bullet-score-row">
          <span class="bullet-score" :class="`bullet-score--${bullet.framework_score}`">
            {{ bullet.framework_score === "weak" ? "Weak" : bullet.framework_score === "partial" ? "Partial" : "Strong" }}
          </span>
          <span v-for="(issue, ii) in bullet.issues" :key="ii" class="bullet-issue">
            {{ issue }}
          </span>
        </div>
        <div v-if="bullet.coaching_questions?.length" class="questions questions--tight">
          <ul class="questions-list">
            <li
              v-for="(q, qi) in bullet.coaching_questions"
              :key="qi"
              class="questions-list__item"
            >
              {{ q }}
            </li>
          </ul>
        </div>
        <div v-if="bullet.framework_score === 'strong' && !bullet.issues?.length" class="looks-good looks-good--inline">
          Looks good!
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss" scoped>
.coaching-panel {
  display: flex;
  flex-direction: column;
  gap: 20px;
  font-size: 13px;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-header-label {
  font-size: 12px;
  color: var(--color-text-muted);
}

.score-badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: 99px;
  border: 1px solid currentColor;

  &--needs_work {
    color: var(--color-danger);
  }
  &--decent {
    color: var(--color-warning);
  }
  &--strong {
    color: var(--color-success);
  }
}

.section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.section-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--color-text-muted);
  display: flex;
  align-items: baseline;
  gap: 6px;

  &--global {
    color: var(--color-danger);
  }
}

.section-title-meta {
  font-size: 10px;
  font-weight: 500;
  text-transform: none;
  letter-spacing: 0;
  color: var(--color-text-muted);
}

.detected-text {
  font-size: 12px;
  color: var(--color-text);
  background: var(--color-bg-subtle);
  border: 1px solid var(--color-border);
  border-radius: var(--radius-sm);
  padding: 8px 10px;
  line-height: 1.5;
  font-style: italic;
}

.issue-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 4px;

  &__item {
    color: var(--color-text);
    padding-left: 14px;
    position: relative;
    line-height: 1.45;

    &::before {
      content: "•";
      position: absolute;
      left: 0;
      color: var(--color-warning);
    }
  }
}

.questions {
  display: flex;
  flex-direction: column;
  gap: 4px;

  &--tight {
    margin-top: 4px;
  }
}

.questions-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--color-text-muted);
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.questions-list {
  list-style: none;
  display: flex;
  flex-direction: column;
  gap: 5px;

  &__item {
    color: var(--color-primary);
    padding-left: 16px;
    position: relative;
    line-height: 1.45;

    &::before {
      content: "→";
      position: absolute;
      left: 0;
      color: var(--color-primary);
      font-size: 11px;
    }
  }
}

.looks-good {
  font-size: 12px;
  font-weight: 500;
  color: var(--color-success);

  &--inline {
    margin-top: 2px;
  }
}

.explainer {
  border: 1px solid var(--color-border);
  border-radius: var(--radius-md);
  overflow: hidden;
}

.explainer-toggle {
  width: 100%;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 12px;
  background: var(--color-bg-subtle);
  border: none;
  cursor: pointer;
  font-size: 12px;
  font-weight: 500;
  color: var(--color-text);
  text-align: left;

  &:hover {
    background: var(--color-border);
  }
}

.explainer-icon {
  font-size: 13px;
  color: var(--color-primary);
}

.explainer-chevron {
  margin-left: auto;
  display: inline-block;
  transition: transform 0.15s;
  font-size: 16px;
  line-height: 1;
  color: var(--color-text-muted);

  &.open {
    transform: rotate(90deg);
  }
}

.explainer-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  border-top: 1px solid var(--color-border);
}

.framework-block {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.framework-name {
  font-weight: 600;
  font-size: 12px;
  color: var(--color-text);
}

.framework-desc {
  font-size: 12px;
  color: var(--color-text-muted);
  line-height: 1.5;
}

.framework-example {
  font-size: 12px;
  padding: 4px 8px;
  border-radius: var(--radius-sm);
  line-height: 1.45;

  &--weak {
    color: var(--color-danger);
    background: color-mix(in srgb, var(--color-danger) 8%, transparent);
  }

  &--strong {
    color: var(--color-success);
    background: color-mix(in srgb, var(--color-success) 8%, transparent);
  }
}

.bullet-card {
  border: 1px solid var(--color-border);
  border-radius: var(--radius);
  padding: 10px 12px;
  display: flex;
  flex-direction: column;
  gap: 6px;

  &--weak {
    border-left: 3px solid var(--color-danger);
  }

  &--partial {
    border-left: 3px solid var(--color-warning);
  }

  &--strong {
    border-left: 3px solid var(--color-success);
  }
}

.bullet-text {
  font-size: 12px;
  color: var(--color-text);
  line-height: 1.45;
  font-style: italic;
}

.bullet-score-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 6px;
}

.bullet-score {
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  padding: 2px 6px;
  border-radius: 99px;
  border: 1px solid currentColor;

  &--weak {
    color: var(--color-danger);
  }

  &--partial {
    color: var(--color-warning);
  }

  &--strong {
    color: var(--color-success);
  }
}

.bullet-issue {
  font-size: 11px;
  color: var(--color-text-muted);

  &:not(:last-child)::after {
    content: " ·";
    margin-left: 2px;
  }
}
</style>
