# The forge — Architecture & Technical Specification

## Project objective

Speed up the process of tailoring a base resume for each job application. The user uploads a `.docx` once, provides job descriptions, and the system uses AI agents to identify skill gaps, suggest modifications within strict guardrails, and export a clean, consistently formatted document.

---

## Feature scope

### Core features

1. **Upload base resume** (`.docx`). System parses and stores it. Images, icons, and column grids are stripped with a warning — the output is always rendered against the standard template.
2. **Standard template download.** A fixed, versioned `.docx` template stored in GCS. Users can download the blank template to understand what the output will look like.
3. **New application from job description.** Pasting a JD creates an application record. The application title is automatically set to `Company Name: Job Title`. Each application has a status: `applied`, `denied`, `cancelled`, `approved`.
4. **AI-driven skill gap analysis.** Three sequential agents (JD Agent → Resume Agent → Diff Agent) produce a ranked skill list and a modification proposal. The Judge validator enforces all forbidden-edit rules programmatically.
5. **User approval gate.** Before the Diff Agent runs, the user reviews the ranked skill list and explicitly approves or excludes each item. Skills not found in the base resume require explicit opt-in.
6. **Diff viewer.** The browser renders an HTML diff between the base and tailored resume. A separate clean `.docx` is available for download — no attempt is made to embed tracked-changes markup inside the DOCX itself.
7. **File versioning.** Full version history is stored in the DB and GCS, but only the latest per application is exposed in the UI.
8. **Download.** Signed GCS URLs for both base and tailored versions.
9. **Google login.** OAuth 2.0 / OIDC via Google.
10. **AI cost tracking per user.** Token counts logged per API call. Monthly cost computed via a Postgres view. A FastAPI middleware enforces a `$5.00/month` cap with a `402` response.

### Optional / future

- Per-application chat for iterative improvement of the tailoring.

---

## Technology choices and rationale

### Frontend

| Technology            | Rationale                                                                              |
| --------------------- | -------------------------------------------------------------------------------------- |
| Vue 3 + TypeScript    | Composition API suits the complex reactive state of the diff viewer and approval flow. |
| shadcn-vue            | Accessible, unstyled-by-default components. Easy to theme via CSS custom properties.   |
| Pinia                 | Simpler than Vuex; first-class TypeScript support.                                     |
| SCSS with `{}` syntax | Keep CSS custom properties for theming; avoid Tailwind's build complexity.             |
| `EventSource` (SSE)   | Strictly server-to-client state updates. No WebSocket overhead needed.                 |

### Backend

| Technology                | Rationale                                                                                                      |
| ------------------------- | -------------------------------------------------------------------------------------------------------------- |
| Python 3.12 + FastAPI     | Async-first, clean OpenAPI generation, Pydantic v2 for structured outputs.                                     |
| SQLModel                  | Single source of truth for DB schema and Pydantic models — avoids duplication.                                 |
| Alembic                   | Explicit migration history. Never auto-migrate in production.                                                  |
| Mammoth                   | `.docx` → clean HTML for diff rendering.                                                                       |
| `python-docx`             | Structured read and template write. Both libraries are used: Mammoth for extraction, `python-docx` for output. |
| `difflib.SequenceMatcher` | Server-side diff computation at the sentence/bullet level. Never computed client-side.                         |

### Agents

**Do not use MCP for agent orchestration.** MCP (Model Context Protocol) is a tool-calling protocol — it gives an LLM access to external resources. It is not an orchestration framework. The three agents here are sequential API calls in Python, each receiving the prior output as input context. Using the Google AI SDK directly with `response_format: {"type": "json_object"}` is simpler, more debuggable, and does not require MCP infrastructure.

| Technology                    | Rationale                                                                                                                      |
| ----------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| Google AI SDK (Python)        | Direct access to gemini-1.5-pro with structured JSON output mode.                                                              |
| Structured output (JSON mode) | All agent outputs are typed JSON. Parse failures trigger a retry, never a crash.                                               |
| Cloud Run Jobs                | Long-running containers for agent execution. Avoids Cloud Run's 60s request timeout — LLM chains regularly hit 60–90s.         |
| Cloud Tasks                   | Queue layer. HTTP callbacks with built-in retry and deduplication. FastAPI enqueues a task; the task triggers a Cloud Run Job. |

