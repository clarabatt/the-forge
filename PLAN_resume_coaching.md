# Plan: Resume Coaching Analysis on Upload

## Overview

When a user uploads a base resume, the system runs a standalone AI coaching analysis — no JD required. The goal is to help the user improve their resume _before_ they start tailoring it for specific applications, by teaching writing frameworks (STAR, XYZ) and asking targeted questions for each experience block and the summary section.

---

## User Flow

1. User clicks **Upload resume** on the Resumes page and selects a `.docx`.
2. Upload completes; the user is redirected to the Resume Details page, where the new resume name appears at the top with a **"Analyzing…"** status indicator.
3. In the background, the coaching agent runs against the parsed `raw_text`.
4. When done, it opens a resume view on the right side of the screen and on the left side the coaching analysis (similar to the feedback view but focused on coaching, not JD-specific feedback):
   - A collapsible explainer of the STAR and XYZ frameworks, since many users won't be familiar with them.
   - Per-section cards: one for the **Summary**, one per **Job Experience**, one for **Global Issues**, one for **Skills**, one per **Education** or **Projects**.
   - Each card shows: detected weaknesses + 2–3 coaching questions to guide rewriting.
   - If no issues are detected, show a green "Looks good!" badge instead.
   - An overall coaching score at the top: "Needs work", "Decent", or "Strong".
     - "Needs work": major issues detected in multiple sections, overall structure is weak.
     - "Decent": some issues detected, but overall structure is okay.
     - "Strong": few to no issues detected, strong use of STAR/XYZ.
5. The user can go to resume list page and see the coaching status for each resume, click into any resume to view its coaching analysis, and the 3-dot menu shows a **"View coaching"** link.

---

## Writing Frameworks (Educational Content)

The agent and UI should explain these two frameworks:

### STAR

**Situation · Task · Action · Result**
Each bullet should tell a micro-story: what was the context, what was your specific responsibility, what did you do, and what was the measurable outcome.

_Weak:_ "Worked on backend services."
_Strong:_ "Reduced p99 API latency by 40 % by migrating 3 high-traffic endpoints from synchronous DB calls to async workers (FastAPI + Redis), eliminating timeouts for ~12 k daily users."

### XYZ

**Accomplished X, as measured by Y, by doing Z.**
A more concise version of STAR, suited for single-line bullets.

_Weak:_ "Improved deployment process."
_Strong:_ "Reduced deployment time by 65 % (from 23 min to 8 min) by introducing parallel build stages and layer caching in the CI/CD pipeline."

---

## Data Model Changes

### Option A — field on `resumes` (recommended)

Add a `coaching_analysis` nullable JSON-string column to the `Resume` table, mirroring how `analysis_feedback` is stored on `Application`.

```python
coaching_analysis: Optional[str] = None  # JSON: see schema below
coaching_status: str = Field(default="pending")  # pending | analyzing | done | failed
```

**JSON schema:**

```json
{
  "summary_feedback": {
    "detected_text": "...",
    "issues": ["issue 1", "issue 2"],
    "coaching_questions": ["Q1", "Q2", "Q3"]
  },
  "experience_blocks": [
    {
      "employer": "Acme Corp",
      "date_range": "2022–2024",
      "bullets": [
        {
          "text": "...",
          "framework_score": "weak|partial|strong",
          "issues": ["no metric", "passive voice"],
          "coaching_questions": [
            "What was the business impact?",
            "Can you quantify the time saved?"
          ]
        }
      ]
    }
  ],
  "global_issues": [
    "No quantified metrics across any bullet",
    "Summary is missing"
  ],
  "overall_score": "needs_work|decent|strong"
}
```

### Migration

New Alembic migration: `0008_add_coaching_to_resumes.py`

- `coaching_analysis TEXT NULL`
- `coaching_status VARCHAR(20) NOT NULL DEFAULT 'pending'`

---

## New Agent: `resume_coaching_agent.py`

**Location:** `backend/agents/resume_coaching_agent.py`

**Model:** Gemini (same as other agents, via `settings.gemini_api_key`)

**Input:** `resume_blocks: list[dict]` — same structure produced by `resume_agent.run()`

**System prompt persona:** Senior resume coach with recruiting background, direct and specific. Not here to praise — here to help the candidate land interviews.

**Output schema:**

```json
{
  "summary_feedback": { ... },
  "experience_blocks": [ ... ],
  "global_issues": [ ... ],
  "overall_score": "needs_work|decent|strong"
}
```

**Prompt strategy:**

