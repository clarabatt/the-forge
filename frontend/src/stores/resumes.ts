import { defineStore } from "pinia";
import { computed, ref } from "vue";

export interface InsightsBullet {
  text: string;
  framework_score: "weak" | "partial" | "strong";
  issues: string[];
  coaching_questions: string[];
}

export interface InsightsExperienceBlock {
  employer: string;
  date_range: string | null;
  bullets: InsightsBullet[];
}

export interface InsightsAnalysis {
  overall_score: "needs_work" | "decent" | "strong";
  global_issues: string[];
  summary_feedback: {
    detected_text: string | null;
    issues: string[];
    coaching_questions: string[];
  };
  skills_feedback: {
    detected_skills: string[];
    issues: string[];
    coaching_questions: string[];
  };
  experience_blocks: InsightsExperienceBlock[];
}

export interface Resume {
  id: string;
  file_name: string;
  bucket_key: string;
  resume_type: "BASE" | "TAILORED";
  is_latest: boolean;
  version_number: number;
  raw_text: string | null;
  user_id: string;
  application_id: string | null;
  coaching_status: "pending" | "analyzing" | "done" | "failed";
  coaching_analysis: string | null;
  created_at: string;
}

export const useResumesStore = defineStore("resumes", () => {
  const resumes = ref<Resume[]>([]);
  const selectedResumeId = ref<string | null>(null);

  const baseResumes = computed(() => resumes.value.filter((r) => r.resume_type === "BASE"));

  async function fetchAll() {
    const res = await fetch("/api/resumes/", { credentials: "include" });
    if (!res.ok) return;
    resumes.value = await res.json();
    if (!selectedResumeId.value) {
      selectedResumeId.value = baseResumes.value[0]?.id ?? null;
    }
  }

  async function fetchOne(id: string): Promise<Resume | null> {
    const res = await fetch(`/api/resumes/${id}`, { credentials: "include" });
    if (!res.ok) return null;
    const resume: Resume = await res.json();
    const idx = resumes.value.findIndex((r) => r.id === id);
    if (idx !== -1) resumes.value[idx] = resume;
    else resumes.value.push(resume);
    return resume;
  }

  async function fetchHtml(id: string): Promise<string | null> {
    const res = await fetch(`/api/resumes/${id}/html`, { credentials: "include" });
    if (!res.ok) return null;
    const body = await res.json();
    return body.html ?? null;
  }

  async function deleteResume(id: string) {
    const res = await fetch(`/api/resumes/${id}`, { method: "DELETE", credentials: "include" });
    if (!res.ok) throw new Error("Delete failed");
    resumes.value = resumes.value.filter((r) => r.id !== id);
    if (selectedResumeId.value === id) {
      selectedResumeId.value = baseResumes.value[0]?.id ?? null;
    }
  }

  async function downloadResume(id: string, fileName: string) {
    const res = await fetch(`/api/resumes/${id}/download`, { credentials: "include" });
    if (!res.ok) throw new Error("Download failed");
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async function renameResume(id: string, fileName: string) {
    const res = await fetch(`/api/resumes/${id}`, {
      method: "PATCH",
      credentials: "include",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ file_name: fileName }),
    });
    if (!res.ok) throw new Error("Rename failed");
    const updated: Resume = await res.json();
    const idx = resumes.value.findIndex((r) => r.id === id);
    if (idx !== -1) resumes.value[idx] = updated;
  }

  function getInsightsAnalysis(resume: Resume): InsightsAnalysis | null {
    if (!resume.coaching_analysis) return null;
    try {
      return JSON.parse(resume.coaching_analysis) as InsightsAnalysis;
    } catch {
      return null;
    }
  }

  return {
    resumes,
    baseResumes,
    selectedResumeId,
    fetchAll,
    fetchOne,
    fetchHtml,
    deleteResume,
    renameResume,
    downloadResume,
    getInsightsAnalysis,
  };
});