### Infrastructure

| Service                 | Use                                                                                                |
| ----------------------- | -------------------------------------------------------------------------------------------------- |
| Cloud Run               | FastAPI API server. Stateless, autoscales to zero.                                                 |
| Cloud Run Jobs          | Agent pipeline execution.                                                                          |
| Cloud Tasks             | Job queue between API and agent jobs.                                                              |
| Cloud SQL (Postgres 15) | Primary datastore.                                                                                 |
| Cloud Storage           | File storage. Private bucket; signed URLs only; never public URLs.                                 |
| Secret Manager          | API keys, DB credentials, OAuth secrets. Never in environment variables directly.                  |
| Cloud Build             | CI/CD. Single `cloudbuild.yaml` builds the multi-stage Docker image, runs migrations, and deploys. |

---

## Repository layout

```
/
├── frontend/                  # Vue 3 + shadcn-vue
│   ├── src/
│   │   ├── views/
│   │   ├── components/
│   │   ├── stores/            # Pinia
│   │   └── composables/
├── backend/
│   ├── agents/                # JD, Resume, Diff agent definitions
│   ├── domain/                # State machine, Judge validator, forbidden-edit rules
│   ├── database/              # SQLModel models, Alembic migrations
│   └── services/              # Mammoth parser, python-docx writer, diff renderer, GCS client
├── Dockerfile                 # Multi-stage: builds Vue, serves via FastAPI static
├── cloudbuild.yaml            # Single deploy trigger
└── docker-compose.yml         # Local dev
```

---

## Application state machine

Because LLM calls are slow (60–90s possible), the backend is a state-driven orchestrator. State is persisted in `applications.status` and pushed to the frontend via SSE.

| State              | Trigger                    | Action                                                                      |
| ------------------ | -------------------------- | --------------------------------------------------------------------------- |
| `UPLOADED`         | User uploads `.docx`       | Parse text via `python-docx`. Store raw text.                               |
| `ANALYZING`        | System starts              | Trigger JD Agent and Resume Agent in parallel via Cloud Tasks.              |
| `PENDING_APPROVAL` | Both agents finish         | Push skill list to UI. Wait for user form submission.                       |
| `TAILORING`        | User submits approval form | Enqueue Diff Agent via Cloud Tasks.                                         |
| `VALIDATING`       | Diff Agent returns output  | Judge runs programmatic validation against protected fields.                |
| `PENDING_RETRY`    | Judge rejects output       | Re-queue Diff Agent with stricter prompt + violation detail. Max 2 retries. |
| `READY`            | Validation passes          | Render diff JSON. Generate signed download URLs.                            |
| `FAILED`           | Any unrecoverable error    | Log error, persist message, notify user via SSE.                            |

`PENDING_RETRY` is a distinct state — not a loop back to `TAILORING`. It produces an audit trail of how many retries each application required and prevents UI confusion about why the user is waiting again.

---

## Database schema

### `users`

| Column        | Type                     | Notes                                                    |
| ------------- | ------------------------ | -------------------------------------------------------- |
| `id`          | UUID PK                  |                                                          |
| `email`       | String (unique, indexed) | Display only. Do not use as join key.                    |
| `google_sub`  | String (unique, indexed) | Primary identity key from Google OIDC. Safer than email. |
| `full_name`   | String                   | From Google profile.                                     |
| `picture_url` | String                   | For the UI header avatar.                                |
| `created_at`  | DateTime                 | Default `now()`.                                         |
| `last_login`  | DateTime                 | Updated on each OIDC callback.                           |
| `is_active`   | Boolean                  | Default `true`. Soft-disable without deletion.           |

### `applications`

