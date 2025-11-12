import { whisperTranscribeRequest } from "../api/whisper";

export async function useWhisper(audioBlob: Blob) {
  const mime = audioBlob.type || "audio/webm";
  const ext = mime.includes("m4a") ? "m4a" : mime.includes("ogg") ? "ogg" : "webm";
  const file = new File([audioBlob], `recording-${Date.now()}.${ext}`, { type: mime });

  // Whisper API 호출
  const res = await whisperTranscribeRequest(file);
  return res.text || res.transcript || "(음성 인식 결과 없음)";
}
