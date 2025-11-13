import { httpPostForm } from "./http";

export async function whisperTranscribeRequest(file: File) {
  const form = new FormData();
  form.append("file", file);
  return await httpPostForm("/whisper/transcribe", form);
}