| Column               | Type                   | Notes                                                                                          |
| -------------------- | ---------------------- | ---------------------------------------------------------------------------------------------- |
| `id`                 | UUID PK                |                                                                                                |
| `user_id`            | UUID FK → `users.id`   |                                                                                                |
| `status`             | Enum                   | See state machine above.                                                                       |
| `company_name`       | String                 |                                                                                                |
| `job_title`          | String                 |                                                                                                |
| `application_status` | Enum                   | `applied`, `denied`, `cancelled`, `approved`. Separate from pipeline status.                   |
| `base_resume_id`     | UUID FK → `resumes.id` | The resume version used as input.                                                              |
| `template_version`   | String                 | e.g. `v1`. Stored at creation time; template updates do not retroactively break old downloads. |
| `retry_count`        | Integer                | Default 0. Incremented on each `PENDING_RETRY` transition.                                     |
| `error_message`      | Text                   | Nullable. Populated on `FAILED`.                                                               |
| `created_at`         | DateTime               |                                                                                                |

### `resumes`

| Column             | Type                              | Notes                                                                                                                 |
| ------------------ | --------------------------------- | --------------------------------------------------------------------------------------------------------------------- |
| `id`               | UUID PK                           |                                                                                                                       |
| `user_id`          | UUID FK → `users.id`              | Ownership.                                                                                                            |
| `application_id`   | UUID FK → `applications.id`       | Nullable. Null for base resumes not yet attached to an application.                                                   |
| `file_name`        | String                            | Original filename, for UI display only.                                                                               |
| `bucket_key`       | String                            | GCS path, e.g. `uploads/{user_id}/{resume_id}.docx`. Store the key, not the full URL. Generate signed URLs on demand. |
| `raw_text`         | Text                              | Mammoth/python-docx extracted output.                                                                                 |
| `resume_type`      | Enum                              | `BASE`, `TAILORED`.                                                                                                   |
| `parent_resume_id` | UUID FK → `resumes.id` (nullable) | Null for the original upload.                                                                                         |
| `version_number`   | Integer                           | Incremented per `parent_resume_id`.                                                                                   |
| `is_latest`        | Boolean (indexed)                 | Flipped by application logic on each new tailored version.                                                            |
| `template_version` | String                            | The template version this resume was rendered against.                                                                |
| `created_at`       | DateTime                          |                                                                                                                       |

### `skills`

| Column           | Type                        | Notes                                                                   |
| ---------------- | --------------------------- | ----------------------------------------------------------------------- |
| `id`             | UUID PK                     |                                                                         |
| `application_id` | UUID FK → `applications.id` |                                                                         |
| `skill_name`     | String                      |                                                                         |
| `category`       | String                      | e.g. `Hard Skill`, `Soft Skill`.                                        |
| `match_status`   | Enum                        | `found_in_resume`, `missing`.                                           |
| `user_action`    | Enum                        | `include`, `exclude`, `rephrase`. Set by the user in the approval gate. |
| `ai_confidence`  | Float                       | 0.0–1.0. From the JD Agent.                                             |
| `rank`           | Integer                     | JD Agent ranking, 1 = highest priority.                                 |

### `llm_usage_logs`

This table is **append-only**. Never update rows. Compute totals via a Postgres view.

| Column           | Type                                   | Notes                                               |
| ---------------- | -------------------------------------- | --------------------------------------------------- |
| `id`             | UUID PK                                |                                                     |
| `user_id`        | UUID FK → `users.id`                   |                                                     |
| `application_id` | UUID FK → `applications.id` (nullable) |                                                     |
| `agent_name`     | Enum                                   | `JD`, `RESUME`, `DIFF`, `JUDGE_RETRY`.              |
| `model`          | String                                 | e.g. `gemini-1.5-pro`. Store the full model string. |
| `input_tokens`   | Integer                                |                                                     |
| `output_tokens`  | Integer                                |                                                     |
| `created_at`     | DateTime                               |                                                     |

**Monthly cost view** (Postgres):

