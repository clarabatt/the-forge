import { ref } from "vue";
import { useResumesStore } from "@/stores/resumes";

export function useFileUpload(onSuccess?: (body: { id?: string }) => void | Promise<void>) {
  const resumesStore = useResumesStore();
  const fileInput = ref<HTMLInputElement | null>(null);
  const isUploading = ref(false);
  const uploadError = ref<string | null>(null);

  function triggerUpload() {
    uploadError.value = null;
    fileInput.value?.click();
  }

  async function onFileSelected(event: Event) {
    const file = (event.target as HTMLInputElement).files?.[0];
    if (!file) return;
    isUploading.value = true;
    uploadError.value = null;
    const form = new FormData();
    form.append("file", file);
    try {
      const res = await fetch("/api/resumes/", {
        method: "POST",
        credentials: "include",
        body: form,
      });
      const body = await res.json().catch(() => ({}));
      if (!res.ok) {
        uploadError.value = body.detail ?? "Upload failed";
        return;
      }
      await resumesStore.fetchAll();
      await onSuccess?.(body);
    } catch {
      uploadError.value = "Network error — try again";
    } finally {
      isUploading.value = false;
      if (fileInput.value) fileInput.value.value = "";
    }
  }

  return { fileInput, isUploading, uploadError, triggerUpload, onFileSelected };
}