- Give it the two framework definitions (STAR / XYZ) as context so it can grade each bullet against them.
- For each bullet: detect whether it has a Result/metric, an Action verb, and a measurable scope.
- For the summary: check if it is role-specific, contains a value proposition, and is not a generic objective statement.
- Generate 2–3 questions per block that prompt the user to think about the missing dimension (metric, context, action, scope).

---

## Backend Changes

### 1. `resume_agent.py` (no change)

Already parses raw text into blocks with `type`, `employer`, `date_range`, `text`, `skills_detected`. This output feeds the coaching agent.

### 2. `routers/resumes.py` — `POST /`

After saving the resume to DB and storage, kick off the coaching analysis:

- **Dev mode (`DEV_MODE=true`):** run as a `BackgroundTasks` task (same pattern as the application pipeline).
- **Production:** enqueue a Cloud Tasks job targeting a new endpoint `POST /internal/resumes/{resume_id}/analyze-coaching`.

The upload response returns immediately with `coaching_status: "analyzing"` so the frontend can poll.

### 3. New internal route or service function

```python
def run_coaching(resume_id: uuid.UUID) -> None:
    # 1. Load resume from DB
    # 2. Run resume_agent.run(raw_text) to get blocks
    # 3. Run resume_coaching_agent.run(blocks)
    # 4. Save JSON to resume.coaching_analysis, set coaching_status = "done"
    # 5. Log LLM usage (new AgentName.RESUME_COACHING enum value)
```

### 4. `models.py`

- Add `coaching_analysis: Optional[str] = None` and `coaching_status: str = "pending"` to `Resume`.
- Add `RESUME_COACHING = "RESUME_COACHING"` to `AgentName` enum.

### 5. `GET /resumes/` — include coaching fields

The list endpoint should return `coaching_status` and `coaching_analysis` so the frontend can display state without an extra fetch.

---

## Frontend Changes

### 1. `stores/resumes.ts`

- Extend `Resume` type with `coaching_status` and `coaching_analysis` (typed interface matching JSON schema above).
- Add `fetchCoachingAnalysis(resumeId)` action for manual refresh.
- Poll on coaching_status === "analyzing" — check every 3 s, stop when `done` or `failed`.

### 2. `views/ResumesView.vue`

- Add a **coaching status chip** in each table row: `Analyzing…` spinner | `View coaching` button | `Failed` badge.
- When "View coaching" is clicked, expand an inline panel below the row (or open a `BaseDialog`) showing `ResumeCoachingPanel`.

### 3. New component: `components/ResumeCoachingPanel.vue`

**Structure:**

```
┌─ Coaching Analysis ────────────────────────────────────┐
│ Overall: [needs_work | decent | strong] badge          │
│                                                        │
│ ℹ What are STAR and XYZ?  [collapsible explainer]     │
│                                                        │
│ ── Summary ─────────────────────────────────────────── │
│ Detected text: "..."                                   │
│ Issues: • Too generic • No target role mentioned       │
│ Questions to guide you:                                │
│   → What specific type of role are you targeting?     │
│   → What is your core value proposition?              │
│                                                        │
│ ── Acme Corp (2022–2024) ───────────────────────────── │
│ Bullet: "Worked on backend services."                  │
│   ⚠ Weak: no metric, no scope, passive phrasing       │
│   Questions:                                           │
│     → What business outcome did this backend work     │
│       enable? (e.g. latency, uptime, cost)            │
│     → How many users or systems were affected?        │
└────────────────────────────────────────────────────────┘
```

**Styling:** same SCSS tokens as the rest of the app (`--color-text`, `--color-border`, etc.), no Tailwind.

---

## Implementation Steps

1. **Migration** — add `coaching_analysis` + `coaching_status` to `resumes` table.
2. **Model + enum** — update `models.py` (`Resume` fields, `AgentName.RESUME_COACHING`).
3. **Coaching agent** — write `resume_coaching_agent.py` with system prompt, STAR/XYZ grading logic, question generation.
4. **Service function** — write `run_coaching(resume_id)` (mirrors `run_pipeline` pattern).
5. **Route integration** — trigger `run_coaching` via BackgroundTasks on `POST /resumes/`.
6. **Resume store** — extend type, add polling logic.
7. **ResumesView** — add status chip + coaching trigger.
8. **ResumeCoachingPanel** — build component with collapsible STAR/XYZ explainer + per-section cards.
9. **Tests** — unit test for coaching agent output schema; route test for upload triggering coaching status transition.

---

## Out of Scope (for this ticket)

- Re-running coaching after the user edits and re-uploads (a new resume version already triggers a new coaching run by design).
- Saving user responses to coaching questions — this is a reading/reflection feature, not a form.
- JD-aware coaching (that's the existing `feedback_agent`).