```sql
CREATE VIEW user_monthly_cost AS
SELECT
  user_id,
  DATE_TRUNC('month', created_at) AS month,
  SUM((input_tokens * 0.000003) + (output_tokens * 0.000015)) AS cost_usd
FROM llm_usage_logs
GROUP BY user_id, DATE_TRUNC('month', created_at);
```

Update the per-token pricing constants here when the model pricing changes. The cost middleware queries this view, never the raw table.

### `chat_messages` (schema reserved, UI deferred)

Even if the chat UI is not built in v1, create this table now. Adding a FK column to a busy table later requires a migration during downtime.

| Column           | Type                        | Notes                |
| ---------------- | --------------------------- | -------------------- |
| `id`             | UUID PK                     |                      |
| `application_id` | UUID FK → `applications.id` |                      |
| `role`           | Enum                        | `user`, `assistant`. |
| `content`        | Text                        |                      |
| `created_at`     | DateTime                    |                      |

---

## Agent orchestration

### Why not MCP

MCP is a tool-calling protocol. It is appropriate when an LLM needs to invoke external resources (search, file read, DB query) at inference time. It is not appropriate for chaining three sequential inference calls with shared context. Use the Google AI Python SDK directly.

### Agent chain

All agents use `gemini-1.5-pro` with `response_format: {"type": "json_object"}`. If JSON parsing fails, the job retries once with the same input before transitioning to `FAILED`.

**1. JD Agent**

Input: raw job description text, job title, company name.

Output JSON:

```json
{
  "skills": [
    {
      "name": "TypeScript",
      "category": "Hard Skill",
      "confidence": 0.97,
      "rank": 1,
      "found_in_resume": false
    }
  ],
  "vibe_check": "High-growth B2B SaaS. Values engineering rigour and measurable impact. Avoids corporate fluff in job listing — expect same in resume.",
  "must_have_count": 5
}
```

Skills ranked 1–10 by the JD Agent. The top 5 are flagged `must-have`. The Judge ensures every `must-have` skill appears at least once in the final output.

**2. Resume Agent**

Input: raw resume text.

Output JSON:

```json
{
  "blocks": [
    {
      "id": "blk_uuid",
      "type": "accomplishment",
      "text": "Reduced API latency by 40% by migrating to async processing.",
      "employer": "Acme Corp",
      "date_range": "2021–2023",
      "skills_detected": ["Python", "async"]
    }
  ]
}
```

Each block has a UUID. The Diff Agent references blocks by ID — it never reconstructs or re-parses the resume.

**3. Diff Agent**

Input: JD Agent output, approved skill list (user decisions applied), accomplishment blocks from the Resume Agent.

System prompt includes the forbidden-edit rules explicitly:

> You MUST NOT change any date, year, month, employer name, job title, or company name. These fields are immutable. You MAY rephrase accomplishment bullet points to incorporate approved skills. You MAY change capitalisation of technology names (e.g. `javascript` → `JavaScript`). Output only a JSON array of modification objects.

Output JSON:

```json
[
  {
    "block_id": "blk_uuid",
    "type": "modified",
    "original": "Built web applications using jQuery.",
    "modified": "Engineered scalable TypeScript microservices serving 2M monthly users."
  },
  {
    "block_id": null,
    "type": "suggestion",
    "text": "Consider quantifying the latency reduction in the second bullet — 'reduced latency by X%' lands better with technical recruiters."
  }
]
```

**4. The Judge (post-processor — Python, not LLM)**

The LLM alone cannot be trusted to honour forbidden-edit rules. The Judge validates programmatically using `difflib.SequenceMatcher`.

