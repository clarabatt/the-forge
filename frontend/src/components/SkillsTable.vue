<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useApplicationsStore, type Skill } from '@/stores/applications'

const props = defineProps<{ applicationId: string }>()

const store = useApplicationsStore()
const skills = ref<Skill[]>([])
const isLoading = ref(false)
const error = ref(false)

type SortKey = 'skill_name' | 'category' | 'match_status'
const sortKey = ref<SortKey>('match_status')
const sortDir = ref<1 | -1>(1)

function toggleSort(key: SortKey) {
  if (sortKey.value === key) {
    sortDir.value = sortDir.value === 1 ? -1 : 1
  } else {
    sortKey.value = key
    sortDir.value = 1
  }
}

const matchOrder = (s: Skill) => s.match_status === 'found_in_resume' ? 0 : 1

const sortedSkills = computed(() =>
  [...skills.value].sort((a, b) => {
    let cmp = 0
    if (sortKey.value === 'match_status') {
      cmp = matchOrder(a) - matchOrder(b)
    } else if (sortKey.value === 'skill_name') {
      cmp = a.skill_name.localeCompare(b.skill_name)
    } else {
      cmp = a.category.localeCompare(b.category)
    }
    return cmp * sortDir.value
  })
)

async function load(id: string) {
  isLoading.value = true
  error.value = false
  try {
    skills.value = await store.fetchSkills(id)
  } catch {
    error.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(() => load(props.applicationId))
watch(() => props.applicationId, (id) => load(id))
</script>

<template>
  <div class="skills-section">
    <h2 class="skills-heading">Skills Analysis</h2>

    <div v-if="isLoading" class="skills-loading">
      <div v-for="n in 6" :key="n" class="skills-loading-row" />
    </div>

    <div v-else-if="error" class="skills-empty">Could not load skills.</div>

    <div v-else-if="skills.length === 0" class="skills-empty">No skills recorded.</div>

    <table v-else class="skills-table">
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
                <path d="M2 5l2.5 2.5L8 3" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
              </svg>
              Yes
            </span>
            <span v-else class="badge-missing">
              <svg width="10" height="10" viewBox="0 0 10 10" fill="none" aria-hidden="true">
                <path d="M2.5 2.5l5 5M7.5 2.5l-5 5" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/>
              </svg>
              No
            </span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<!-- inline sub-component for the sort arrow -->
<script lang="ts">
import { defineComponent, h } from 'vue'

const SortIcon = defineComponent({
  props: {
    active: Boolean,
    dir: Number,
  },
  render() {
    const up = this.active && this.dir === -1
    const color = this.active ? 'currentColor' : 'var(--color-border)'
    return h(
      'svg',
      { width: 10, height: 10, viewBox: '0 0 10 10', fill: 'none', 'aria-hidden': 'true', style: 'flex-shrink:0' },
      [
        h('path', {
          d: up ? 'M2 6.5l3-3 3 3' : 'M2 3.5l3 3 3-3',
          stroke: color,
          'stroke-width': 1.5,
          'stroke-linecap': 'round',
          'stroke-linejoin': 'round',
        }),
      ]
    )
  },
})

export { SortIcon }
</script>

<style lang="scss" scoped>
.skills-section {
  margin-bottom: 32px;
}

.skills-heading {
  font-size: 13px;
  font-weight: 600;
  color: var(--color-text);
  margin-bottom: 12px;
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
    0%, 100% { opacity: 1; }
    50% { opacity: 0.4; }
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

  &:hover { color: var(--color-text); }
}

.col-skill { width: 45%; font-weight: 500; }
.col-category { width: 35%; }
.col-match { width: 20%; }

.badge-found,
.badge-missing {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  font-weight: 500;
}

.badge-found { color: var(--color-success); }
.badge-missing { color: var(--color-text-muted); }
</style>