```python
import re
import difflib

DATE_PATTERN = re.compile(
    r'\b(19|20)\d{2}\b|'
    r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|'
    r'Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\b',
    re.IGNORECASE
)

def extract_protected_tokens(text: str, blocks: list[dict]) -> set[str]:
    tokens = set()
    for b in blocks:
        tokens.update(DATE_PATTERN.findall(b["text"]))
        tokens.add(b["employer"])
        tokens.add(b["date_range"])
    return tokens

def judge(original_blocks: list[dict], modifications: list[dict]) -> tuple[bool, list[str]]:
    protected = extract_protected_tokens("", original_blocks)
    violations = []
    for mod in modifications:
        if mod["type"] != "modified":
            continue
        original_tokens = set(DATE_PATTERN.findall(mod["original"]))
        modified_tokens = set(DATE_PATTERN.findall(mod["modified"]))
        changed_dates = original_tokens.symmetric_difference(modified_tokens)
        if changed_dates:
            violations.append(f"Date mutation detected: {changed_dates}")
        for token in protected:
            if token in mod["original"] and token not in mod["modified"]:
                violations.append(f"Protected field removed: '{token}'")
    return len(violations) == 0, violations
```

On rejection, the violations are injected into the Diff Agent's retry prompt as a `Critical Error` block. Maximum 2 retries before `FAILED`.

---

## Recruiter feedback tone

The overall feedback (not the diff — the written assessment) uses a deliberately non-flattering persona.

**System prompt snippet:**

> You are a cynical Technical Recruiter at a FAANG company. You have reviewed over 10,000 resumes. Do not use corporate fluff. If a bullet point is weak or lacks metrics, call it out directly. Be fair, but do not stroke the candidate's ego. Your job is to improve the resume, not to make the candidate feel good about it.

Feedback is structured as:

- **Overall assessment**: 2–3 sentences. Direct verdict on fit for the role.
- **Strong points**: Only genuine strengths. If there are none, say so.
- **Weak points**: Bullet points that lack metrics, are too vague, or are irrelevant to the JD. Call out each one specifically.
- **Recommended changes**: Concrete suggestions with examples.

---

## Diff viewer

### Server-side diff rendering

The diff JSON is computed in Python using `difflib` at the sentence and bullet-point level. The Vue component does not compute diffs — it only renders the JSON returned by the API.

```python
from difflib import SequenceMatcher

def compute_diff(original_text: str, modified_text: str) -> list[dict]:
    original_lines = original_text.split('\n')
    modified_lines = modified_text.split('\n')
    result = []
    matcher = SequenceMatcher(None, original_lines, modified_lines)
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            for line in original_lines[i1:i2]:
                result.append({"type": "original", "text": line})
        elif tag == 'replace':
            for line in original_lines[i1:i2]:
                result.append({"type": "removed", "text": line})
            for line in modified_lines[j1:j2]:
                result.append({"type": "added", "text": line})
        elif tag == 'delete':
            for line in original_lines[i1:i2]:
                result.append({"type": "removed", "text": line})
        elif tag == 'insert':
            for line in modified_lines[j1:j2]:
                result.append({"type": "added", "text": line})
    return result
```

Suggestion-type blocks from the Diff Agent are appended to the relevant section of the diff JSON.

### Vue rendering

```vue
<template>
  <div class="diff-viewer">
    <div v-for="(block, i) in diff" :key="i" :class="blockClass(block.type)">
      {{ block.text }}
    </div>
  </div>
</template>
```

CSS classes:

- `removed`: `text-orange-600 line-through bg-orange-50`
- `added`: `text-blue-600 bg-blue-50`
- `suggestion`: `bg-yellow-100 border-l-4 border-yellow-400 p-2`
- `original`: unstyled

### DOCX download

The clean DOCX download is generated server-side by `python-docx`, writing the AI-modified content into the versioned standard template. No tracked-changes markup is embedded in the DOCX. The diff is a browser-only view.

---

## SSE contract

This contract must be defined before frontend and backend work begins in parallel, to avoid integration drift.

```
GET /api/applications/{id}/stream
Authorization: Bearer <session_token>
Content-Type: text/event-stream
```

Events:

```
event: status_changed
data: {"status": "ANALYZING", "updated_at": "2025-01-01T12:00:00Z"}

event: status_changed
data: {"status": "PENDING_APPROVAL", "updated_at": "...", "skills": [...]}

event: status_changed
data: {"status": "TAILORING", "updated_at": "..."}

event: status_changed
data: {"status": "PENDING_RETRY", "updated_at": "...", "retry_count": 1}

event: status_changed
data: {"status": "READY", "updated_at": "...", "diff_url": "/api/applications/{id}/diff", "download_url": "..."}

event: status_changed
data: {"status": "FAILED", "updated_at": "...", "error": "Judge rejected after 2 retries: date mutation detected"}
```

The Vue `EventSource` listener updates Pinia store on each event. The application view is entirely driven by `application.status` — no polling.

---

## Security notes

### Google OAuth CSRF protection

Store the `state` parameter from the OIDC initiation in a short-lived Postgres record (TTL 10 minutes) or Redis key. Validate it on callback. Do not skip this in v1.

```python
# On /auth/google/login
state = secrets.token_urlsafe(32)
await db.execute(
    "INSERT INTO oauth_state (state, expires_at) VALUES ($1, NOW() + INTERVAL '10 minutes')",
    state
)
# Redirect to Google with state param

# On /auth/google/callback
row = await db.fetchrow("SELECT * FROM oauth_state WHERE state = $1 AND expires_at > NOW()", state)
if not row:
    raise HTTPException(status_code=400, detail="Invalid or expired OAuth state")
await db.execute("DELETE FROM oauth_state WHERE state = $1", state)
```

### GCS signed URLs

Never store or return the full GCS public URL. Store the bucket key. Generate signed URLs on demand with a short TTL (15 minutes for downloads, 5 minutes for uploads).

### Cost rate limiting

Two levels, both required:

1. **Monthly cost cap**: Middleware checks `user_monthly_cost` view on each agent-triggering request. If `cost_usd > 5.00`, return `402 Payment Required`.
2. **Burst rate limit**: Max 3 agent pipeline runs per user per 10 minutes. Prevents cost-cap bypass via rapid submissions. Implemented as a sliding window counter in Postgres or Redis.

### File storage hygiene

Apply a GCS lifecycle policy to the `uploads/` prefix: delete objects older than 7 days. The `outputs/` prefix is retained (user's tailored resumes). This limits storage of raw uploaded files and reduces GDPR exposure.

---

## Standard template versioning

The standard template is stored at `gs://{bucket}/templates/v1/base.docx`. When the template is updated:

1. Upload the new version as `templates/v2/base.docx`.
2. Update the `CURRENT_TEMPLATE_VERSION` config value.
3. New applications use `v2`. Existing applications retain `v1` in `applications.template_version` and continue to download against the `v1` template.

This means old tailored resumes remain downloadable and look correct indefinitely.

---

## Forbidden and allowed edit rules

| Rule                                             | Enforcement                                              |
| ------------------------------------------------ | -------------------------------------------------------- |
| Dates must not change                            | Judge: regex extraction + symmetric diff                 |
| Employer names must not change                   | Judge: token comparison against Resume Agent blocks      |
| Job titles / role names must not change          | Judge: token comparison against Resume Agent blocks      |
| Company names must not change                    | Judge: token comparison                                  |
| Capitalisation of technology names is allowed    | Explicitly permitted in Diff Agent system prompt         |
| Skills not in base resume require user opt-in    | Enforced at the approval gate — user must mark `include` |
| All `must-have` skills must appear at least once | Judge: string search in final output                     |

---

## Local development

```bash
# Start all services
docker compose up

# Services:
# - frontend:  http://localhost:5173
# - backend:   http://localhost:8000
# - postgres:  localhost:5432
# - adminer:   http://localhost:8080 (DB GUI)

# Run migrations
cd backend && alembic upgrade head

# Run agent jobs locally (bypasses Cloud Tasks/Run)
python -m backend.agents.run --application-id <uuid>
```

The `docker-compose.yml` includes a local stub for Cloud Tasks that calls the agent job directly, so the full pipeline runs locally without GCP credentials.

---

## Deployment

Single `cloudbuild.yaml` trigger on push to `main`:

1. Build the multi-stage Docker image (Vue static build → FastAPI image).
2. Run `alembic upgrade head` as a migration step.
3. Deploy to Cloud Run.

The Vue build output is served as static files by FastAPI using `StaticFiles`. No separate frontend hosting required.
